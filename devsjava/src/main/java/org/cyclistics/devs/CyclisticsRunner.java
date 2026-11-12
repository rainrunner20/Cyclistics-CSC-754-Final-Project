package org.cyclistics.devs;

import java.util.Arrays;
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
                || model.lane().isServing()) {
            throw new AssertionError("Coupled DEVS results differ from the deterministic scenario");
        }
        System.out.println("PASS: coupled models executed and two cyclists departed.");
        System.out.println("NOTE: timestamp trace, library/course-version check, and Python comparison remain pending.");
    }
}
