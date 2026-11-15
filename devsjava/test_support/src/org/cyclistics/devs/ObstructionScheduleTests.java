package org.cyclistics.devs;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/** Standalone parser tests. No fake coordinator or third-party JAR required. */
public final class ObstructionScheduleTests {
    private ObstructionScheduleTests() { }

    private static double[][] parse(String body) throws Exception {
        Path file = Files.createTempFile("cyclistics-v2-events-", ".csv");
        try {
            Files.writeString(file, body);
            return ObstructionSchedule.readCsv(file);
        } finally {
            Files.deleteIfExists(file);
        }
    }

    private static void shouldReject(String body) throws Exception {
        try {
            parse(body);
            throw new AssertionError("Rejected fixture unexpectedly accepted");
        } catch (IllegalArgumentException expected) {
            // This is the expected parser failure, never a passing model run.
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 1) {
            double[][] imported = ObstructionSchedule.readCsv(Path.of(args[0]));
            if (imported.length != 1 || imported[0][0] != 12 || imported[0][1] != 20) {
                throw new AssertionError("Python bridge CSV did not preserve expected 12–20 s window");
            }
            System.out.println("PASS: real Python-generated event CSV parsed by Java");
            return;
        }
        String header = "time_s,event_type\n";
        double[][] windows = parse(header
                + "12,obstruction_start\n20,obstruction_end\n"
                + "30,obstruction_start\n31,obstruction_end\n");
        if (windows.length != 2 || windows[0][0] != 12 || windows[0][1] != 20
                || windows[1][0] != 30 || windows[1][1] != 31) {
            throw new AssertionError("Unexpected scheduled block windows");
        }
        shouldReject(header + "12,obstruction_start\n");
        shouldReject(header + "20,obstruction_end\n");
        shouldReject(header + "12,obstruction_start\n12,obstruction_end\n");
        shouldReject(header + "12,obstruction_start\n11,obstruction_end\n");
        shouldReject(header + "12,obstruction_start\n13,obstruction_start\n"
                + "20,obstruction_end\n");
        shouldReject(header + "12,other_command\n20,obstruction_end\n");
        shouldReject(header + "NaN,obstruction_start\n20,obstruction_end\n");
        shouldReject(header + "10000001,obstruction_start\n10000002,obstruction_end\n");
        shouldReject("wrong,header\n12,obstruction_start\n20,obstruction_end\n");
        System.out.println("PASS: canonical obstruction CSV parsing and negative cases");
    }
}
