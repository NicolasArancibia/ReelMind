[CmdletBinding()]
param([ValidateSet('Backup','RestoreVerify')][string]$Action='Backup',[string]$Bundle)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$taskRuntime=Get-ReelMindRuntime
$taskPrevious=@{}
foreach($taskName in @('PGUSER','PGPASSWORD','REELMIND_DATA_ROOT','REELMIND_ADMIN_USER','REELMIND_ADMIN_PASSWORD')) {
    $taskPrevious[$taskName]=[Environment]::GetEnvironmentVariable($taskName,'Process')
}
try {
    $taskCredential=Import-Clixml -LiteralPath $taskRuntime.CredentialPath
    $env:PGUSER=$taskCredential.UserName
    $env:PGPASSWORD=$taskCredential.GetNetworkCredential().Password
    $env:REELMIND_DATA_ROOT=Get-ReelMindDataRoot $taskRuntime
    $taskArguments=@('-m','app.maintenance','backup')
    if($Action -eq 'RestoreVerify') {
        if(-not $Bundle){throw 'Bundle es obligatorio; no se restaura sobre una base existente.'}
        $taskAdminCredential=Import-Clixml -LiteralPath $taskRuntime.AdminCredentialPath
        $env:REELMIND_ADMIN_USER=$taskAdminCredential.UserName
        $env:REELMIND_ADMIN_PASSWORD=$taskAdminCredential.GetNetworkCredential().Password
        $taskArguments=@('-m','app.maintenance','restore-verify','--bundle',$Bundle)
    }
    Push-Location -LiteralPath (Join-Path $ReelMindRoot 'backend')
    try { & $taskRuntime.PythonPath @taskArguments; $taskExit=$LASTEXITCODE } finally {Pop-Location}
} finally {
    foreach($taskName in $taskPrevious.Keys){[Environment]::SetEnvironmentVariable($taskName,$taskPrevious[$taskName],'Process')}
    $taskCredential=$null; $taskAdminCredential=$null
}
exit $taskExit
