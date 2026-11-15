extensions [csv]

;; Cyclistics v2 experimental multi-lane model.
;; Time is measured in 1-second ticks. Distance is in schematic patches.
;; Neither this model nor its TTC proxy predicts observed NYC collisions.

breed [cyclists cyclist]
breed [cars car]
breed [trucks truck]

cyclists-own [free-speed stop-ticks waiting? merged?]
cars-own [driving-speed]

globals [
  requested-arrivals arrival-draws speed-draws admitted-count
  pending-arrivals departed-count total-completed-stop
  cars-requested cars-pending cars-departed cars-admitted
  car-arrival-draws car-speed-draws
  obstruction-active? replay-rows
  queue-now max-queue queue-area observed-blocked-ticks
  merge-events return-events potential-conflict-ticks minimum-ttc-s
  trajectory-rows
]

to-report bicycle-lane-color
  report green + 1
end

to paint-v2-street
  ask patches [
    ifelse pycor = 0 [
      set pcolor bicycle-lane-color
    ] [
      ifelse pycor = 1 [
        set pcolor white
      ] [
        ifelse pycor = 2 [
          set pcolor gray - 2
        ] [
          ifelse pycor > 2 [
            set pcolor gray - 1
            if pycor = 3 and (pxcor mod 5) < 3 [ set pcolor white ]
          ] [
            set pcolor gray + 3
          ]
        ]
      ]
    ]
  ]
end

to setup
  clear-all
  random-seed seed-value
  set-default-shape cyclists "bicycle"
  set-default-shape cars "car"
  set-default-shape trucks "truck"
  paint-v2-street

  set requested-arrivals 0
  set pending-arrivals 0
  set admitted-count 0
  set departed-count 0
  set total-completed-stop 0

  set cars-requested 0
  set cars-pending 0
  set cars-admitted 0
  set cars-departed 0

  ;; Pre-sample all demand and desired speeds. Every setup with the same
  ;; seed and parameters produces identical cyclist and car input draws.
  set arrival-draws (n-values run-length [ i -> random-float 1 ])
  set speed-draws (n-values run-length [ i -> (0.65 + random-float 0.65) ])
  set car-arrival-draws (n-values run-length [ i -> random-float 1 ])
  set car-speed-draws (n-values run-length [ i -> (1.1 + random-float 0.8) ])

  set obstruction-active? false
  set replay-rows []
  set queue-now 0
  set max-queue 0
  set queue-area 0
  set observed-blocked-ticks 0
  set merge-events 0
  set return-events 0
  set potential-conflict-ticks 0
  set minimum-ttc-s -1
  set trajectory-rows []
  reset-ticks
  update-obstruction
end

to go
  if ticks >= run-length [ stop ]
  update-obstruction
  if obstruction-active? [ set observed-blocked-ticks observed-blocked-ticks + 1 ]
  request-cyclist
  request-car
  admit-cyclist
  admit-car

  ;; Advance both lanes from front to back; a follower sees its leader's
  ;; updated x position and cannot pass through it.
  foreach (sort-on [(- xcor)] cars) [ driver -> ask driver [ move-car ] ]
  foreach (sort-on [(- xcor)] cyclists) [
    rider -> ask rider [ move-cyclist-v2 ]
  ]

  set queue-now (pending-arrivals + count (cyclists with [waiting?]))
  set max-queue (max (list max-queue queue-now))
  set queue-area (queue-area + queue-now)
  measure-conflict-proxies
  tick
  record-trajectories
  if not conservation-ok? [ error "V2 cyclist/car conservation failed" ]
  if not lane-spacing-ok? [ error "V2 lane spacing violation" ]
end

