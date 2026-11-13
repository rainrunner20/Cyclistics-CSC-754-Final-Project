extensions [csv]

;; Cyclistics - NetLogo ABM, milestone 3.2B: sensitivity experiments
;; One tick = one simulated second. One patch ~ one unit of lane distance.
;; This is an independent agent-based prototype, NOT a live DEVS co-simulation.
;; No real observed cyclist trajectories or crash-risk predictions are used.

breed [cyclists cyclist]
breed [trucks truck]

cyclists-own [
  free-speed               ;; patches per tick: each rider has an individual speed
  stop-ticks               ;; whole seconds spent completely stopped
  waiting?                 ;; changed every tick by that rider's local rule
]

globals [
  requested-arrivals       ;; stochastic cyclist demand created so far
  arrival-draws            ;; fixed, seeded Bernoulli draws for fair scenarios
  speed-draws              ;; fixed per-arrival speeds so comparisons are paired
  admitted-count           ;; number of cyclists assigned speeds so far
  pending-arrivals         ;; people waiting to enter if the spawn area is occupied
  departed-count           ;; cyclists that have exited the modeled lane
  total-completed-stop     ;; stop-ticks for riders who have exited only
  obstruction-active?      ;; whether a truck occupies the bottleneck
  queue-now                ;; fully stopped riders + pending entrants
  max-queue                ;; largest observed queue-now
  queue-area               ;; sum of per-tick queue lengths (rider-seconds)
]

to setup
  clear-all
  random-seed seed-value
  set-default-shape cyclists "bicycle"
  set-default-shape trucks "truck"
  ask patches [
    ifelse pycor = 0
      [ set pcolor sky ]
      [ ifelse abs pycor = 1
          [ set pcolor gray + 2 ]
          [ set pcolor gray - 1 ] ]
  ]
  set requested-arrivals 0
  ;; Pre-sample arrivals before any riders or trucks are created. Otherwise
  ;; truck creation or different queue lengths can change the RNG sequence.
  ;; Fixed seed + fixed input rate => identical demand in clear/blocked runs.
  set arrival-draws (n-values run-length [ i -> random-float 1 ])
  ;; Match each requested cyclist's desired speed across control/treatment.
  ;; Draw speeds before any scenario-specific truck creation or queue delays.
  set speed-draws (n-values run-length [ i -> (0.7 + random-float 0.6) ])
  set admitted-count 0
  set pending-arrivals 0
  set departed-count 0
  set total-completed-stop 0
  set obstruction-active? false
  set queue-now 0
  set max-queue 0
  set queue-area 0
  reset-ticks
  update-obstruction
end

to go
  if ticks >= run-length [ stop ]
  update-obstruction
  request-arrival
  admit-pending-cyclist

  ;; Front-to-back order lets each follower observe the updated front rider.
  ;; This keeps riders from passing each other in our single-lane model.
  foreach (sort-on [(- xcor)] cyclists) [ rider ->
    ask rider [ move-cyclist ]
  ]

  set queue-now (pending-arrivals + count (cyclists with [waiting?]))
  set max-queue (max (list max-queue queue-now))
  set queue-area (queue-area + queue-now)
  tick
end

to update-obstruction
  let scheduled? (blockage-enabled = 1 and
    ticks >= blockage-start and
    ticks < (blockage-start + blockage-duration))
  if scheduled? != obstruction-active? [
    set obstruction-active? scheduled?
    ifelse obstruction-active? [
      ask patches with [pycor = 0 and pxcor >= 6 and pxcor <= 7] [
        set pcolor orange
      ]
      create-trucks 1 [
        setxy 6.5 0
        set size 2
        set heading 90
        set color red
      ]
    ] [
      ask trucks [ die ]
      ask patches with [pycor = 0 and pxcor >= 6 and pxcor <= 7] [
        set pcolor sky
      ]
    ]
  ]
end

to request-arrival
  ;; Bernoulli demand: expected arrivals per tick = cyclists/hour / 3600.
  ;; This is synthetic traffic, even if a later experiment picks a NYC-based rate.
  if (item ticks arrival-draws) < (arrival-rate-per-hour / 3600) [
    set requested-arrivals requested-arrivals + 1
    set pending-arrivals pending-arrivals + 1
  ]
