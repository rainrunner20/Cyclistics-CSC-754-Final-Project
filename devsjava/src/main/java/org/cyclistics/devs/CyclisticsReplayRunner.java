package org.cyclistics.devs;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import model.simulation.coordinator;

/**
 * Replay reviewed offline blockage windows with the actual DEVS-Suite library.
 *
 * This is NOT live data streaming or Java–NetLogo clock synchronization.
 * The coordinator clock is in simulated seconds, not camera UTC timestamps.
 */
public final class CyclisticsReplayRunner {
    private CyclisticsReplayRunner() { }

    private static List<Double> parseArrivals(String csv) {
        String[] tokens = csv.split(",", -1);
        if (tokens.length == 0 || tokens.length > 2000) {
            throw new IllegalArgumentException("Provide one to 2000 arrival seconds");
        }
        List<Double> arrivals = new ArrayList<>();
        double previous = -1;
        for (String token : tokens) {
            double t;
            try {
                t = Double.parseDouble(token);
            } catch (NumberFormatException exc) {
                throw new IllegalArgumentException("Invalid arrival timestamp", exc);
            }
            if (!Double.isFinite(t) || t < 0 || t <= previous) {
                throw new IllegalArgumentException("Arrivals must be finite, sorted and unique");
            }
            arrivals.add(t);
            previous = t;
        }
        return arrivals;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            throw new IllegalArgumentException(
                    "Usage: CyclisticsReplayRunner <events.csv> <arrivals-s> <headway-s>"
                    + " (example: events.csv 10,15 4)");
        }
        double[][] blockWindows = ObstructionSchedule.readCsv(Path.of(args[0]));
        List<Double> arrivals = parseArrivals(args[1]);
        double headway = Double.parseDouble(args[2]);
        if (!Double.isFinite(headway) || headway <= 0) {
            throw new IllegalArgumentException("Passage headway must be positive");
        }

        CyclisticsCoupledModel model = new CyclisticsCoupledModel(
                "CyclisticsOfflineReplay", arrivals, blockWindows, headway);
        // This is the actual external DEVS-Suite coordinator, NOT a test adapter.
        coordinator simulation = new coordinator(model);
        simulation.initialize();
        simulation.simulate(10000);

        List<LaneBottleneck.Departure> departures = model.lane().departureTrace();
        for (LaneBottleneck.Departure departure : departures) {
            System.out.printf(Locale.ROOT, "DEPARTURE,%.3f,%s%n",
                    departure.timeSeconds(), departure.cyclistId());
        }
        System.out.println("Cyclistics offline DEVS-Suite replay summary:");
        System.out.println("  generated=" + model.generator().emittedCount());
        System.out.println("  obstruction events=" + model.obstructions().firedEvents());
        System.out.println("  departed=" + model.lane().departedCount());
        System.out.println("  max waiting=" + model.lane().maxWaitingQueue());

        if (model.generator().emittedCount() != arrivals.size()
                || model.obstructions().firedEvents() != blockWindows.length * 2
                || model.lane().departedCount() != departures.size()) {
            throw new AssertionError("External Java coordinator accounting mismatch");
        }
        System.out.println("PASS: actual coordinator processed the provided offline schedule.");
        System.out.println("NOTE: not live NetLogo–Java synchronization or NYC validation.");
    }
}
