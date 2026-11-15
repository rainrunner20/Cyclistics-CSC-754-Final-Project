# CSC 754 Cyclistics — final individual paper and presentation blueprint

**Purpose:** Convert the implemented repository into a clear, reproducible academic submission. This is an **outline and drafting guide**, not a claim that the final paper/slides or external bibliography have already been completed.

**Suggested paper target:** 10–12 pages, subject to Dr. Gu's latest instructions (do not exceed his stated maximum of 20 without permission). The sample page allocation below totals approximately **11 pages including figures and references**; adjust to the required formatting.

## One-sentence project pitch (ELI5)

*Cyclistics tests what happens to a simulated bike lane when a truck blocks it: cyclist agents form queues, a discrete-event model schedules the blockage and departures, and controlled experiments show how cyclist demand and blockage duration change the outcome.*

## Research questions and supported findings

| Question | Evidence to use | Wording to avoid |
| --- | --- | --- |
| What happens to queue lengths as bicycle demand and blockage duration grow? | [160-pair NetLogo study](research_sensitivity_findings.md): all tested nonzero obstruction combinations increase mean simulated waiting counts | "We measured NYC queueing"; "we proved how much travel time will increase in Brooklyn" |
| Do Python and Java DEVS-Suite implement one small event schedule consistently? | [Two-cyclist fixture](cross_model_comparison_results.md): 14 s and 24 s departures; peak waiting queue 1 | "All three engines produce identical results"; "all event schedules are verified" |
| Does the model conserve riders and replay deterministically? | 151 Python tests, genuine NetLogo verification suites, paired-input checks | "Tests prove all real-world predictions are correct" |
| How much computation does a small NetLogo experiment require? | [GitHub-hosted runtime evidence](performance_evidence_results.md): 36 timed trials, 12 summary groups | "NetLogo is faster than DEVSJAVA"; "the timing figures demonstrate city-scale readiness" |
| How can measured NYC counts inform demand? | [Prospect Park West provisional count stream](nyc_prospect_park_west_calibration.md) | "The recorded queue predictions are field-calibrated and validated" |

## Recommended paper structure (~11 pages)

| Section | Approx. pages | What to write |
| --- | ---: | --- |
| 1. Abstract and introduction | 1.0 | Urban lane-blocking motivation; problem, objective, contributions and scientific scope |
| 2. Related work | 1.0 | Peer-reviewed sources on urban digital twins, cyclist modeling, ABM/DEVS, and simulation verification; **cite actual papers you have read**, not invented references |
| 3. Architecture and modeling formalisms | 2.0 | Pipeline graphic; Python event list; Java DEVS atomic/coupled tuple; NetLogo agents/ticks |
| 4. Data and experimental methodology | 2.0 | NYC raw count limitations; sensitivity grid; paired random seeds; queue definitions; verification and runtime conditions |
| 5. Results and discussion | 2.5 | Main sensitivity figure and table; confidence intervals; deterministic Java/Python fixture; one runtime benchmark graphic and its noise caveats |
| 6. Verification, threats to validity | 1.0 | Tests, replay and conservation; external data gaps, simplifications, model mismatch, limits of small samples |
| 7. Conclusion and future work | 0.5 | What was learned; realistic extensions, not claims of functionality |
| References and captions | 1.0 | References for every external factual claim, algorithm/design attribution and figure |

The allocation above is an *editing budget*, not a school-mandated structure. Verify actual formatting, page count and submission date against the syllabus or professor.

### Suggested abstract starter (revise after paper is complete)

