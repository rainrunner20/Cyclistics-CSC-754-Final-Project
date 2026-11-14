# Milestone 2.2B — DEVS-Suite 2.1 API compatibility

## Evidence that motivated the changes

The external binary in the local `devsjava/vendor/` folder was reported as
`DEVS-Suite-2.1.0-20090428.jar` (702,134 bytes). Its `jar tf` output showed:

- `GenCol/entity.class`
- `model/modeling/message.class`, `model/modeling/content.class`
- `view/modeling/ViewableAtomic.class`
- `model/simulation/coordinator.class`

`javap -public` confirmed `message.read(int)` returns `content`,
`content.getPortName()` returns a string, and `message.onPort(String,int)`
checks a particular input message. The previous `message.getPortName(int)`
was a test-adapter convenience, not a method in that external binary.

## Changes

1. Atomic model imports now use the observed `model.modeling` and
   `view.modeling` packages.
2. LaneBottleneck obtains the port of message element `i` using
   `inputs.read(i).getPortName()`; it uses `inputs.onPort("arrival", i)`
   for the per-item check.
3. Unit tests use the same public message interface seen in `javap`.
4. The **test-only adapter** now models these 2.1 packages. Its fake files
   remain strictly separate from the external-JAR build.
5. The Docker test images and external-JAR check are updated accordingly.

## Verify on Windows

From your project root, with the historical JAR present in `devsjava/vendor/`:

```powershell
.\devsjava\scripts\verify-real-devsjava.ps1
```

When it prints `PASS`, production code **compiled against the actual JAR**.
If it fails, use the `javac` errors: inherited helpers like `outputNameOnPort`
are not enumerated in your earlier `javap` output for `atomic`/`ViewableAtomic`.
Don't substitute the fake test adapter to silence a real-JAR error.

Run local smoke tests independently:

```powershell
docker build -f devsjava/Dockerfile.generator-tests -t cyclistics-generator-tests devsjava
docker run --rm cyclistics-generator-tests
docker build -f devsjava/Dockerfile.obstruction-tests -t cyclistics-obstruction-tests devsjava
docker run --rm cyclistics-obstruction-tests
docker build -f devsjava/Dockerfile.bottleneck-tests -t cyclistics-bottleneck-tests devsjava
docker run --rm cyclistics-bottleneck-tests
```

**Still pending:** execute with the real coordinator and verify coupled-model event ordering,
ports, departures, queue metrics, and cross-model results. The historical JAR
is **not confirmed** as Dr. Gu's exact course distribution.
