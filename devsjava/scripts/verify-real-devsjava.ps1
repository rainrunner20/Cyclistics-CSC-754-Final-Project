# Runs a compiler compatibility check in Docker, without a local Java install.
# Invoke from the Cyclistics repository root:
#   .\devsjava\scripts\verify-real-devsjava.ps1
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker was not found. Start Docker Desktop and try again.'
}
if (-not (Test-Path (Join-Path $repo 'devsjava\vendor'))) {
    throw 'Create devsjava/vendor and put the external course JAR(s) in it.'
}

# The Docker bind mount works with Windows paths containing spaces.
$mount = "type=bind,source=$repo,target=/workspace,readonly"
& docker run --rm --mount $mount --workdir /workspace eclipse-temurin:17-jdk-jammy bash devsjava/scripts/verify-real-devsjava.sh
if ($LASTEXITCODE -ne 0) {
    throw "DEVSJAVA compatibility check failed (exit code $LASTEXITCODE). See output above."
}