end

to admit-pending-cyclist
  if pending-arrivals > 0 [
    ;; Don't draw two cyclists on top of one another at the western entrance.
    if not any? (cyclists with [xcor < (min-pxcor + 1)]) [
      create-cyclists 1 [
        setxy min-pxcor 0
        set heading 90
        set color blue
        set size 1.2
        set free-speed (item admitted-count speed-draws)
        set stop-ticks 0
        set waiting? false
      ]
      set pending-arrivals pending-arrivals - 1
      set admitted-count admitted-count + 1
    ]
  ]
end

to move-cyclist  ;; cyclist context only
  let possible-step free-speed

  ;; A rider checks the nearest rider in front (a simple local interaction).
  let rider-ahead min-one-of (other cyclists with [
    xcor > [xcor] of myself
  ]) [ xcor ]
  if rider-ahead != nobody [
    set possible-step (min (list possible-step
      ([xcor] of rider-ahead - xcor - 0.85)))
  ]

  ;; A truck prevents NEW riders entering x > 5. Riders who passed the
  ;; stop line before it arrived may finish, as in our DEVS example.
  if obstruction-active? and xcor <= 5 [
    set possible-step (min (list possible-step (5 - xcor)))
  ]

  ;; Never travel beyond the model's non-wrapping eastern edge.
  set possible-step (max (list 0
    (min (list possible-step (max-pxcor - xcor)))))

  ;; Always apply any positive motion, even the final small step to the exit.
  ;; Otherwise a rider within 0.01 patches of the exit can become stuck
  ;; forever and create a permanent queue behind them.
  set waiting? (possible-step <= 0.000000001)
  if possible-step > 0 [
    set xcor xcor + possible-step
  ]
  ifelse waiting? [
    set stop-ticks stop-ticks + 1
    set color yellow
  ] [
    set color blue
  ]

  if xcor >= (max-pxcor - 0.001) [
    set total-completed-stop total-completed-stop + stop-ticks
    set departed-count departed-count + 1
    die
  ]
end

to-report mean-stop-completed
  if departed-count = 0 [ report 0 ]
  report (total-completed-stop / departed-count)
end

to-report conservation-ok?
  ;; This identity should hold every tick, including with an entrance backlog.
  report requested-arrivals = (pending-arrivals + count cyclists + departed-count)
end

to run-headless-scenario
  setup
  repeat run-length [ go ]
  show (word "requested=" requested-arrivals
    " departed=" departed-count
    " active=" count cyclists
    " pending=" pending-arrivals
    " peak-queue=" max-queue
    " mean-stop-completed=" (precision mean-stop-completed 3))
  if not conservation-ok? [ error "Cyclist conservation failed" ]
end

;; ================================================================
;; Controlled experiment: same stochastic demand AND cyclist speeds.
;; NetLogo's model directory is the default base for relative files.
;; This model assumes the repo contains ../outputs/ (already gitignored).
;; ================================================================

to-report mean-queue
  if ticks = 0 [ report 0 ]
  report (queue-area / ticks)
end

to-report experiment-row [scenario-label]
  report (list scenario-label blockage-enabled seed-value
    arrival-rate-per-hour blockage-start blockage-duration run-length
    requested-arrivals departed-count (count cyclists) pending-arrivals
    max-queue (precision mean-queue 3)
    (precision mean-stop-completed 3) conservation-ok?)
end