to update-obstruction
  let scheduled? (blockage-enabled = 1 and
    ticks >= blockage-start and
    ticks < (blockage-start + blockage-duration))
  ;; The optional validated CSV overrides the interface's synthetic truck schedule.
  if not empty? replay-rows [
    set scheduled? false
    foreach replay-rows [ item-row ->
      if (item 0 item-row) <= ticks [
        if (item 1 item-row) = "obstruction_start" [ set scheduled? true ]
        if (item 1 item-row) = "obstruction_end" [ set scheduled? false ]
      ]
    ]
  ]
  if scheduled? != obstruction-active? [
    set obstruction-active? scheduled?
    ifelse scheduled? [
      ask patches with [pycor = 0 and pxcor >= 6 and pxcor <= 7] [
        set pcolor orange
      ]
      create-trucks 1 [
        setxy 6.5 0
        set heading 90
        set size 2
        set color red
      ]
    ] [
      ask trucks [ die ]
      ask patches with [pycor = 0 and pxcor >= 6 and pxcor <= 7] [
        set pcolor bicycle-lane-color
      ]
    ]
  ]
end

to request-cyclist
  if (item ticks arrival-draws) < (arrival-rate-per-hour / 3600) [
    set requested-arrivals requested-arrivals + 1
    set pending-arrivals pending-arrivals + 1
  ]
end

to request-car
  if (item ticks car-arrival-draws) < (car-rate-per-hour / 3600) [
    set cars-requested cars-requested + 1
    set cars-pending cars-pending + 1
  ]
end

to admit-cyclist
  if pending-arrivals > 0 [
    if not any? (cyclists with [xcor < (min-pxcor + 1) and not merged?]) [
      create-cyclists 1 [
        setxy min-pxcor 0
        set heading 90
        set color blue
        set size 1.1
        set free-speed (item admitted-count speed-draws)
        set stop-ticks 0
        set waiting? false
        set merged? false
      ]
      set admitted-count admitted-count + 1
      set pending-arrivals pending-arrivals - 1
    ]
  ]
end

to admit-car
  if cars-pending > 0 [
    if not any? ((turtle-set cars (cyclists with [merged?])) with [
      ycor = 2 and xcor < (min-pxcor + 1.5)
    ]) [
      create-cars 1 [
        setxy min-pxcor 2
        set heading 90
        set color violet
        set size 1.25
        set driving-speed (item cars-admitted car-speed-draws)
      ]
      set cars-admitted cars-admitted + 1
      set cars-pending cars-pending - 1
    ]
  ]
end

to-report safe-lane-change? [target-row]
  ;; Gap acceptance is a model rule, not a validated human driver model.
  let others-on-target (turtle-set (other cyclists with [
    ycor = target-row
  ]) (cars with [ycor = target-row]))
  if any? (others-on-target with [
    abs (xcor - [xcor] of myself) < 3.0
  ]) [ report false ]
  report true
end

to maybe-change-lane
  ;; Cyclists attempt to bypass the blocked green lane using the car lane.
  if merging-enabled = 1 and obstruction-active? and not merged? and
     xcor >= 2 and xcor <= 5 and safe-lane-change? 2 [
    set ycor 2
    set merged? true
    set merge-events merge-events + 1
    set color cyan
  ]
  ;; Return to the green bike lane once past the obstruction and safe.
  if merged? and xcor >= 9 and safe-lane-change? 0 [
    set ycor 0
    set merged? false
    set return-events return-events + 1
  ]
end

to move-car
  let possible-step driving-speed
  let leaders ((turtle-set (other cars) (cyclists with [merged?])) with [
    ycor = 2 and xcor > [xcor] of myself
  ])
  if any? leaders [
    let ahead min-one-of leaders [xcor]
    set possible-step (min (list possible-step ([xcor] of ahead - xcor - 1.1)))
  ]
  set possible-step (max (list 0
    (min (list possible-step (max-pxcor - xcor)))))
  if possible-step > 0 [ set xcor xcor + possible-step ]
  if xcor >= (max-pxcor - 0.001) [
    set cars-departed cars-departed + 1
    die
  ]
end

