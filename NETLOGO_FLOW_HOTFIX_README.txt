Cyclistics NetLogo 3.1A - flow deadlock bugfix

Symptom: 600-tick run completed with demand=107, departed=6 and queue=101.
Cause: positive steps shorter than 0.01 were discarded. An almost-finished cyclist could stall permanently.
Fix: apply every positive movement and only classify effectively zero movement as stopped.

Install on feat/netlogo-abm from the repository root:
  Expand-Archive -LiteralPath "$HOME\Downloads\cyclistics-milestone-3-1b-netlogo-flow-fix.zip" -DestinationPath . -Force

Close the open NetLogo model WITHOUT saving before extracting, then reopen .nlogo.
Run structural checks:
  docker compose run --build --rm tests
Then open NetLogo, click setup and go. Verify demand, departures, and queue.
If runtime works, stage the files and commit one fix.