to run-paired-experiment
  ;; Run only when the forever "go" button is stopped.
  ;; Resetting via setup gives each scenario the same initial conditions.
  let original-blockage blockage-enabled

  set blockage-enabled 0
  setup
  repeat run-length [ go ]
  if not conservation-ok? [ error "Clear-lane conservation failed" ]
  let clear-row (experiment-row "clear")
  let original-arrivals arrival-draws
  let original-speeds speed-draws

  set blockage-enabled 1
  setup
  repeat run-length [ go ]
  if not conservation-ok? [ error "Blocked-lane conservation failed" ]
  let blocked-row (experiment-row "blocked")

  ;; Check the actual sampled inputs, not only the seed value.
  if arrival-draws != original-arrivals [
    error "Paired experiment failed: arrival schedules differ"
  ]
  if speed-draws != original-speeds [
    error "Paired experiment failed: individual desired speeds differ"
  ]
  if (item 7 clear-row) != (item 7 blocked-row) [
    error "Paired experiment failed: requested cyclist counts differ"
  ]

  ;; Restore the user's slider setting; leave the blocked result displayed.
  set blockage-enabled original-blockage
  let columns ["scenario" "blockage_enabled" "seed" "arrival_rate_per_hour"
    "blockage_start_s" "blockage_duration_s" "run_length_s"
    "requested" "departed" "on_lane" "pending" "peak_queue"
    "mean_queue" "mean_stop_completed_s" "conservation_ok"]
  csv:to-file "../outputs/netlogo_paired_results.csv"
    (list columns clear-row blocked-row)

  print "Cyclistics paired experiment: identical arrival and desired-speed draws"
  print (word "CLEAR   demand=" (item 7 clear-row)
    " departed=" (item 8 clear-row)
    " peak-queue=" (item 11 clear-row)
    " mean-queue=" (item 12 clear-row)
    " mean-stop-completed=" (item 13 clear-row))
  print (word "BLOCKED demand=" (item 7 blocked-row)
    " departed=" (item 8 blocked-row)
    " peak-queue=" (item 11 blocked-row)
    " mean-queue=" (item 12 blocked-row)
    " mean-stop-completed=" (item 13 blocked-row))
  print "CSV saved: ../outputs/netlogo_paired_results.csv"
end

;; =====================================================================
;; Sensitivity study: 4 demand rates x 4 durations x 10 random seeds.
;; Each (rate, seed) baseline is computed once and reused for 4 paired
;; comparisons, including the exact no-blockage control (duration 0).
;; 40 clear baselines + 120 obstructed runs = 160 simulated scenarios.
;; Source data stay fully synthetic. Results are not field calibration.
;; =====================================================================

to run-sensitivity-study
  ;; This one-shot procedure must run while the forever "go" button is off.
  ;; Match demands and individual desired speeds per seed / arrival rate.
  let rates [150 300 600 900]
  let durations [0 30 60 120]
  let seeds [101 102 103 104 105 106 107 108 109 110]
  let original-rate arrival-rate-per-hour
  let original-blockage blockage-enabled
  let original-start blockage-start
  let original-duration blockage-duration
  let original-seed seed-value
  let original-length run-length
  let rows []

  no-display
  set blockage-start 45
  set run-length 600

  foreach rates [ rate ->
    foreach seeds [ seed-number ->
      set arrival-rate-per-hour rate
      set seed-value seed-number
      set blockage-enabled 0
      set blockage-duration 0
      setup
      repeat run-length [ go ]
      if not conservation-ok? [ error "Sensitivity baseline violated cyclist conservation" ]

      ;; Save the reference outputs and full underlying random draws.
      let base-arrivals arrival-draws
      let base-speeds speed-draws
      let base-requested requested-arrivals
      let base-departed departed-count
      let base-peak max-queue
      let base-mean-queue mean-queue
      let base-mean-stop mean-stop-completed
      let base-remaining (pending-arrivals + count cyclists)

      foreach durations [ duration ->
        set blockage-duration duration
        set blockage-enabled (ifelse-value (duration = 0) [0] [1])
        setup
        repeat run-length [ go ]
        if not conservation-ok? [ error "Sensitivity run violated cyclist conservation" ]
        if arrival-draws != base-arrivals [
          error "Sensitivity run did not preserve the sampled arrival schedule"
        ]
        if speed-draws != base-speeds [
          error "Sensitivity run did not preserve the cyclist desired speeds"
        ]
        if requested-arrivals != base-requested [
          error "Sensitivity run did not preserve requested cyclist demand"
        ]

        let treatment-mean-queue mean-queue
        let treatment-mean-stop mean-stop-completed
        let treatment-remaining (pending-arrivals + count cyclists)
        if duration = 0 [
          ;; Zero blockage must exactly reproduce the control scenario.
          if (departed-count != base-departed or
              max-queue != base-peak or
              treatment-mean-queue != base-mean-queue or
              treatment-mean-stop != base-mean-stop or
              treatment-remaining != base-remaining) [
            error "Zero-duration control differs from its baseline"
          ]
        ]

        ;; One paired row per (rate, duration, seed).
        ;; Deltas are treatment MINUS clear; do not round before analysis.
        let row (list rate duration seed-number blockage-start run-length
          requested-arrivals
          base-departed departed-count (departed-count - base-departed)
          base-peak max-queue (max-queue - base-peak)
          base-mean-queue treatment-mean-queue
          (treatment-mean-queue - base-mean-queue)
          base-mean-stop treatment-mean-stop
          (treatment-mean-stop - base-mean-stop)
          base-remaining treatment-remaining
          conservation-ok? true)
        set rows (lput row rows)
      ]
      print (word "Finished sensitivity runs: rate=" rate
        "/hr seed=" seed-number " (4 paired durations)")
    ]
  ]

  ;; Restore every changed interface parameter. Reset the model to match.
  set arrival-rate-per-hour original-rate
  set blockage-enabled original-blockage
  set blockage-start original-start
  set blockage-duration original-duration
  set seed-value original-seed
  set run-length original-length
  setup
  display

  let columns ["arrival_rate_per_hour" "blockage_duration_s" "seed"
    "blockage_start_s" "run_length_s" "requested"
    "clear_departed" "blocked_departed" "delta_departed"
    "clear_peak_queue" "blocked_peak_queue" "delta_peak_queue"
    "clear_mean_queue" "blocked_mean_queue" "delta_mean_queue"
    "clear_mean_stop_completed_s" "blocked_mean_stop_completed_s"
    "delta_mean_stop_completed_s" "clear_remaining" "blocked_remaining"
    "conservation_ok" "paired_inputs_ok"]
  csv:to-file "../outputs/netlogo_sensitivity_raw.csv"
    (fput columns rows)
  print (word "PASS: wrote " (length rows)
    " paired sensitivity rows to ../outputs/netlogo_sensitivity_raw.csv")
  print "Use the Python analysis command to calculate means and 95% intervals."
