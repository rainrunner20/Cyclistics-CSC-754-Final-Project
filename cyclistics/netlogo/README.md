# NetLogo agent model — planned next phase

NetLogo's `csv` extension can load `outputs/netlogo_events_*.csv` using `csv:from-file`. The exported files have columns `time_s,event_type,value`; ignore the header.

Agents: cyclist turtles with desired speed and pass/wait preference. Spatial grid: patches forming a bike lane and a conceptual adjacent lane. Basic rules: spawn at arrival times, move at desired speed, respond to obstruction, keep safe spacing, optionally enter adjacent lane, measure delays and merge exposure.

Map an integer `tick` to **one simulated second** and explicitly define how fractional-second event times are rounded. Use BehaviorSpace to repeat scenarios with varying demand, blockage duration, and rider behavior. Do not claim a fully integrated real-time digital twin or actual crash prediction unless implemented and validated.
