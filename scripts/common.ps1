$ReelMindRoot = Split-Path -Parent $PSScriptRoot

function Get-ReelMindRuntime {
    $runtimeFile = Join-Path $ReelMindRoot '.local\runtime.json'
    if (Test-Path -LiteralPath $runtimeFile) {
        return Get-Content -LiteralPath $runtimeFile -Raw | ConvertFrom-Json
    }
    # Fallback for installations created before the runtime manifest was introduced.
    return [pscustomobject]@{
        PythonPath = (Join-Path $env:LOCALAPPDATA 'ReelMind\venvs\backend\Scripts\python.exe')
        CredentialPath = (Join-Path $env:LOCALAPPDATA 'ReelMind\secrets\postgres-app.xml')
        AdminCredentialPath = (Join-Path $env:LOCALAPPDATA 'ReelMind\secrets\postgres-admin.xml')
    }
}