end
@#$#@#$#@
GRAPHICS-WINDOW
261
10
929
198
-1
-1
20.0
1
10
1
1
1
0
0
0
1
-16
16
-4
4
1
1
1
ticks
30.0

BUTTON
10
12
123
48
setup
setup
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
128
12
242
48
go
go
T
1
T
OBSERVER
NIL
NIL
NIL
NIL
0

SLIDER
10
59
242
92
arrival-rate-per-hour
arrival-rate-per-hour
0
1800
600.0
30
1
cyclists/hr
HORIZONTAL

SLIDER
10
98
242
131
blockage-enabled
blockage-enabled
0
1
1.0
1
1
0=off 1=on
HORIZONTAL

SLIDER
10
137
242
170
blockage-start
blockage-start
0
200
45.0
5
1
seconds
HORIZONTAL

SLIDER
10
176
242
209
blockage-duration
blockage-duration
0
200
65.0
5
1
seconds
HORIZONTAL

SLIDER
10
215
242
248
seed-value
seed-value
0
9999
754.0
1
1
NIL
HORIZONTAL

SLIDER
10
254
242
287
run-length
run-length
100
1800
600.0
100
1
seconds
HORIZONTAL

MONITOR
260
217
361
262
Demand
requested-arrivals
0
1
11

MONITOR
366
217
467
262
On lane
count cyclists
0
1
11

MONITOR
472
217
573
262
Queued
queue-now
0
1
11

MONITOR
578
217
680
262
Departed
departed-count
0
1
11

MONITOR
685
217
786
262
Peak queue
max-queue
0
1
11

MONITOR
791
217
929
262
Mean stop (s)
mean-stop-completed
2
1
11

MONITOR
10
299
242
347
Conservation check
conservation-ok?
0
1
11

BUTTON
10
355
242
389
Compare clear vs blocked
run-paired-experiment
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

MONITOR
10
396
242
441
Mean queue (riders)
mean-queue
2
1
11

BUTTON
10
447
242
481
Run sensitivity study
run-sensitivity-study
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

