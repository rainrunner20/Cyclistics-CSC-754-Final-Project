#!/usr/bin/env bash
# Compile and execute the full model using ONLY the external DEVS-Suite JAR.
set -euo pipefail
cd /workspace
shopt -s nullglob
jars=(devsjava/vendor/*.jar)
if (( ${#jars[@]} == 0 )); then
  echo 'ERROR: put DEVS-Suite-2.1.0-20090428.jar in devsjava/vendor/ first.' >&2
  exit 2
fi
classpath="$(IFS=:; echo "${jars[*]}")"
classes="$(mktemp -d)"
trap 'rm -rf "$classes"' EXIT

# Never include devsjava/test_support: that is a separate fake API.
echo 'Compiling real production classes against DEVS-Suite...'
javac --release 17 -cp "$classpath" -d "$classes" devsjava/src/main/java/org/cyclistics/devs/*.java

echo 'Starting DEVS-Suite coordinator (headless)...'
java -Djava.awt.headless=true -cp "$classes:$classpath" org.cyclistics.devs.CyclisticsRunner
