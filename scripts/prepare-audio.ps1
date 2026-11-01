$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$runtime = Get-ReelMindRuntime
$previousDataRoot = $env:REELMIND_DATA_ROOT
try {
    if (-not $env:REELMIND_DATA_ROOT) { $env:REELMIND_DATA_ROOT = Get-ReelMindDataRoot $runtime }
    Push-Location -LiteralPath (Join-Path $ReelMindRoot 'backend')
    try {
        & $runtime.PythonPath -m app.prepare_audio
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar el modelo local.' }
    } finally { Pop-Location }
} finally { $env:REELMIND_DATA_ROOT = $previousDataRoot }
