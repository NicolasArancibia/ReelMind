[CmdletBinding()]
param(
    [switch]$Admin,
    [switch]$Check
)

# Opens psql using this Windows user's encrypted local credential.
# The password is never printed and is removed from the process environment on exit.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$runtime = Get-ReelMindRuntime
$psqlPath = Join-Path $env:ProgramFiles 'PostgreSQL\18\bin\psql.exe'
if (-not (Test-Path -LiteralPath $psqlPath)) {
    throw 'PostgreSQL 18 is not installed in the expected location. See docs/setup-windows.md.'
}
$databaseName = if ($Admin) { 'postgres' } else { 'reelmind' }
$credentialPath = if ($Admin) { $runtime.AdminCredentialPath } else { $runtime.CredentialPath }
if (-not (Test-Path -LiteralPath $credentialPath)) {
    throw 'Local encrypted credential not found. Complete PostgreSQL preparation first.'
}
$credential = Import-Clixml -LiteralPath $credentialPath
if ($credential -isnot [Management.Automation.PSCredential]) {
    throw 'The local credential is not a valid PSCredential.'
}
$previousPassword = $env:PGPASSWORD
$psqlExit = 1
try {
    $env:PGPASSWORD = $credential.GetNetworkCredential().Password
    $psqlArgs = @('-X', '-w', '-h', '127.0.0.1', '-p', '5432', '-U', $credential.UserName, '-d', $databaseName)
    if ($Check) {
        $psqlArgs += @('-v', 'ON_ERROR_STOP=1', '-c', 'SELECT current_user, current_database(), version();')
    }
    & $psqlPath @psqlArgs
    $psqlExit = $LASTEXITCODE
} finally {
    $env:PGPASSWORD = $previousPassword
    $credential = $null
}
exit $psqlExit