to move-cyclist-v2
  maybe-change-lane
  let possible-step free-speed
  let leaders ((turtle-set (other cyclists) cars) with [
    ycor = [ycor] of myself and xcor > [xcor] of myself
  ])
  if any? leaders [
    let ahead min-one-of leaders [xcor]
    set possible-step (min (list possible-step ([xcor] of ahead - xcor - 1.1)))
  ]
  if obstruction-active? and not merged? and xcor <= 5 [
    set possible-step (min (list possible-step (5 - xcor)))
  ]
  set possible-step (max (list 0
    (min (list possible-step (max-pxcor - xcor)))))
  set waiting? (possible-step <= 0.000000001)
  if possible-step > 0 [ set xcor xcor + possible-step ]
  ifelse waiting? [
    set stop-ticks stop-ticks + 1
    set color yellow
  ] [
    ifelse merged? [ set color cyan ] [ set color blue ]
  ]
  if xcor >= (max-pxcor - 0.001) [
    set total-completed-stop total-completed-stop + stop-ticks
    set departed-count departed-count + 1
    die
  ]
end

to measure-conflict-proxies
  ;; Simplified closing-gap TTC between a car and a cyclist using the car
  ;; lane. Distances are patches and speeds patches per 1-second tick.
  ;; Do NOT interpret these proxy counts as observed crashes or near misses.
  foreach (sort-on [who] (cyclists with [merged?])) [ rider ->
    ask rider [
      let approaching (cars with [xcor < [xcor] of myself])
      if any? approaching [
        let car-behind max-one-of approaching [xcor]
        let gap (xcor - [xcor] of car-behind - 1.1)
        let closing-speed ([driving-speed] of car-behind - free-speed)
        if gap > 0 and closing-speed > 0 [
          let ttc (gap / closing-speed)
          if minimum-ttc-s < 0 or ttc < minimum-ttc-s [
            set minimum-ttc-s ttc
          ]
          if ttc < 3 [
            set potential-conflict-ticks potential-conflict-ticks + 1
          ]
        ]
      ]
    ]
  ]
end

to record-trajectories
  ;; Every row is simulated kinematics, not tracked real riders or cars.
  foreach (sort-on [who] cyclists) [ rider ->
    ask rider [
      set trajectory-rows (lput (list ticks "cyclist" who xcor ycor
        free-speed merged?) trajectory-rows)
    ]
  ]
  foreach (sort-on [who] cars) [ driver ->
    ask driver [
      set trajectory-rows (lput (list ticks "car" who xcor ycor
        driving-speed false) trajectory-rows)
    ]
  ]
end

to-report lane-spacing-ok?
  ;; Check both physical lanes after every tick. Distinct car/cyclist agent
  ;; types use the same longitudinal clearance invariant within a lane.
  foreach [0 2] [ road-lane ->
    let traffic (sort-on [xcor] (turtle-set
      (cars with [ycor = road-lane])
      (cyclists with [ycor = road-lane])))
    if (length traffic) > 1 [
      let previous first traffic
      foreach (but-first traffic) [ current ->
        if ([xcor] of current - [xcor] of previous) < 0.75 [
          report false
        ]
        set previous current
      ]
    ]
  ]
  report true
end

to-report conservation-ok?
  report (requested-arrivals =
    (pending-arrivals + departed-count + count cyclists)) and
    (cars-requested = (cars-pending + cars-departed + count cars))
end

to-report mean-queue
  if ticks = 0 [ report 0 ]
  report (queue-area / ticks)
end

to-report mean-stop-completed
  if departed-count = 0 [ report 0 ]
  report (total-completed-stop / departed-count)
end

to run-v2-verification
  ;; Run from a stopped go loop. Verify both agent populations survive load.
  setup
  repeat run-length [ go ]
  if not conservation-ok? [ error "V2 verification failed" ]
  if merge-events < return-events [ error "More returns than merges" ]
  if minimum-ttc-s < 0 and potential-conflict-ticks != 0 [
    error "Conflict proxy reported without a defined TTC"
  ]
  print (word "PASS: V2 tick, cyclist/car conservation, lane change accounting; "
    "requested cyclists=" requested-arrivals
    " requested cars=" cars-requested
    " merges=" merge-events " conflict-proxy-ticks=" potential-conflict-ticks)
end

