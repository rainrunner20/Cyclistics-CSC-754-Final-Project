# LaneBottleneck — Milestone 2.1C

This folder now contains three independently testable atomic model classes:

- `CyclistGenerator.java` — emits scheduled `arrival` events.
- `ObstructionController.java` — emits `block` and `clear` control events.
- `LaneBottleneck.java` — queues cyclists and emits `departed` events.

Use `Dockerfile.bottleneck-tests` for the third component's **isolated** tests.
These are not coupled-model integration tests. See `docs/devs_bottleneck_design.md`
for formal definitions and the next steps.
