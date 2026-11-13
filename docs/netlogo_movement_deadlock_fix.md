# Cyclistics NetLogo: fractional movement deadlock fix

## Observation

The model opened and completed 600 ticks, but the screenshot showed demand=107, on lane=38, departed=6, queue=101, peak queue=101, and conservation=true. It should not leave so many cyclists queued after a temporary obstruction clears at t=110 under low baseline demand.

## Root cause

The previous `move-cyclist` logic interpreted **any movement less than 0.01 patches** as a full stop **and omitted that motion entirely**. A rider within 0.01 patches of the exit could therefore never finish, blocking every rider behind it. Cycling throughput could collapse even without a truck. Conservation still passed because no cyclists were deleted.

## Fix

Always apply a positive step, no matter how small. Count a full-stop tick only when movement is effectively zero (<= 1e-9). The front-to-back iteration fix from the previous hotfix is retained.

## How to verify with actual NetLogo

1. Close the model without saving, extract this ZIP into the repository root, and reopen the `.nlogo` file.
2. At the default settings (arrival-rate-per-hour=600, blockage-enabled=1, start=45, duration=65, seed=754, run-length=600), press **setup**, then **go**. The queue should rise around the obstruction and subsequently clear/recover rather than continuously grow until tick 600.
3. In Command Center, run `show (list requested-arrivals departed-count pending-arrivals count cyclists queue-now max-queue)` and `show conservation-ok?`.
4. Repeat with `blockage-enabled=0`, same seed and arrival rate. Compare departures, queue, and mean stopped time.
5. The static tests verify source structure only. NetLogo desktop execution and screenshot are the actual runtime checks.

This is a synthetic ABM prototype and not an empirical crash-risk or travel-time prediction.
