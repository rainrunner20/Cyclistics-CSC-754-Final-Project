# DEVSJAVA milestone 2.1A — CyclistGenerator

A small, testable first atomic model. The `test_support/` classes are lightweight **testing stand-ins**, not the course's DEVSJAVA runtime.

From repository root, build and run with Docker:

```powershell
docker build -f devsjava/Dockerfile.generator-tests -t cyclistics-generator-tests devsjava
docker run --rm cyclistics-generator-tests
```

Then keep running the existing Python regression tests:

```powershell
docker compose run --build --rm tests
```

Next milestone: get the actual DEVSJAVA JAR/source used in CSC 754 and verify the Java model against it before implementing the coupled simulation.
