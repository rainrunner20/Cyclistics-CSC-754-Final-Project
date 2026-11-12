package org.cyclistics.devs;

import java.util.ArrayList;
import java.util.List;

import genDevs.modeling.message;
import simView.ViewableAtomic;

/**
 * Announces when a bicycle lane becomes blocked and when it clears.
 *
 * Each {start, end} window is measured in seconds from simulation time zero.
 * The schedule is fixed for now: later experiments will swap in other windows.
 *
 * This class uses common DEVSJAVA method signatures, but for this milestone
 * we only test it against the clearly labeled, TEST-ONLY adapter in the repo.
 */
public final class ObstructionController extends ViewableAtomic {
    private final List<Double> eventTimes = new ArrayList<>();
    private final List<String> eventPorts = new ArrayList<>();

    private int nextEventIndex;
    private boolean blocked;

    public ObstructionController(String name, double[][] windows) {
        super(name);
        addOutport("block");
        addOutport("clear");

        if (windows == null) {
            throw new IllegalArgumentException("windows cannot be null");
        }
        double previousEnd = -1.0;
        for (double[] window : windows) {
            if (window == null || window.length != 2) {
                throw new IllegalArgumentException("each obstruction needs [start, end]");
            }
            double start = window[0];
            double end = window[1];
            // Refuse overlapping or backwards times so we never emit a
            // second 'block' while the previous obstruction is still active.
            if (!Double.isFinite(start) || !Double.isFinite(end)
                    || start < 0 || end <= start || start < previousEnd) {
                throw new IllegalArgumentException("windows must be ordered, nonoverlapping, and positive-length");
            }
            eventTimes.add(start);
            eventPorts.add("block");
            eventTimes.add(end);
            eventPorts.add("clear");
            previousEnd = end;
        }
    }

    @Override
    public void initialize() {
        super.initialize();
        nextEventIndex = 0;
        blocked = false;
        if (eventTimes.isEmpty()) {
            passivate();
        } else {
            // The first time advance starts from simulation time zero.
            holdIn("scheduled", eventTimes.get(0));
        }
    }

    @Override
    public message out() {
        // DEVS calls the output function BEFORE the internal transition.
        // Only report the state change; deltint() will apply it next.
        if (nextEventIndex >= eventTimes.size()) {
            return new message();
        }
        String port = eventPorts.get(nextEventIndex);
        return outputNameOnPort(port.equals("block") ? "blocked" : "cleared", port);
    }

    @Override
    public void deltint() {
        if (nextEventIndex >= eventTimes.size()) {
            passivate();
            return;
        }
        blocked = eventPorts.get(nextEventIndex).equals("block");
        int previousIndex = nextEventIndex;
        nextEventIndex++;
        if (nextEventIndex == eventTimes.size()) {
            passivate();
        } else {
            // DEVS expects the time UNTIL the next event, not its absolute time.
            double gap = eventTimes.get(nextEventIndex) - eventTimes.get(previousIndex);
            holdIn("scheduled", gap);
        }
    }

    @Override
    public void deltext(double elapsed, message inputs) {
        // This model has no input ports. If a coordinator delivers an empty
        // external bag, we preserve the remaining delay to the next event.
        Continue(elapsed);
        if (inputs != null && inputs.getLength() > 0) {
            throw new IllegalArgumentException("ObstructionController has no input ports");
        }
    }

    @Override
    public void deltcon(double elapsed, message inputs) {
        // Internal event wins at a timestamp tie; there is no external
        // control input in this version, so we preserve the new schedule.
        deltint();
        deltext(0.0, inputs);
    }

    public boolean isBlocked() {
        return blocked;
    }

    public int firedEvents() {
        return nextEventIndex;
    }
}
