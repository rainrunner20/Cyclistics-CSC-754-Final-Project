package org.cyclistics.devs;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Strictly parse reviewed offline blockage events into DEVS-Suite windows.
 *
 * Simulation seconds are not UTC observation times. Only canonical event CSVs
 * should reach this class, and we still validate the final Java boundary.
 */
public final class ObstructionSchedule {
    private ObstructionSchedule() { }

    public static double[][] readCsv(Path path) throws IOException {
        List<String> lines = Files.readAllLines(path);
        if (lines.size() < 3 || !lines.get(0).equals("time_s,event_type")) {
            throw new IllegalArgumentException("Need a header and paired obstruction events");
        }
        List<double[]> intervals = new ArrayList<>();
        int previous = -1;
        Integer start = null;
        for (int i = 1; i < lines.size(); i++) {
            String[] cells = lines.get(i).split(",", -1);
            if (cells.length != 2) {
                throw new IllegalArgumentException("Expected two CSV columns on line " + (i + 1));
            }
            int time;
            try {
                time = Integer.parseInt(cells[0]);
            } catch (NumberFormatException exc) {
                throw new IllegalArgumentException("Invalid simulation tick on line " + (i + 1), exc);
            }
            if (time < 0 || time > 10_000_000 || time < previous) {
                throw new IllegalArgumentException("Nonnegative, sorted simulation ticks required");
            }
            if (cells[1].equals("obstruction_start")) {
                if (start != null) {
                    throw new IllegalArgumentException("Overlapping obstruction start");
                }
                start = time;
            } else if (cells[1].equals("obstruction_end")) {
                if (start == null || time <= start) {
                    throw new IllegalArgumentException("Unmatched or nonpositive obstruction interval");
                }
                intervals.add(new double[]{start, time});
                start = null;
            } else {
                throw new IllegalArgumentException("Unknown event type: " + cells[1]);
            }
            previous = time;
        }
        if (start != null) {
            throw new IllegalArgumentException("Unclosed obstruction");
        }
        return intervals.toArray(new double[0][]);
    }
}