to run-v2-experiment
  setup
  repeat run-length [ go ]
  if not conservation-ok? [ error "V2 experiment conservation failed" ]
  let header ["tick_s" "type" "agent_id" "x_patch" "lane_y"
              "desired_speed_patches_per_tick" "merged"]
  csv:to-file "../outputs/v2_trajectories.csv" (fput header trajectory-rows)
  csv:to-file "../outputs/v2_metrics.csv"
    (list ["seed" "bike_rate_per_hour" "car_rate_per_hour"
           "horizon_s" "cyclists_requested" "cyclists_departed"
           "cars_requested" "cars_departed" "peak_bike_queue"
           "mean_bike_queue" "merges" "returns" "potential_conflict_ticks"
           "minimum_model_ttc_s" "conservation_ok"]
      (list seed-value arrival-rate-per-hour car-rate-per-hour run-length
        requested-arrivals departed-count cars-requested cars-departed
        max-queue mean-queue merge-events return-events
        potential-conflict-ticks minimum-ttc-s conservation-ok?))
  print "PASS: wrote V2 trajectory and model-metrics CSV files."
end

to load-v2-event-replay [filename]
  let raw csv:from-file filename
  if length raw < 3 [ error "V2 replay needs a header plus paired events" ]
  if (first raw) != ["time_s" "event_type"] [
    error "V2 replay header must be time_s,event_type"
  ]
  set replay-rows but-first raw
  let previous -1
  let blocked? false
  foreach replay-rows [ entry ->
    if length entry != 2 [ error "V2 replay: invalid event row length" ]
    let t item 0 entry
    let kind item 1 entry
    if not is-number? t [ error "V2 replay: time must be numeric" ]
    if t != floor t or t < 0 or t < previous [
      error "V2 replay: time must be sorted, nonnegative whole seconds"
    ]
    if kind = "obstruction_start" [
      if blocked? [ error "V2 replay: overlapping starts" ]
      set blocked? true
    ]
    if kind = "obstruction_end" [
      if not blocked? or t = previous [
        error "V2 replay: unexpected end"
      ]
      set blocked? false
    ]
    if kind != "obstruction_start" and kind != "obstruction_end" [
      error "V2 replay: unknown event type"
    ]
    set previous t
  ]
  if blocked? [ error "V2 replay ends during a blockage" ]
end

to run-v2-replay [filename]
  setup
  load-v2-event-replay filename
  repeat run-length [ go ]
  if not conservation-ok? [ error "V2 replay conservation failed" ]
  print (word "PASS: replayed " (length replay-rows) " supplied event rows.")
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

SLIDER
10
355
242
389
car-rate-per-hour
car-rate-per-hour
0
1800
450.0
30
1
cars/hr
HORIZONTAL

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

SLIDER
10
447
242
481
merging-enabled
merging-enabled
0
1
1.0
1
1
0=wait 1=merge
HORIZONTAL

BUTTON
10
488
242
522
Verify mixed traffic
run-v2-verification
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
10
527
242
561
Run v2 experiment
run-v2-experiment
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

TEXTBOX
264
509
406
530
Moving (blue)
11
0.0
1

TEXTBOX
411
509
559
530
Stopped (yellow)
11
0.0
1

TEXTBOX
564
509
704
530
Truck (red)
11
0.0
1

TEXTBOX
709
509
929
530
Blocked zone (orange)
11
0.0
1

TEXTBOX
263
540
929
562
Experimental two-lane schematic — not field-validated traffic
10
0.0
1


MONITOR
261
568
435
613
Cars in lane
count cars
0
1
11

MONITOR
440
568
619
613
Cyclist merges
merge-events
0
1
11

MONITOR
625
568
929
613
Potential TTC proxy ticks
potential-conflict-ticks
0
1
11
@#$#@#$#@
## WHAT IS IT?

The green lane, asphalt, separator and sidewalk are a stylized NYC-inspired
illustration. Only the center row carries cyclists; surrounding patches have
no simulated vehicles or pedestrians. The road layout is not a measured NYC map.

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

car
false
0
Polygon -7500403 true true 40 120 75 70 210 70 255 120 260 180 40 180
Rectangle -16777216 true false 65 95 115 130
Circle -16777216 true false 70 175 48
Circle -16777216 true false 195 175 48

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
