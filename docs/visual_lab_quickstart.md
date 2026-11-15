# Event Inspector + Policy Lab (Python DES)

This is a visual replay of **real events from the Python discrete-event reference**. It does not run Java DEVS-Suite, NetLogo, computer vision, or a live NYC traffic feed inside the browser.

## Run on Windows with VS Code

First confirm that you're in this repository and you have no local work you would overwrite:

~~~powershell
git remote get-url origin
git status --short
git branch --show-current
git fetch origin
~~~

If the working tree is clean, use the feature branch:

~~~powershell
git switch --track origin/feat/devs-event-inspector-policy-lab
python -m pip install -e .
python -m unittest tests.test_visual_lab -v
python -m cyclistics.visual_lab --rate 900 --seed 754 --horizon 300 --blockage-start 45 --blockage-duration 120 --early-clearance-duration 30 --output outputs/visual_lab.json
python -m http.server 8000 --directory web
~~~

If you already created that local branch, use `git switch feat/devs-event-inspector-policy-lab` instead. Stop the local server with Ctrl+C. Open **http://localhost:8000/lab.html** and select `outputs/visual_lab.json` with **Import visual_lab.json**.

The export command is also available in the browser page, so you can change parameters and re-export without touching the frontend source. The `outputs/` directory is git-ignored; do not commit trace files as if they were measured observations.

## Try these experiments

1. Change `--blockage-duration` to 180 while keeping `--early-clearance-duration` at 30. Import the new JSON and compare mean wait and peak queue.
2. Use `--rate 300` and then `--rate 1200`. Observe how traffic demand changes queue formation.
3. In the event inspector, look for an obstruction start and an arrival at the same model timestamp. The Python heap prioritizes obstruction end, obstruction start, service completion, then arrival, with insertion order breaking identical-priority ties. Trace timestamps are rounded to 0.001 s for display; a printed collision does not always imply an exact-time tie.
4. Step through a blocked scenario and watch `arrived_so_far == completed_so_far + queue_waiting + in_service`. Every event must pass this conservation check.
5. Compare the three policies using the **same seeded arrival list**. This is a paired experimental design; independent random draws would obscure the effect of obstruction timing.

## What the viewer actually shows

- **Event log:** arrival, obstruction start/end, or service completion, in the order Python processed them
- **Post-event phase:** blocked (no *new* service), serving, or idle. A cyclist already being served can finish during a blockage.
- **Queue chart:** actual queue sizes emitted by the model at each event, not interpolated live observations
- **Policy comparison:** no obstruction, standard clearance, and earlier clearance, each under identical generated arrivals
- **Result metrics:** mean wait, departures by the arrival horizon, peak waiting queue, and total arrivals from the existing reference engine

The HTML reader validates the output schema and limits file size. It reads the chosen JSON locally and does not upload it to a server. Avoid importing unknown files you do not trust.

## How this relates to Dr. Gu's teaching

- **DES:** the system jumps from event to event rather than moving every cyclist at fixed wall-clock intervals.
- **Events and ordering:** simultaneous arrivals, completions, and obstruction changes are prioritized, making the event schedule observable and testable.
- **FSM/state transition idea:** blocked/serving/idle is a helpful *display label derived from the reference state*, not a claim of a complete formal DEVS atomic specification.
- **Experimental control:** use identical arrival draws to compare changes in clearance policy.
- **Verification:** event ordering and cyclist conservation are tested and displayed.
- **Validation boundary:** none of these queue/delay measures has been checked against independent real-world NYC obstruction observations.

## What would make this a true DEVSJAVA inspector?

The existing Java models must emit a versioned event/transition record directly from an executed DEVS-Suite coordinator, including model identity, input/output ports, phases, time advances and internal/external/confluent transitions. A separate adapter and tests would then map that log into a compatible viewer. The current Python output **must not** be renamed Java evidence.

## Next incremental features

- A tested Java coordinator event exporter and state inspector
- NetLogo trajectory replay (from actual model-generated CSV) in a lane-view canvas
- Real experiment configuration saved alongside trace hashes
- Optional coupled intersection controller with well-specified transitions
- Automated end-to-end browser playback verification
