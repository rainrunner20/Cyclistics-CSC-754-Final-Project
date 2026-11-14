# Run from repository root: .\devsjava\scripts\run-real-coupled.ps1
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Start Docker Desktop before running this script.'
}
$mount = "type=bind,source=$repo,target=/workspace,readonly"
& docker run --rm --mount $mount --workdir /workspace eclipse-temurin:17-jdk-jammy bash devsjava/scripts/run-real-coupled.sh
if ($LASTEXITCODE -ne 0) {
    throw "Coupled DEVS-Suite run failed (exit code $LASTEXITCODE). See output above."
}
