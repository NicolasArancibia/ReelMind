$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'backend.ps1') -Action PrepareAV
exit $LASTEXITCODE
