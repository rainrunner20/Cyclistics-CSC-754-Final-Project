package org.cyclistics.devs;

import java.util.Arrays;

/** Structural checks only; event-clock behavior needs the real coordinator. */
public final class CoupledStructureSmokeTests {
    private static int assertions = 0;
    private static void check(boolean condition, String label) {
        assertions++;
        if (!condition) throw new AssertionError(label);
    }
    public static void main(String[] args) {
        CyclisticsCoupledModel model = new CyclisticsCoupledModel(
                "Cyclistics", Arrays.asList(10.0, 15.0), new double[][]{{12, 20}}, 4.0);
        check("Cyclistics".equals(model.getName()), "coupled model name");
        check(model.childCount() == 3, "three child atomic models");
        check(model.couplingCount() == 4, "3 internal + 1 external coupling");
        check(model.hasOutputPort("departed"), "exposed departure port");
        check(model.hasCoupling("arrival->arrival"), "arrival path");
        check(model.hasCoupling("block->block"), "block path");
        check(model.hasCoupling("clear->clear"), "clearance path");
        check(model.hasCoupling("departed->departed"), "departure path");
        check(model.generator() != null, "generator getter");
        check(model.obstructions() != null, "obstruction getter");
        check(model.lane() != null, "lane getter");
        System.out.println("PASS: " + assertions + " coupled-structure assertions (test-only wiring adapter)");
        System.out.println("PENDING: verify event routing through real DEVS-Suite coordinator");
    }
}
