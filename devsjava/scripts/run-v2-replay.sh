#!/usr/bin/env bash
# Run actual external DEVS-Suite classes on an explicitly supplied offline CSV.
set -euo pipefail
cd /workspace

if (( $# != 3 )); then
  echo 'Usage: run-v2-replay.sh relative-events.csv 10,15 4' >&2
  exit 2
fi
events="$1"
arrivals="$2"
headway="$3"
if [[ "$events" == /* || "$events" == *".."* || ! -f "$events" ]]; then
  echo 'ERROR: supply a valid repo-relative CSV path.' >&2
  exit 2
fi
set -- devsjava/vendor/*.jar
if [[ ! -f "$1" ]]; then
  echo 'ERROR: place a compatible external DEVS-Suite JAR in devsjava/vendor/.' >&2
  exit 2
fi
classpath="$(IFS=:; echo "$*")"
classes="$(mktemp -d)"
trap 'rm -rf "$classes"' EXIT

# Only genuine production classes compile against the separately obtained JAR.
javac --release 17 -cp "$classpath" -d "$classes" devsjava/src/main/java/org/cyclistics/devs/*.java
java -Djava.awt.headless=true -cp "$classes:$classpath" \
  org.cyclistics.devs.CyclisticsReplayRunner "$events" "$arrivals" "$headway"
