$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'backend.ps1') -Action PrepareAudio
exit $LASTEXITCODE
