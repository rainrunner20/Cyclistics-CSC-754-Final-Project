package org.cyclistics.devs;

import java.util.Arrays;
import java.util.Collections;
import model.modeling.content;
import model.modeling.message;
import GenCol.entity;

/**
 * These small tests exercise the generator's own transitions without a DEVS coordinator.
 * The test-only adapter is NOT a replacement for the course DEVSJAVA framework.
 */
public final class CyclistGeneratorSmokeTests {
    private static int checks = 0;

    private static void expect(boolean condition, String description) {
        checks++;
        if (!condition) throw new AssertionError(description);
    }

    private static void equal(double actual, double expected, String description) {
        expect(Math.abs(actual - expected) < 1e-8, description + ": " + actual + " vs " + expected);
    }

    private static message stopMessage() {
        message message = new message();
        message.add(new content("stop", new entity("shutdown")));
        return message;
    }

    private static void expectBadSchedule(Runnable operation) {
        try {
            operation.run();
        } catch (IllegalArgumentException expected) {
            checks++;
            return;
        }
        throw new AssertionError("Expected an IllegalArgumentException for invalid schedule");
    }

    public static void main(String[] args) {
        CyclistGenerator generator = new CyclistGenerator("arrivals", Arrays.asList(10.0, 15.0, 30.0));
        generator.initialize();
        equal(generator.ta(), 10.0, "First arrival scheduled at second 10");
        expect("scheduled".equals(generator.getPhase()), "Generator should be active");
        expect(generator.out().getLength() == 1, "First arrival output is present");
        expect("arrival".equals(generator.out().read(0).getPortName()), "Output uses the arrival port");
        expect("cyclist-1".equals(generator.out().getValOnPort("arrival", 0).getName()), "First cyclist ID");

        // In DEVS, output happens before the internal transition at the same time.
        generator.deltint();
        equal(generator.ta(), 5.0, "Second arrival is five seconds after the first");
        expect("cyclist-2".equals(generator.out().getValOnPort("arrival", 0).getName()), "Second cyclist ID");
        generator.deltint();
        equal(generator.ta(), 15.0, "Third arrival is fifteen seconds later");
        generator.deltint();
        expect("passive".equals(generator.getPhase()), "Generator passivates after final arrival");
        expect(generator.emittedCount() == 3, "Tracks all scheduled arrivals");
        expect(generator.out().getLength() == 0, "No output after final arrival");

        CyclistGenerator empty = new CyclistGenerator("empty", Collections.emptyList());
        empty.initialize();
        expect(Double.isInfinite(empty.ta()), "Empty schedule remains passive");

        CyclistGenerator fixed = CyclistGenerator.evenlySpaced("fixed", 120.0, 90.0);
        fixed.initialize();
        equal(fixed.ta(), 30.0, "120/hour gives one arrival every 30 seconds");
        fixed.deltint();
        equal(fixed.ta(), 30.0, "Uniform spacing stays at 30 seconds");
        fixed.deltint();
        fixed.deltint();
        expect(Double.isInfinite(fixed.ta()), "At horizon, all arrivals are emitted");

        // With an external stop at second 3, the generator should not emit at second 10.
        CyclistGenerator stopped = new CyclistGenerator("stopped", Arrays.asList(10.0, 20.0));
        stopped.initialize();
        stopped.deltext(3.0, stopMessage());
        expect(Double.isInfinite(stopped.ta()), "Stop makes generator passive");
        expect(stopped.emittedCount() == 0, "No arrivals emitted before stop");

        // Simultaneous stop at time 10 happens after the output due at time 10.
        CyclistGenerator tied = new CyclistGenerator("tied", Arrays.asList(10.0, 20.0));
        tied.initialize();
        expect("cyclist-1".equals(tied.out().getValOnPort("arrival", 0).getName()), "Arrival output is due at tie");
        tied.deltcon(0, stopMessage());
        expect(tied.emittedCount() == 1, "Due arrival was processed at tie");
        expect(Double.isInfinite(tied.ta()), "Simultaneous stop suppresses future arrivals");

        expectBadSchedule(() -> new CyclistGenerator("bad", Arrays.asList(10.0, 3.0)));
        expectBadSchedule(() -> new CyclistGenerator("bad", Arrays.asList(-1.0)));
        expectBadSchedule(() -> new CyclistGenerator("bad", Arrays.asList(Double.NaN)));
        expectBadSchedule(() -> CyclistGenerator.evenlySpaced("bad", -20.0, 60.0));

        System.out.println("PASS: " + checks + " CyclistGenerator smoke assertions (test-only DEVS adapter)");
        System.out.println("PENDING: compile and execute using course DEVSJAVA jar and coordinator");
    }
}
