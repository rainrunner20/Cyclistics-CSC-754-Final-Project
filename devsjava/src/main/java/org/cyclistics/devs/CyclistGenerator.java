package org.cyclistics.devs;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import genDevs.modeling.message;
import simView.ViewableAtomic;

/**
 * Emits cyclist-arrival events at specified simulation times.
 *
 * We start with a repeatable schedule instead of random arrivals inside this
 * model. Later we can feed it a seeded schedule from the Python experiment,
 * which makes comparing the two implementations much easier.
 *
 * Time units: seconds. A schedule time is relative to simulation time zero.
 */
public final class CyclistGenerator extends ViewableAtomic {
    private final List<Double> arrivalTimes;
    private int nextArrivalIndex;

    public CyclistGenerator(String name, List<Double> arrivalTimes) {
        super(name);
        addInport("stop");
        addOutport("arrival");

        if (arrivalTimes == null) {
            throw new IllegalArgumentException("arrivalTimes must not be null");
        }
        List<Double> copy = new ArrayList<>(arrivalTimes);
        double previous = -1;
        for (double t : copy) {
            if (!Double.isFinite(t) || t < 0 || t < previous) {
                throw new IllegalArgumentException("arrival times must be sorted and nonnegative");
            }
            previous = t;
        }
        this.arrivalTimes = Collections.unmodifiableList(copy);
    }

    /** Build a deterministic schedule using an average cyclists/hour input. */
    public static CyclistGenerator evenlySpaced(String name, double ratePerHour, double horizonSeconds) {
        if (!Double.isFinite(ratePerHour) || ratePerHour < 0
                || !Double.isFinite(horizonSeconds) || horizonSeconds <= 0) {
            throw new IllegalArgumentException("rate must be >= 0 and horizon > 0");
        }
        List<Double> times = new ArrayList<>();
        if (ratePerHour > 0) {
            double spacing = 3600.0 / ratePerHour;
            // Cap the generated event list to catch accidental runaway inputs.
            for (int k = 1; k <= 1_000_000; k++) {
                double t = k * spacing;
                if (t > horizonSeconds + 1e-9) {
                    break;
                }
                times.add(t);
                if (k == 1_000_000) {
                    throw new IllegalArgumentException("too many arrivals for a single schedule");
                }
            }
        }
        return new CyclistGenerator(name, times);
    }

    @Override
    public void initialize() {
        super.initialize();
        nextArrivalIndex = 0;
        if (arrivalTimes.isEmpty()) {
            passivate();
        } else {
            holdIn("scheduled", arrivalTimes.get(0));
        }
    }

    @Override
    public message out() {
        if (nextArrivalIndex >= arrivalTimes.size()) {
            return new message();
        }
        // DEVS lambda runs BEFORE delta_internal: use +1 for the arriving ID.
        return outputNameOnPort("cyclist-" + (nextArrivalIndex + 1), "arrival");
    }

    @Override
    public void deltint() {
        int previous = nextArrivalIndex;
        nextArrivalIndex++;
        if (nextArrivalIndex >= arrivalTimes.size()) {
            passivate();
            return;
        }
        double interval = arrivalTimes.get(nextArrivalIndex) - arrivalTimes.get(previous);
        holdIn("scheduled", interval);
    }

    @Override
    public void deltext(double elapsed, message inputs) {
        Continue(elapsed); // preserve the remaining time if another input arrives
        if (somethingOnPort(inputs, "stop")) {
            passivate();
        }
    }

    @Override
    public void deltcon(double elapsed, message inputs) {
        // At an exact tie, DEVS emits this arrival first; a simultaneous stop
        // prevents FUTURE arrivals. The order is intentional and documented.
        deltint();
        deltext(0, inputs);
    }

    public int emittedCount() {
        return nextArrivalIndex;
    }
}
