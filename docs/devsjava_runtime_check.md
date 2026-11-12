# Milestone 2.2A: Compile against the external DEVSJAVA library

## Why this exists

Cyclistics currently has three Java atomic models: CyclistGenerator,
ObstructionController, and LaneBottleneck. The local smoke tests use a
small **test-only adapter**. A successful smoke test is **not** the same as
compiling with the professor's DEVSJAVA library or executing its coordinator.

The 2003 DEVSJAVA manuscript linked from the CSC 754 course website
covers atomic and coupled models and the parallel-DEVS simulation protocol.
It also warns that simplified textbook signatures should not be used for
debugging an actual Java distribution. We therefore check the **real binary API**.

## What to obtain

Use the version of the DEVSJAVA JAR(s) actually provided by CSC 754 if
available. Put all JARs directly in `devsjava/vendor/` without committing them.
The historical DEVS-Suite 2.1.0 file linked in `devsjava/vendor/README.md`
is an *optional compatibility candidate*, not a verified course distribution.

## Check on Windows / VS Code

From the repository root, on `feat/devs-atomic-models`:

```powershell
git branch --show-current
git status
Get-ChildItem .\devsjava\vendor\*.jar | Select-Object Name, Length
.\devsjava\scripts\verify-real-devsjava.ps1
```

The PowerShell script starts a Java 17 Docker container. Inside it, the Bash
script looks for required `GenCol`, `genDevs`, and `simView` classes and compiles
only production sources with `javac`. Test adapter classes are excluded.

**PASS** means only that the three production models compiled against the
provided JAR(s). It does not mean the DEVS scheduler, couplings, or simulation
outputs have been tested. If compilation fails, save the actual error messages;
we must adapt our code to the installed API rather than bypass the failure.

## Follow-up

Once compilation passes, implement a real coordinator-driven end-to-end run
with three atomic models, using documented couplings and small deterministic
arrivals/blockages. Compare event times, departure order, and queue statistics
to the Python reference model where assumptions match.

## Research sources

- CSC 754 class page: https://www.cs.csi.cuny.edu/~gu/teaching/courses/csc754/csc754.html
- Class DEVSJAVA manuscript: https://www.cs.csi.cuny.edu/~gu/teaching/courses/csc754/slides/DEVSJAVA_Manuscript.pdf
- Arizona Center for Integrative Modeling and Simulation DEVS-Suite archives:
  https://acims.asu.edu/devs-suite-documentation
