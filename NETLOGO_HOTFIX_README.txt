Cyclistics NetLogo 3.1A quick fix

Problem: sort-on returns a list of cyclists; NetLogo ask cannot process a list directly.
Fix: foreach the sorted list, then ask each cyclist in order.

Install from the repository root:
  Expand-Archive -LiteralPath "$HOME\Downloads\cyclistics-milestone-3-1a-netlogo-go-hotfix.zip" -DestinationPath . -Force

Close the open NetLogo model WITHOUT saving before extracting, then reopen the .nlogo file.
Click setup first; Go remains disabled until ticks are initialized.
Next click go.

Run structural checks:
  docker compose run --build --rm tests

This patch is not yet validated with the actual NetLogo desktop compiler.
