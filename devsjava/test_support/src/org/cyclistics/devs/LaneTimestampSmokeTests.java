package org.cyclistics.devs;

import java.util.List;
import GenCol.entity;
import model.modeling.content;
import model.modeling.message;

/** Test-only transition harness: validates model bookkeeping without DEVS-Suite. */
public final class LaneTimestampSmokeTests {
    private static int checks;
    private static void check(boolean ok, String description) {
        checks++;
        if (!ok) throw new AssertionError(description);
    }
    private static message event(String port, String value) {
        message bag = new message();
        bag.add(new content(port, new entity(value)));
        return bag;
    }
    private static void departure(LaneBottleneck.Departure d, String id, double t) {
        check(d.cyclistId().equals(id), "departure id " + id);
        check(Math.abs(d.timeSeconds() - t) < 1e-9, "departure time " + t);
    }
    public static void main(String[] args) {
        // Inputs: 10 arrival, 12 block, 15 arrival, 20 clear.
        // One cyclist in service finishes at 14 despite the blockage.
        LaneBottleneck lane = new LaneBottleneck("lane", 4.0);
        lane.initialize();
        lane.deltext(10, event("arrival", "cyclist-1"));
        lane.deltext(2, event("block", "truck"));
        lane.deltint(); // 14: complete cyclist-1
        lane.deltext(1, event("arrival", "cyclist-2"));
        check(lane.waitingCount() == 1, "waiting during blockage");
        lane.deltext(5, event("clear", "truck-left"));
        lane.deltint(); // 24: complete cyclist-2
        List<LaneBottleneck.Departure> trace = lane.departureTrace();
        check(trace.size() == 2, "two completions recorded");
        departure(trace.get(0), "cyclist-1", 14.0);
        departure(trace.get(1), "cyclist-2", 24.0);
        check(lane.maxWaitingQueue() == 1, "max queue of one");
        check(lane.departedCount() == 2, "two departures total");
        check(lane.waitingCount() == 0, "queue drained");
        check(!lane.isServing(), "no service remains");

        // A departure tied with a fresh BLOCK must be recorded at exactly
        // the scheduled completion time; the new queue stays blocked.
        LaneBottleneck tie = new LaneBottleneck("tie", 3.0);
        tie.initialize();
        tie.deltext(0, event("arrival", "a"));
        tie.deltext(1, event("arrival", "b"));
        tie.deltcon(0, event("block", "delivery")); // time 3
        check(tie.isBlocked(), "block applies at departure tie");
        check(tie.waitingCount() == 1, "b remains queued");
        departure(tie.departureTrace().get(0), "a", 3.0);
        tie.deltext(2, event("clear", "departure")); // time 5
        tie.deltint(); // time 8
        departure(tie.departureTrace().get(1), "b", 8.0);

        // Ensure that clients cannot modify the stored trace.
        boolean immutable = false;
        try {
            trace.clear();
        } catch (UnsupportedOperationException expected) {
            immutable = true;
        }
        check(immutable, "trace accessor returns immutable data");
        check(lane.departureTrace().size() == 2, "internal records are intact");
        lane.initialize();
        check(lane.departureTrace().isEmpty(), "restart clears the trace");

        System.out.println("PASS: " + checks + " LaneBottleneck timestamp assertions (test-only adapter)");
    }
}
