package org.cyclistics.devs;

import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import model.simulation.coordinator;

/**
 * Minimal real-framework integration check using a predictable scenario.
 *
 * A first cyclist arrives at 10s and spends 4s passing the bottleneck.
 * A blockage from 12s to 20s does not stop an in-progress passage.
 * The second cyclist arrives at 15s, waits, and passes after clearance.
 *
 * Real-JAR execution is required before treating this as verified.
 */
public final class CyclisticsRunner {
    private CyclisticsRunner() { }

    public static void main(String[] args) {
        System.setProperty("java.awt.headless", "true");
        CyclisticsCoupledModel model = new CyclisticsCoupledModel(
                "Cyclistics", Arrays.asList(10.0, 15.0),
                new double[][]{{12.0, 20.0}}, 4.0);

        // This is DEVS-Suite's actual coordinator, NOT our unit-test adapter.
        coordinator simulator = new coordinator(model);
        simulator.initialize();
        simulator.simulate(30); // maximum coordinator iterations, not seconds

        // Print a machine-readable trace from completed INTERNAL transitions.
        // This is the result of the real DEVS coordinator driving the model.
        List<LaneBottleneck.Departure> departures = model.lane().departureTrace();
        for (LaneBottleneck.Departure event : departures) {
            System.out.printf(Locale.ROOT, "DEPARTURE,%.3f,%s%n",
                    event.timeSeconds(), event.cyclistId());
        }

        System.out.println("Cyclistics coupled-DEVS summary:");
        System.out.println("  generated=" + model.generator().emittedCount());
        System.out.println("  obstruction events=" + model.obstructions().firedEvents());
        System.out.println("  departed=" + model.lane().departedCount());
        System.out.println("  max waiting=" + model.lane().maxWaitingQueue());
        System.out.println("  remaining=" + model.lane().waitingCount());

        if (model.generator().emittedCount() != 2
                || model.obstructions().firedEvents() != 2
                || model.lane().departedCount() != 2
                || model.lane().maxWaitingQueue() != 1
                || model.lane().waitingCount() != 0
                || model.lane().isBlocked()
                || model.lane().isServing()
                || departures.size() != 2) {
            throw new AssertionError("Coupled DEVS results differ from the deterministic scenario");
        }
        requireDeparture(departures.get(0), "cyclist-1", 14.0);
        requireDeparture(departures.get(1), "cyclist-2", 24.0);
        System.out.println("PASS: real coordinator departure timestamps match 14s and 24s.");
        System.out.println("NOTE: Python independently checks the same deterministic fixture;"
                + " field validation and course-library equivalence are still pending.");
    }

    private static void requireDeparture(LaneBottleneck.Departure actual,
                                         String expectedId, double expectedSeconds) {
        if (!expectedId.equals(actual.cyclistId())
                || Math.abs(actual.timeSeconds() - expectedSeconds) > 1e-9) {
            throw new AssertionError("Unexpected departure " + actual.cyclistId()
                    + " at " + actual.timeSeconds() + "s; expected "
                    + expectedId + " at " + expectedSeconds + "s");
        }
    }
}
