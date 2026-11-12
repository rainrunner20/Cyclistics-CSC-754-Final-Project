;; Cyclistics - NetLogo ABM, milestone 3.1A
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
  pending-arrivals         ;; people waiting to enter if the spawn area is occupied
  departed-count           ;; cyclists that have exited the modeled lane
  total-completed-stop     ;; stop-ticks for riders who have exited only
  obstruction-active?      ;; whether a truck occupies the bottleneck
  queue-now                ;; fully stopped riders + pending entrants
  max-queue                ;; largest observed queue-now
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
  set pending-arrivals 0
  set departed-count 0
  set total-completed-stop 0
  set obstruction-active? false
  set queue-now 0
  set max-queue 0
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
  ask (sort-on [(- xcor)] cyclists) [ move-cyclist ]

  set queue-now (pending-arrivals + count (cyclists with [waiting?]))
  set max-queue (max (list max-queue queue-now))
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
        set free-speed (0.7 + random-float 0.6)
        set stop-ticks 0
        set waiting? false
      ]
      set pending-arrivals pending-arrivals - 1
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

  set waiting? (possible-step < 0.01)
  ifelse waiting? [
    set stop-ticks stop-ticks + 1
    set color yellow
  ] [
    set xcor xcor + possible-step
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
60
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

Cyclistics Milestone 3.1A is a small, visual agent-based bicycle-lane model for CSC 754. Each cyclist is an independent turtle that has an individual speed and follows the rider ahead. A delivery truck blocks the lane between configurable times. This is not a real-time digital twin or a measured NYC traffic model.

## HOW TO USE IT

1. Click **setup** and then **go**. One tick is one simulated second.
2. Blue bicycles are moving. Yellow bicycles are stopped. The red/orange truck is an obstruction.
3. Compare `blockage-enabled = 0` (clear lane) with `blockage-enabled = 1` using the same `seed-value`.
4. Observe the queue plot, peak queue, departure count, and completed-rider stop-time monitor.
5. Start with the defaults, then vary arrival-rate-per-hour, blockage-duration, and seed-value.

## HOW IT WORKS

**ABM (CSC 754):** Cyclists are turtles. The road is made of patches. Each cyclist observes the next cyclist ahead and moves at its personal desired speed unless following distance or an obstruction prevents that movement. Movement is processed from the most advanced cyclist backward.

**Discretization:** One `go` call is one second. Arrivals are Bernoulli trials with probability arrival-rate-per-hour / 3600 per tick. The random arrival draws are precomputed in `setup` so a clear and blocked run with the same seed and demand rate sees identical requested arrivals. Excess demand waits outside the lane when the entrance is occupied.

**Obstruction:** The truck occupies the marked lane region during the interval `[blockage-start, blockage-start + blockage-duration)`. Cyclists already beyond the stop line x = 5 can finish passing.

**Statistics:** `queue-now` counts riders currently *fully stopped* plus riders awaiting entrance. `mean-stop-completed` averages only whole stopped ticks for cyclists who have departed, not all travel delay and not censored in-progress waits. `max-queue` is the largest queue counted at the end of a tick. The conservation monitor checks `requested = departed + active + pending`.

## WHAT IT DOES NOT DO

This model is intentionally separate from the Java DEVS-Suite coordinator. It has one lane, a fixed obstruction location, no overtaking, no collisions, no CCTV computer vision, and no real-world trajectory data. Its continuous turtle position and one-second update rules differ from the Java single-server DEVS timing assumptions, so their statistics should not be claimed to match yet. This milestone is a visual prototype, not a validated prediction of cycling safety.

## FUTURE EXTENSIONS

Next: reproducible clear-vs-blocked comparisons, timestamped CSV exports, multiple behavior profiles, time-step convergence checks, sensitivity analysis, and explicit DEVS/NetLogo cross-model validation.
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
