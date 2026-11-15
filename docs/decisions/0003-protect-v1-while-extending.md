# ADR 0003 — Preserve verified Cyclistics v1 while experimenting with live digital-twin features

**Status:** Accepted as an experimental architecture decision, November 14, 2026

## Context

Cyclistics v1 has separately executable and tested Python DES, Java DEVS-Suite and NetLogo models, plus 160-pair sensitivity evidence and a 36-run headless NetLogo benchmark. Adding camera detections, adjacent traffic, lane changes and streaming orchestration changes the dynamics and data provenance. It would be misleading to retroactively reuse the original validation checks or claim unchanged research results.

## Decision

1. **Do not overwrite the v1 one-lane NetLogo model or original experimental CSVs.** Experimental multi-lane traffic belongs in a new named model with separate controls, output directories, checks and captions.
2. **Separate observations, interpretations and simulated actions.** A vision model's bounding box means "candidate object"; only an explicit, traceable decision may create an obstruction scenario. Detection confidence is not proof of a real blockage.
3. **Version all event contracts.** Keep source event ID, observation time, provenance and validation status. A simulated event must add explicit scenario ID and simulation-time mapping rather than reinterpreting wall time as model time.
4. **Prove deterministic replay before claiming live coordination.** NetLogo uses global ticks, Java DEVS-Suite uses event-time advances, and Python DES has its own tie policy. A CSV importer is not itself real-time two-way coupling.
5. **Treat TTC and PET as surrogate conflict indicators only.** A realistic crash-probability prediction requires validated vehicle geometry, trajectories, exposure definitions and independent incident data.
6. **Make dependencies optional.** The verified core Python package remains usable without Roboflow credentials, proprietary ArcGIS keys, Java JARs or a live camera.
7. **Do not publish personal camera footage, location identifiers, API secrets or third-party libraries into the repository.** Any needed data should have explicit permission and retention policy.
8. **Re-run v1 regression checks on every experimental PR.** Experimental model changes cannot silently rewrite prior figures, conclusions or historical test data.

## Alternatives considered

- **Rewrite the existing NetLogo lane in-place:** rejected; it would invalidate previously recorded baselines and their hashes.
- **Connect everything over sockets immediately:** rejected for the first increment; unsolved time mapping, event deduplication and recovery would make output attribution unreliable.
- **Label collision counts as NYC crashes:** rejected; the model does not observe or estimate validated real collisions.
- **Build only presentation mockups:** rejected as a substitute for functioning detection, traffic and mapping software.

## Consequences

The final report can present the original verified results as **v1** and any implemented, tested extensions as a separately labeled **experimental v2**. New feature branches and PRs are maintained, and extra functionality is described as *planned* until code and real execution prove it works. The current academic paper remains a deliverable even if later optional extensions are not yet complete.
