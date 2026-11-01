$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$taskRuntime = Get-ReelMindRuntime
$taskPreviousRoot = $env:REELMIND_DATA_ROOT
$taskPreviousPassword = $env:PGPASSWORD
$taskPreviousUser = $env:PGUSER
try {
    $env:REELMIND_DATA_ROOT = Get-ReelMindDataRoot $taskRuntime
    # The short inference check uses the same global heavy reservation as the engine.
    $taskCredential = Import-Clixml -LiteralPath $taskRuntime.CredentialPath
    $env:PGPASSWORD = $taskCredential.GetNetworkCredential().Password
    $env:PGUSER = $taskCredential.UserName
    Push-Location (Join-Path $ReelMindRoot 'backend')
    try { & $taskRuntime.PythonPath -m app.prepare_av; if ($LASTEXITCODE) { throw 'Preparacion audiovisual fallida.' } }
    finally { Pop-Location }
} finally {
    $env:REELMIND_DATA_ROOT = $taskPreviousRoot
    $env:PGPASSWORD = $taskPreviousPassword
    $env:PGUSER = $taskPreviousUser
    $taskCredential = $null
}
