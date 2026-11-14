package org.cyclistics.devs;

import GenCol.entity;
import model.modeling.content;
import model.modeling.message;

/** Run atomic transition checks without downloading JUnit or the course JAR. */
public final class LaneBottleneckSmokeTests {
    private static int passed;

    private static void check(boolean condition, String label) {
        if (!condition) {
            throw new AssertionError(label);
        }
        passed++;
    }

    private static void number(double expected, double actual, String label) {
        check(Math.abs(expected - actual) < 1e-9,
                label + " (wanted " + expected + ", got " + actual + ")");
    }

    private static void text(String expected, String actual, String label) {
        check(expected.equals(actual),
                label + " (wanted " + expected + ", got " + actual + ")");
    }

    private static message input(String port, String value) {
        message bag = new message();
        bag.add(new content(port, new entity(value)));
        return bag;
    }

    private static void invalid(Runnable operation, String label) {
        boolean rejected = false;
        try {
            operation.run();
        } catch (IllegalArgumentException expected) {
            rejected = true;
        }
        check(rejected, label);
    }

    private static String departure(LaneBottleneck lane) {
        message output = lane.out();
        check(output.getLength() == 1, "one cyclist departs per internal event");
        text("departed", output.read(0).getPortName(), "correct DEVS output port");
        return output.getValOnPort("departed", 0).getName();
    }

    private static void testIdleAndFIFO() {
        LaneBottleneck lane = new LaneBottleneck("lane", 3.0);
        lane.initialize();
        check(Double.isInfinite(lane.ta()), "idle lane is passive");
        check(lane.out().getLength() == 0, "passive lane has no output");
        check(!lane.isBlocked() && !lane.isServing(), "lane starts clear and idle");
        check(lane.waitingCount() == 0 && lane.departedCount() == 0, "initial counters are zero");

        lane.deltext(0, input("arrival", "alice"));
        text("alice", lane.currentCyclist(), "alice starts passage");
        number(3, lane.ta(), "first passage completes in 3 seconds");
        check(lane.waitingCount() == 0, "cyclist in service is not waiting");

        lane.deltext(1, input("arrival", "bob"));
        number(2, lane.ta(), "bob does not reset alice's remaining time");
        lane.deltext(0.5, input("arrival", "cara"));
        number(1.5, lane.ta(), "second arrival also preserves remaining passage time");
        check(lane.waitingCount() == 2, "bob and cara are waiting");
        check(lane.maxWaitingQueue() == 2, "peak waiting line excludes in-service cyclist");

        text("alice", departure(lane), "alice is first to depart");
        check(lane.departedCount() == 0, "out() must not change the state");
        lane.deltint();
        text("bob", lane.currentCyclist(), "bob is served second");
        number(3, lane.ta(), "next passage starts after alice leaves");
        text("bob", departure(lane), "bob departs second");
        lane.deltint();
        text("cara", departure(lane), "cara departs third");
        lane.deltint();
        check(lane.departedCount() == 3, "three cyclists departed");
        check(lane.waitingCount() == 0, "queue fully drained");
        check(Double.isInfinite(lane.ta()), "lane passivates after all departures");
        check(lane.out().getLength() == 0, "no extra departure while idle");
        check(lane.maxWaitingQueue() == 2, "peak waiting queue remains recorded");

        lane.initialize();
        check(lane.departedCount() == 0 && lane.maxWaitingQueue() == 0,
                "reinitialize resets recorded statistics");
    }

    private static void testBlockedDuringPassage() {
        LaneBottleneck lane = new LaneBottleneck("blocked", 4.0);
        lane.initialize();
        lane.deltext(0, input("arrival", "already-passing"));
        lane.deltext(1, input("block", "truck"));
        check(lane.isBlocked(), "lane becomes blocked");
        number(3, lane.ta(), "ongoing cyclist still has three seconds left");
        lane.deltext(1, input("arrival", "waiting-one"));
        lane.deltext(0, input("arrival", "waiting-two"));
        check(lane.waitingCount() == 2, "both new cyclists wait during blockage");
        number(2, lane.ta(), "blockage does not interrupt ongoing service");
        text("already-passing", departure(lane), "ongoing cyclist may finish");
        lane.deltint();
        check(lane.departedCount() == 1, "one cyclist finished during blockage");
        check(!lane.isServing() && Double.isInfinite(lane.ta()), "no new passage until clear");
        lane.deltext(0, input("clear", "truck-left"));
        check(!lane.isBlocked(), "clearance opens lane");
        text("waiting-one", lane.currentCyclist(), "first waiting cyclist starts");
        number(4, lane.ta(), "clearance schedules fresh passage");
        text("waiting-one", departure(lane), "FIFO after clearance");
        lane.deltint();
        text("waiting-two", departure(lane), "second queued cyclist departs next");
        lane.deltint();
        check(lane.departedCount() == 3, "everyone eventually leaves");
    }