> Bicycle-lane obstructions can create temporary bottlenecks, but their modeled effects depend on the demand rate, obstruction duration, and representation of cyclist behavior. Cyclistics is a reproducible prototype combining a Python discrete-event reference, a Java DEVS-Suite atomic/coupled model, and a standalone NetLogo agent-based bicycle-lane model. A controlled NetLogo sensitivity experiment varies four attempted arrival rates and four blockage durations across ten paired seeds, creating 160 paired outcome records. Within the synthetic one-lane model, larger demand and longer obstructions produce higher average and peak waiting queues. At 900 attempted cyclists/hour and a 120-second obstruction, the mean blocked-minus-clear waiting-queue difference is 3.369 cyclists (individual approximate 95% paired t interval: 2.940–3.798). Separately, the Python and Java event models agree on two departure timestamps in one deterministic scenario, and a headless NetLogo run provides a limited machine-dependent runtime benchmark. These findings demonstrate internally verified simulation behavior rather than validated predictions of NYC street conditions.

Keep a formal **"Contributions"** sentence focused on (a) independently implemented formalisms, (b) paired experiments and validation checks, and (c) reproducible evidence/provenance. Do not characterize this as a live digital twin.

## Figures — strongest evidence first

1. **Figure 1 — architecture:** [Current architecture](architecture.md) diagram. Caption: *Separate Python discrete-event, Java coupled-DEVS and NetLogo agent-based implementations; arrows denote inputs and analysis, not live inter-engine synchronization.*
2. **Figure 2 — NetLogo spatial screenshot:** Capture directly from the running .nlogo file with cyclists stopped at the schematic truck obstruction; include clearly legible queue plot and scenario parameters. **Not yet supplied as the final screenshot.**
3. **Figure 3 — primary experiment chart:** locally exported `outputs/research_evidence/netlogo_delta_mean_queue.svg`; [research findings](research_sensitivity_findings.md) provide numeric values and 95% paired t intervals. Caption: *Simulated blocked-minus-clear mean waiting queue versus obstruction duration at four attempted arrival rates (10 paired seeds per condition; individual approximate 95% t intervals).*
4. **Figure 4 — secondary experiment chart or table:** `outputs/research_evidence/netlogo_delta_peak_queue.svg` or a condensed subset of the 16-row result table. Caption: *Mean across seeds of paired changes in each run's maximum waiting queue; not a single-run queue maximum.*
5. **Figure 5 — optional verification diagram:** 10/12/14/15/20/24-second event sequence in [comparison results](cross_model_comparison_results.md), explicitly labeled a schematic of the deterministic fixture.
6. **Figure 6 — optional performance evidence:** `netlogo_runtime_600s.svg` from the GitHub artifact; describe **ms per simulated tick on Ubuntu**, not rider delay. Use only as a supporting figure if space allows.

**Prioritize Figures 1–3.** For a 10–12-page paper, 3–5 strong figures usually communicate more clearly than many redundant charts. Do not duplicate long tables already represented by a chart without a specific reason.

## Methods details the professor can ask about

### DEVS atomic model — LaneBottleneck

Present `M = (X, S, Y, δint, δext, λ, ta)` with an explicit confluent policy `δcon`:

- **X:** arriving cyclist IDs and truck block/clear messages.
- **S:** blockage flag, waiting FIFO queue, current service, next completion time/remaining time, accounting counters.
- **Y:** completed-cyclist departure events.
- **δint:** complete the cyclist in service, update the queue, begin the next passage if clear.
- **δext:** apply elapsed time and incoming cyclists/control messages; queue arrivals or begin service when possible.
- **λ:** emit the departure before its associated internal state transition.
- **ta:** remaining service time while active; infinity when passive.
- **δcon:** resolve coincident completion and external messages by applying the documented completion/input policy.

For the exact behavior and ambiguous simultaneous event details, cite the corresponding [source design](devs_bottleneck_design.md) and Java implementation; never assume the framework's default ordering. **Coupled model:** explain port messages from generator and obstruction controller to the bottleneck and the coordinator's role in advancing event time.

### NetLogo ABM

Explain one rider per cyclist turtle, the single-lane grid, local movement, agent speed differences, stop/wait behavior near a blockage, conservation checks, and the 1-second tick. Emphasize **emergent queueing**: a queue forms when individual riders cannot pass the blocker; the model does not directly script a fixed queue result.

### Replicated experiment statistics

