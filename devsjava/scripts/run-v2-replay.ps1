# Run from repo-root PowerShell; requires a locally supplied DEVS-Suite JAR.
param(
    [string]$EventFile = 'netlogo/fixtures/v2_synthetic_obstruction.csv',
    [string]$Arrivals = '10,15',
    [string]$Headway = '4'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Start Docker Desktop before running the Java replay.'
}
if ([IO.Path]::IsPathRooted($EventFile) -or $EventFile.Contains('..')) {
    throw 'EventFile must be a path relative to the repository root.'
}
if (-not (Test-Path (Join-Path $repo $EventFile) -PathType Leaf)) {
    throw 'EventFile not found under repository root.'
}
$mount = "type=bind,source=$repo,target=/workspace,readonly"
& docker run --rm --mount $mount --workdir /workspace eclipse-temurin:17-jdk-jammy bash devsjava/scripts/run-v2-replay.sh $EventFile $Arrivals $Headway
if ($LASTEXITCODE -ne 0) {
    throw "DEVS-Suite offline replay failed (exit $LASTEXITCODE). See output above."
}
