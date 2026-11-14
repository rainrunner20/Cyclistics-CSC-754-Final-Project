package org.cyclistics.devs;

import java.util.Objects;

import GenCol.entity;
import model.modeling.content;
import model.modeling.message;

/** Standalone logic tests: not a replacement for a real DEVSJAVA coordinator. */
public final class ObstructionControllerSmokeTests {
    private static int assertions = 0;

    private static void check(boolean expected, String description) {
        assertions++;
        if (!expected) {
            throw new AssertionError(description);
        }
    }

    private static void equal(double expected, double actual, String description) {
        check(Math.abs(expected - actual) < 1e-9,
              description + ": expected=" + expected + " actual=" + actual);
    }

    private static void port(ObstructionController controller, String expected) {
        message output = controller.out();
        check(output.getLength() == 1, "exactly one scheduled output");
        check(Objects.equals(expected, output.read(0).getPortName()), "expected output port " + expected);
        String expectedValue = expected.equals("block") ? "blocked" : "cleared";
        check(Objects.equals(expectedValue, output.getValOnPort(expected, 0).getName()),
              "expected output value " + expectedValue);
    }

    private static void reject(Runnable action, String description) {
        boolean threw = false;
        try {
            action.run();
        } catch (IllegalArgumentException expected) {
            threw = true;
        }
        check(threw, description);
    }

    public static void main(String[] args) {
        ObstructionController controller = new ObstructionController("truck", new double[][]{
                {10, 20}, {30, 45}
        });
        controller.initialize();
        check(!controller.isBlocked(), "starts with a clear lane");
        equal(10, controller.ta(), "first truck arrives at 10s");
        port(controller, "block");

        // out() only announces the event; deltint() changes the state.
        check(!controller.isBlocked(), "output does not mutate model state");
        controller.deltint();
        check(controller.isBlocked(), "truck blocks the lane after transition");
        check(controller.firedEvents() == 1, "one event processed");
        equal(10, controller.ta(), "clear is 10 seconds after block");
        port(controller, "clear");
        controller.deltint();
        check(!controller.isBlocked(), "lane clears at 20s");
        equal(10, controller.ta(), "next truck begins at 30s");
        port(controller, "block");
        controller.deltint();
        check(controller.isBlocked(), "second truck blocks the lane");
        equal(15, controller.ta(), "second truck stays for 15 seconds");
        port(controller, "clear");
        controller.deltint();
        check(!controller.isBlocked(), "final clearance restores lane");
        check(controller.firedEvents() == 4, "all four events processed");
        check(Double.isInfinite(controller.ta()), "controller passivates after final event");
        check(controller.out().getLength() == 0, "no outputs after completion");

        // Check that unrelated empty external events don't reset the timer.
        ObstructionController elapsed = new ObstructionController("elapsed", new double[][]{{10, 20}});
        elapsed.initialize();
        elapsed.deltext(3, new message());
        equal(7, elapsed.ta(), "elapsed time is deducted from remaining delay");
        reject(() -> elapsed.deltext(0, input("arrival", "unexpected")),
               "unsupported external inputs are rejected");

        // Adjacent windows are allowed: clear and block at the same second.
        // They are two finite zero-gap DEVS events, not one permanent blockage.
        ObstructionController adjacent = new ObstructionController("adjacent", new double[][]{{0, 5}, {5, 7}});
        adjacent.initialize();
        equal(0, adjacent.ta(), "an obstruction can begin at t=0");
        port(adjacent, "block");
        adjacent.deltint();
        equal(5, adjacent.ta(), "first clearance at t=5");
        port(adjacent, "clear");
        adjacent.deltint();
        equal(0, adjacent.ta(), "next blockage starts at same timestamp");
        port(adjacent, "block");
        adjacent.deltint();
        check(adjacent.isBlocked(), "second block applies at same timestamp");
        equal(2, adjacent.ta(), "final clearance is two seconds later");
        adjacent.deltint();
        check(Double.isInfinite(adjacent.ta()), "adjacent windows eventually end");
        check(!adjacent.isBlocked(), "lane is clear at final transition");

        ObstructionController empty = new ObstructionController("empty", new double[][]{});
        empty.initialize();
        check(Double.isInfinite(empty.ta()), "empty obstruction schedule is passive");
        check(!empty.isBlocked(), "empty schedule stays unblocked");
        controller.initialize();
        equal(10, controller.ta(), "reinitializing resets the event index");
        check(controller.firedEvents() == 0 && !controller.isBlocked(),
              "reinitializing resets the state");

        reject(() -> new ObstructionController("bad", null), "reject null windows");
        reject(() -> new ObstructionController("bad", new double[][]{null}), "reject null window");
        reject(() -> new ObstructionController("bad", new double[][]{{1}}), "reject missing end time");
        reject(() -> new ObstructionController("bad", new double[][]{{4, 4}}), "reject zero-length blockage");
        reject(() -> new ObstructionController("bad", new double[][]{{4, 2}}), "reject backwards window");
        reject(() -> new ObstructionController("bad", new double[][]{{-1, 4}}), "reject negative start");
        reject(() -> new ObstructionController("bad", new double[][]{{Double.NaN, 4}}), "reject NaN");
        reject(() -> new ObstructionController("bad", new double[][]{{1, Double.POSITIVE_INFINITY}}),
               "reject infinite end");
        reject(() -> new ObstructionController("bad", new double[][]{{1, 4}, {3, 5}}),
               "reject overlapping windows");
        reject(() -> new ObstructionController("bad", new double[][]{{10, 20}, {1, 2}}),
               "reject unsorted windows");

        System.out.println("PASS: " + assertions + " ObstructionController smoke assertions (test-only DEVS adapter)");
        System.out.println("PENDING: execution with Dr. Gu's course DEVSJAVA jar and coordinator");
    }

    private static message input(String port, String name) {
        message bag = new message();
        bag.add(new content(port, new entity(name)));
        return bag;
    }
}
