# Milestone 3.8B — Measured NetLogo computational performance (GitHub-hosted Linux)

**Run date:** November 14, 2026 (America/New_York; GitHub Actions recorded November 15, 2026 UTC).  
**Verified execution:** [GitHub Actions run 43666376890](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43666376890), **successful**.  
**Download raw outputs:** [NetLogo performance artifact 14141653620](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43666376890/artifacts/14141653620) (GitHub artifact subject to retention).  
**Tested source:** commit `a556870338f80882438216d5a1d31185e9835d7a`.

## Experiment and provenance

A real **NetLogo 6.3.0 headless engine** ran using the official 6.3.0 Linux tarball in GitHub Actions, not Python's synthetic unit-test fixtures. Its BehaviorSpace setup invoked the unmodified `run-verification-suite` and `run-runtime-benchmarks` procedures in `Cyclistics_Bike_Lane_ABM.nlogo`:

- **5/5 verification cases passed**, including zero demand, replay and obstruction scheduling.
- **36/36 benchmark trials** were completed and validated.
- The analyzer generated **12 grouped runtime results**, two SVG plots, and a SHA-256 manifest.
- Raw CSVs and figures were downloaded and their **four generated-output SHA-256 digests plus two raw-input digests** were recomputed independently from the GitHub artifact ZIP; all six matched its manifest.

Cloud environment recorded in the artifact: **GitHub-hosted Ubuntu 22.04**, NetLogo **6.3.0**, OpenJDK **11.0.33**, Python **3.12.16**. The NetLogo version supports Java 11+. The elapsed time is **wall-clock computation time on a shared cloud runner**, not measured time on the user's Windows computer. No real NYC bicycle data, real street validation, or Java-versus-NetLogo runtime comparison was involved.

NetLogo `setup` is excluded from each measured trial; a separate unmeasured 100-tick warmup runs before the benchmark grid. The model suppresses view updates. The design has 3 attempted arrival rates (150, 600, 900 cyclists/hour) × 2 obstruction flags × 2 horizons (600, 1,200 simulated seconds) × 3 seeds (201–203).

## Measured results

**Warning:** These are very short timings (about 0.004–0.024 wall-clock seconds for an entire run). They are sensitive to timer resolution, JVM warmup, scheduling jitter and shared runner load. The table is a **descriptive engineering smoke benchmark**, not strong evidence of computational scaling or a stable obstruction cost.

| Attempted cyclists/h | Obstruction | Simulated horizon (s) | Mean elapsed (wall-clock s) | Mean ms per simulated tick |
| ---: | :---: | ---: | ---: | ---: |
| 150 | Off | 600 | 0.00600 | 0.0100 |
| 150 | On | 600 | 0.00800 | 0.0133 |
| 600 | Off | 600 | 0.00767 | 0.0128 |
| 600 | On | 600 | 0.00833 | 0.0139 |
| 900 | Off | 600 | 0.01100 | 0.0183 |
| 900 | On | 600 | 0.01033 | 0.0172 |
| 150 | Off | 1200 | 0.00767 | 0.0064 |
| 150 | On | 1200 | 0.00667 | 0.0056 |
| 600 | Off | 1200 | 0.01633 | 0.0136 |
| 600 | On | 1200 | 0.01433 | 0.0119 |
| 900 | Off | 1200 | 0.01933 | 0.0161 |
| 900 | On | 1200 | 0.02033 | 0.0169 |

All values are rounded for readability; the source CSV and `performance_table.csv` retain six-decimal summaries. Each row summarizes **three measured seeds**.

**Interpretation:** Runtime per simulated tick is small in this simplified single-lane model, and the 900/h groups generally take longer than the 150/h groups. Some blocked runs are faster than clear runs and some longer horizons have lower milliseconds-per-tick; this **is not evidence that obstructions improve computational performance**. These patterns reflect low-resolution and noisy, short timings and the small three-replicate sample. We do **not** report statistically significant differences, model-wide scaling complexity, maximum supported city size, or real-world traffic predictions.

## Generated figures

1. **`netlogo_runtime_600s.svg`** — milliseconds of computation per simulated tick vs. attempted cyclist demand for 600-tick trials, separate lines for obstruction on/off.
2. **`netlogo_runtime_1200s.svg`** — same comparison for 1,200-tick trials.

Both exported vector figures were visually opened for review. They correctly label **measured ms per simulation tick**, three demand levels, and two obstruction states; their y-axis scales differ by horizon, so visual slope or vertical displacement should not be used to compare absolute values across figures. The graphics do **not** include confidence intervals. Given measurement noise, use one runtime figure as a **supporting methodology graphic**, not the paper's main scientific result.

## SHA-256 audit of the archived evidence

The following SHA-256 digests came from the GitHub-hosted NetLogo job's manifest and were separately verified from the downloaded ZIP bytes:

| Evidence file | SHA-256 |
| --- | --- |
| `netlogo_verification_checks.csv` | `70dff43eb72730b4c2e34a7b50528aa9236623caf1cb0e984c40a59311143f72` |
| `netlogo_runtime_benchmarks.csv` | `8de93ac0bc921464bd8e77aa7dd5baf31459fb363a993125d6a5006883172cb0` |
| `performance_table.csv` | `a5b903ea23037040d2b8b8a44e11c316743a053c68817d52d1ccc29dbad3663e` |
| `performance_table.md` | `4dd9a83b08b2f8546c1d85cf6ff31dd8e5e2035833f3b66ee64597abbe255b79` |
| `netlogo_runtime_600s.svg` | `90fac04aa85adee5580b79be3244f137dd6f5fc057ac10e1c4fa7c000c9b1540` |
| `netlogo_runtime_1200s.svg` | `490e38c3c18ed2e5342580da02b63bb8a7f415922889646c3532f6fda717404e` |

The artifact also includes `performance_manifest.json` (with code/model source digests) and `runner_environment.txt`. Source and output ZIP artifacts are **not** committed to Git history, to keep research measurements distinct from software code. The GitHub artifact may expire after 30 days; download and retain it with the project's submission materials.

## Contrast with DEVSJAVA

NetLogo operates with **fixed one-second global simulation ticks**. The existing **Java DEVS-Suite coordinator** advances between scheduled input/internal events and was verified against the Python DES reference only on the **two-cyclist deterministic fixture** (departures at 14 and 24 modeled seconds). The NetLogo cloud-run timing charts do **not** measure or compare DEVSJAVA performance. A fair engine-to-engine performance study would require aligned model assumptions, identical workloads and hardware, and sufficient repeated measurements.

**Bottom line for CSC 754:** We can explain and reproduce both a functional verification suite and a real computational timing experiment. We cannot yet claim NYC field validation, production-ready city scalability, or statistical performance superiority.
