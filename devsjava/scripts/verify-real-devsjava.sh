#!/usr/bin/env bash
# Check the actual external DEVSJAVA binary, not Cyclistics' test adapter.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
vendor_dir="$repo_root/devsjava/vendor"
source_dir="$repo_root/devsjava/src/main/java/org/cyclistics/devs"

shopt -s nullglob
jars=("$vendor_dir"/*.jar)
if (( ${#jars[@]} == 0 )); then
    echo "ERROR: No external DEVSJAVA JARs in devsjava/vendor/." >&2
    echo "Copy the course JAR(s) there first. See docs/devsjava_runtime_check.md." >&2
    exit 2
fi

# All imported framework classes must come from external JARs.
required=(
    'GenCol/entity.class'
    'model/modeling/message.class'
    'model/modeling/content.class'
    'view/modeling/ViewableAtomic.class'
    'model/simulation/coordinator.class'
)
missing=0
for class_name in "${required[@]}"; do
    found=0
    for jar_file in "${jars[@]}"; do
        if jar tf "$jar_file" | grep -Fx "$class_name" >/dev/null; then
            found=1
            break
        fi
    done
    if (( found )); then
        echo "FOUND external class: $class_name"
    else
        echo "MISSING external class: $class_name" >&2
        missing=1
    fi
done

if (( missing )); then
    echo "ERROR: This set of JARs does not expose the DEVS-Suite 2.1 classes our models expect." >&2
    echo "Confirm the library version and packages using jar tf/javap." >&2
    exit 3
fi

classpath="$(IFS=:; echo "${jars[*]}")"
classes_dir="$(mktemp -d)"
trap 'rm -rf "$classes_dir"' EXIT

# Deliberately compile ONLY production model sources. Never include test_support/
# here, because its ViewableAtomic is a local stand-in, not course DEVSJAVA.
sources=("$source_dir"/*.java)
if (( ${#sources[@]} == 0 )); then
    echo "ERROR: No Cyclistics atomic model sources found." >&2
    exit 4
fi

echo "Compiling ${#sources[@]} Cyclistics models against ${#jars[@]} external JAR(s)..."
javac -cp "$classpath" -d "$classes_dir" "${sources[@]}"
echo "PASS: Model source compiles against the provided external DEVSJAVA JAR(s)."
echo "NOT YET VERIFIED: runtime execution with a real DEVSJAVA coordinator."
