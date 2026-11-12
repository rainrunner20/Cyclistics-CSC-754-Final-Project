# DEVS-Suite 2.1: remove adapter-only convenience methods

The actual `DEVS-Suite-2.1.0-20090428.jar` does **not** expose two helpers previously supplied by the local test adapter: `outputNameOnPort(...)` and `somethingOnPort(...)`.

- Output uses `new message()` and `output.add(new content(port, new entity(name)))`.
- Input detection uses the external API `message.onPort(port, index)` while iterating over `message.getLength()`.
- CyclistGenerator, ObstructionController and LaneBottleneck still use their original event schedules and the same concurrency priorities.
- The test-only `ViewableAtomic` no longer defines those two helpers, so smoke tests cannot accidentally rely on methods absent from the external library.

**Verification:** run `./devsjava/scripts/verify-real-devsjava.ps1` from the repo root with the DEVS-Suite JAR in `devsjava/vendor/`. Then rebuild and run all three Docker smoke-test images. These changes only address the six compiler errors reported in Milestone 2.2B. Production compilation and real coordinator execution require separate confirmation on the user's machine.