PLOT
260
281
929
494
Queue length over time
Time (seconds)
Cyclists waiting / entering
0.0
600.0
0.0
10.0
true
false
"" ""
PENS
"queue" 1.0 0 -2674135 true "" "plot queue-now"
@#$#@#$#@
## WHAT IS IT?

Cyclistics Milestone 3.2A is a small, visual agent-based bicycle-lane model for CSC 754. Each cyclist is an independent turtle that has an individual speed and follows the rider ahead. A delivery truck blocks the lane between configurable times. This is not a real-time digital twin or a measured NYC traffic model.

## HOW TO USE IT

1. Click **setup** and then **go**. One tick is one simulated second.
2. Blue bicycles are moving. Yellow bicycles are stopped. The red/orange truck is an obstruction.
3. Compare `blockage-enabled = 0` (clear lane) with `blockage-enabled = 1` using the same `seed-value`.
4. Observe the queue plot, peak queue, departure count, and completed-rider stop-time monitor.
5. Stop the forever **go** button, click **Compare clear vs blocked** to run an A/B experiment automatically, or type `run-paired-experiment` in the Command Center. Results are exported as CSV to the repository's `outputs/netlogo_paired_results.csv` (relative to the `netlogo/` model directory).
6. Re-run with different `seed-value` and arrival rate to assess sensitivity.

## HOW IT WORKS

**ABM (CSC 754):** Cyclists are turtles. The road is made of patches. Each cyclist observes the next cyclist ahead and moves at its personal desired speed unless following distance or an obstruction prevents that movement. Movement is processed from the most advanced cyclist backward.

**Discretization:** One `go` call is one second. Arrivals are Bernoulli trials with probability arrival-rate-per-hour / 3600 per tick. The random arrival draws are precomputed in `setup` so a clear and blocked run with the same seed and demand rate sees identical requested arrivals and the same pre-sampled desired speeds for each cyclist. Excess demand waits outside the lane when the entrance is occupied.

**Obstruction:** The truck occupies the marked lane region during the interval `[blockage-start, blockage-start + blockage-duration)`. Cyclists already beyond the stop line x = 5 can finish passing.

**Statistics:** `queue-now` counts riders currently *fully stopped* plus riders awaiting entrance. `mean-stop-completed` averages only whole stopped ticks for cyclists who have departed, not all travel delay and not censored in-progress waits. `max-queue` is the largest queue counted at the end of a tick. `mean-queue` is the average of end-of-tick queue counts across the simulated horizon (pending entrants + fully stopped cyclists). The conservation monitor checks `requested = departed + active + pending`.

## WHAT IT DOES NOT DO

This model is intentionally separate from the Java DEVS-Suite coordinator. It has one lane, a fixed obstruction location, no overtaking, no collisions, no CCTV computer vision, and no real-world trajectory data. Its continuous turtle position and one-second update rules differ from the Java single-server DEVS timing assumptions, so their statistics should not be claimed to match yet. This milestone is a visual prototype, not a validated prediction of cycling safety.

## FUTURE EXTENSIONS

Next: replicated experiments across multiple seeds, additional rider behavior profiles, time-step convergence, and careful DEVS/NetLogo comparisons under harmonized assumptions. This first two-row CSV is an internal paired comparison, not field validation.
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

bicycle
false
0
Circle -7500403 false true 23 164 105
Circle -7500403 false true 173 164 105
Line -7500403 true 75 218 142 133
Line -7500403 true 142 133 225 217
Line -7500403 true 225 217 75 217
Line -7500403 true 75 217 169 215
Line -7500403 true 169 215 142 133
Line -7500403 true 126 126 157 126
Line -7500403 true 217 216 214 118
Line -7500403 true 214 118 252 118

truck
false
0
Rectangle -7500403 true true 20 110 197 210
Polygon -7500403 true true 197 130 254 130 283 167 283 210 197 210
Rectangle -16777216 true false 212 137 249 163
Circle -16777216 true false 57 193 53
Circle -16777216 true false 205 193 53
Circle -7500403 true true 67 203 33
Circle -7500403 true true 215 203 33
@#$#@#$#@
NetLogo 6.3.0
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180
@#$#@#$#@
0
@#$#@#$#@
