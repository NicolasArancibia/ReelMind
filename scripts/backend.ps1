[CmdletBinding()]
param([ValidateSet('Run', 'Migrate', 'Test', 'Check')][string]$Action = 'Run')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$runtime = Get-ReelMindRuntime
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot 'backend'
$pythonPath = $runtime.PythonPath
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Backend environment missing. Run scripts/setup.ps1 first.'
}
$previousPassword = $env:PGPASSWORD
$previousUser = $env:PGUSER
$commandExit = 1
try {
    if (-not $env:PGPASSWORD) {
        $credential = Import-Clixml -LiteralPath $runtime.CredentialPath
        $env:PGPASSWORD = $credential.GetNetworkCredential().Password
        $env:PGUSER = $credential.UserName
    }
    Push-Location -LiteralPath $backendDir
    try {
        switch ($Action) {
            'Run' { & $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000 }
            'Migrate' {
                $pgHostName = if ($env:PGHOST) { $env:PGHOST } else { '127.0.0.1' }
                if ($pgHostName -notin @('127.0.0.1', 'localhost', '::1')) { throw 'Only local database migrations are permitted.' }
                $pgPortNumber = if ($env:PGPORT) { $env:PGPORT } else { '5432' }
                $pgDatabaseName = if ($env:PGDATABASE) { $env:PGDATABASE } else { 'reelmind' }
                $pgUserName = if ($env:PGUSER) { $env:PGUSER } else { 'reelmind_app' }
                $runtimeRoot = Split-Path -Parent (Split-Path -Parent $runtime.CredentialPath)
                $backupDir = Join-Path $runtimeRoot 'backups'
                New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
                $backupPath = Join-Path $backupDir ('before-migration-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.dump')
                & (Join-Path $env:ProgramFiles 'PostgreSQL\18\bin\pg_dump.exe') -w -h $pgHostName -p $pgPortNumber -U $pgUserName -d $pgDatabaseName -Fc -f $backupPath
                if ($LASTEXITCODE -ne 0) { throw 'Database backup failed. No migration was applied.' }
                Write-Output ('Backup: ' + $backupPath)
                & $pythonPath -m alembic upgrade head
            }
            'Test' { & $pythonPath -m pytest }
            'Check' { & $pythonPath -m alembic check }
        }
        $commandExit = $LASTEXITCODE
    } finally { Pop-Location }
} finally {
    $env:PGPASSWORD = $previousPassword
    $env:PGUSER = $previousUser
    $credential = $null
}
exit $commandExit