Four rates (150, 300, 600, 900/hour) × four durations (0, 30, 60, 120 s) × 10 seeds (101–110); obstruction begins t=45; horizon 600 s. The experiment records **160 paired records**, with baseline results reused within each rate/seed. For each condition, compute the blocked-minus-clear average waiting-count difference per seed and summarize it with a sample mean and individual t-based 95% interval using nine degrees of freedom.

Example result: at **900/h, 120 s**, mean queue difference `+3.368833`, interval `[2.939551, 3.798115]`; average paired peak-queue difference `+31.7`. These are model outcomes, **not extra seconds of waiting** or field measurements. The 16 intervals are not corrected for multiple comparisons.

## Presentation plan (~12 slides; adapt to the actual assigned time)

| Slide | Title | Visible content (one concise sentence per bullet) | Visual |
| ---: | --- | --- | --- |
| 1 | Cyclistics | Investigating simulated bicycle-lane obstructions with discrete-event and agent-based models | Actual NetLogo screenshot or clean title diagram |
| 2 | Real-world problem | A blocked bike lane forces arriving cyclists to slow or queue, especially during busy periods | Genuine illustrative photo only if rights/source permit |
| 3 | Research question | How do demand and obstruction duration affect simulated waiting queues? | 4×4 experiment matrix |
| 4 | System overview | Python DES, Java DEVS, and NetLogo are independently executed models with shared research questions | Architecture diagram |
| 5 | DEVS atomic/coupled design | A generator, obstruction controller, and lane bottleneck exchange events through ports | Atomic/coupled schematic |
| 6 | Event scheduling | In the shared verification case, cyclist departures occur at 14 s and 24 s | Time-sequence diagram |
| 7 | NetLogo ABM | Cyclist turtles follow local rules and form a queue at the truck | **Actual** model screenshot |
| 8 | Controlled experiments | Each blockage scenario is paired with an unobstructed run using matched random draws | Experiment-grid diagram |
| 9 | Main finding | Longer blockages and greater simulated demand increase the average waiting queue | **Primary 95% CI chart** |
| 10 | Peak queues | High-demand obstruction scenarios produce larger transient queue peaks | Secondary queue chart |
| 11 | Verification and limitations | Conservation, replay and a real coordinator fixture are verified, but NYC queue predictions are not field validated | Small checkmark-versus-limit table |
| 12 | Conclusion and future work | Cyclistics demonstrates controlled simulation methodology; real calibration and camera-linked events remain future work | Summary with 2–3 specific next steps |

**Speaker-note guidance:** explain *what the audience is seeing*, give one intuitive rider/truck example, connect it explicitly to Dr. Gu's terminology (atomic, coupled, event scheduling, ABM, global ticks, sensitivity, verification), and transition naturally to the next slide. Keep slide bullets short; put detailed reasoning in speaker notes.

## Pre-submission review

- [ ] Every chart label identifies whether the unit is **cyclists**, **simulated seconds**, or **wall-clock milliseconds**.
- [ ] All numerical results match the source CSV and manifest, not hand-entered estimates.
- [ ] External literature citations have been checked against actual full-text papers and bibliography entries.
- [ ] A screenshot of the running NetLogo model is included rather than a fabricated screenshot.
- [ ] The report explicitly states that Java/Python match **one deterministic fixture**, NetLogo is not numerically cross-validated with them, and NYC queues/crashes are not field-validated.
- [ ] No claim that Roboflow/ArcGIS or true live co-simulation is already operational.
- [ ] The codebase, Docker setup, NetLogo version, external JAR limitation, and generated output locations are explained.
- [ ] Paper, slides and demo are consistent with the professor's **current** format and submission requirements.

## What must still be supplied or checked

A final bibliography from peer-reviewed material (not yet audited in this repository), the original locally retained 3.8A NetLogo experimental output/figures, a suitable actual model screenshot, and professor-specific submission details. The paper/slide files themselves are not generated by this blueprint.