    private static void testControlPriorityAndBagOrdering() {
        LaneBottleneck lane = new LaneBottleneck("at-start", 3.0);
        lane.initialize();
        message bag = input("arrival", "waiting-first");
        bag.add(new content("block", new entity("truck")));
        bag.add(new content("arrival", new entity("waiting-second")));
        lane.deltext(0, bag);
        check(lane.isBlocked(), "block wins over arrival at same time");
        check(lane.waitingCount() == 2, "both simultaneous arrivals queue");
        check(!lane.isServing() && Double.isInfinite(lane.ta()), "blocked idle lane stays passive");
        lane.deltext(0, input("clear", "clear"));
        text("waiting-first", lane.currentCyclist(), "simultaneous arrivals preserve bag order");
        text("waiting-first", departure(lane), "first waiting cyclist departs first");
        lane.deltint();
        text("waiting-second", departure(lane), "second waiting cyclist departs second");
        lane.deltint();

        LaneBottleneck conflict = new LaneBottleneck("conflict", 3.0);
        conflict.initialize();
        conflict.deltext(0, input("block", "truck"));
        message both = input("clear", "gone");
        both.add(new content("arrival", new entity("new-cyclist")));
        both.add(new content("block", new entity("another-truck")));
        conflict.deltext(0, both);
        check(conflict.isBlocked(), "block wins if clear and block arrive together");
        check(conflict.waitingCount() == 1 && !conflict.isServing(), "no passage starts on control tie");
        conflict.deltext(0, input("clear", "gone"));
        text("new-cyclist", conflict.currentCyclist(), "later clear starts queued passage");
    }

    private static void testConfluentTransitions() {
        LaneBottleneck lane = new LaneBottleneck("tied", 3.0);
        lane.initialize();
        lane.deltext(0, input("arrival", "first"));
        lane.deltext(1, input("arrival", "second"));
        text("first", departure(lane), "output is computed before tied transition");
        message tied = input("block", "truck");
        tied.add(new content("arrival", new entity("third")));
        lane.deltcon(0, tied);
        check(lane.departedCount() == 1, "first cyclist finishes on confluent event");
        check(lane.isBlocked(), "simultaneous block takes effect");
        check(lane.waitingCount() == 2 && !lane.isServing(),
                "second and third cyclists stay queued");
        lane.deltext(0, input("clear", "cleared"));
        text("second", departure(lane), "FIFO resumes after tie is cleared");
        lane.deltint();
        text("third", departure(lane), "third cyclist is served last");
        lane.deltint();

        LaneBottleneck clearTie = new LaneBottleneck("clear-tie", 5.0);
        clearTie.initialize();
        clearTie.deltext(0, input("arrival", "serving"));
        clearTie.deltext(0, input("block", "truck"));
        clearTie.deltext(0, input("arrival", "waiting"));
        text("serving", departure(clearTie), "current passage completes at tie");
        clearTie.deltcon(0, input("clear", "truck-left"));
        text("waiting", clearTie.currentCyclist(), "clear-on-tie starts queued passage");
        number(5, clearTie.ta(), "new passage uses full headway");
    }

    private static void testBadInputs() {
        invalid(() -> new LaneBottleneck("invalid", 0), "zero passage time rejected");
        invalid(() -> new LaneBottleneck("invalid", -1), "negative passage time rejected");
        invalid(() -> new LaneBottleneck("invalid", Double.NaN), "NaN passage time rejected");
        invalid(() -> new LaneBottleneck("invalid", Double.POSITIVE_INFINITY),
                "infinite passage time rejected");

        LaneBottleneck lane = new LaneBottleneck("bad-input", 3.0);
        lane.initialize();
        invalid(() -> lane.deltext(0, null), "null input bag rejected");
        invalid(() -> lane.deltext(0, input("unknown", "value")), "unknown port rejected");
        message broken = input("arrival", "good");
        broken.add(new content("arrival", null));
        invalid(() -> lane.deltext(0, broken), "missing cyclist identity rejected");
        check(lane.waitingCount() == 0 && !lane.isServing(),
                "invalid bag cannot partially add cyclists");
        invalid(() -> lane.deltext(-1, new message()), "negative elapsed time rejected");
    }

    public static void main(String[] args) {
        testIdleAndFIFO();
        testBlockedDuringPassage();
        testControlPriorityAndBagOrdering();
        testConfluentTransitions();
        testBadInputs();
        System.out.println("PASS: " + passed + " LaneBottleneck smoke assertions (test-only DEVS adapter)");
        System.out.println("PENDING: compile and execute with actual CSC 754 DEVSJAVA jar/coordinator");
    }
}
