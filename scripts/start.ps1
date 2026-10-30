[CmdletBinding()]
param([switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$runtime = Get-ReelMindRuntime
$localDir = Join-Path $ReelMindRoot '.local'
$processFile = Join-Path $localDir 'processes.json'
$url = 'http://127.0.0.1:5180'
New-Item -ItemType Directory -Path $localDir -Force | Out-Null

if (Test-Path -LiteralPath $processFile) {
    $existing = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
    if ($existing.Root -ne $ReelMindRoot) { throw 'The process record belongs to another project. Nothing changed.' }
    $alive = @($existing.Processes | Where-Object {
        $process = Get-Process -Id $_.Id -ErrorAction SilentlyContinue
        $process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $_.StartedTicks
    })
    if ($alive.Count -gt 0) {
        if ($alive.Count -ne 2) { throw 'ReelMind is partially running. Use Detener ReelMind, then start again.' }
        $health = Invoke-RestMethod -Uri ($url + '/api/health') -TimeoutSec 5
        if ($health.status -ne 'ok') { throw 'ReelMind is not ready. Review .local logs.' }
        Write-Output ('ReelMind ya esta abierto: ' + $url)
        if ($OpenBrowser) { Start-Process $url }
        return
    }
}

foreach ($portNumber in @(8000, 5180)) {
    if (@(Get-NetTCPConnection -State Listen -LocalPort $portNumber -ErrorAction SilentlyContinue).Count -gt 0) {
        throw "Port $portNumber is occupied. No existing process was stopped."
    }
}
if (-not (Test-Path -LiteralPath $runtime.PythonPath)) { throw 'Run scripts/setup.ps1 first.' }
$vitePath = Join-Path $ReelMindRoot 'frontend\node_modules\vite\bin\vite.js'
if (-not (Test-Path -LiteralPath $vitePath)) { throw 'Run scripts/setup.ps1 first.' }
if (-not (Test-Path -LiteralPath (Join-Path $ReelMindRoot 'frontend\dist\index.html'))) { throw 'Frontend build missing. Run npm.cmd run build in frontend.' }
$records = @()
$previousPassword = $env:PGPASSWORD
$previousUser = $env:PGUSER
$previousDataRoot = $env:REELMIND_DATA_ROOT
try {
    if (-not $env:REELMIND_DATA_ROOT) { $env:REELMIND_DATA_ROOT = Get-ReelMindDataRoot $runtime }
    $credential = Import-Clixml -LiteralPath $runtime.CredentialPath
    $env:PGPASSWORD = $credential.GetNetworkCredential().Password
    $env:PGUSER = $credential.UserName
    $backendArgs = '-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir "' + (Join-Path $ReelMindRoot 'backend') + '"'
    $backend = Start-Process -FilePath $runtime.PythonPath -ArgumentList $backendArgs -WorkingDirectory $ReelMindRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $localDir 'api.log') -RedirectStandardError (Join-Path $localDir 'api-error.log')
    $records += [pscustomobject]@{ Id=$backend.Id; StartedTicks=$backend.StartTime.ToUniversalTime().Ticks.ToString(); Kind='api' }
    # Frontend must not inherit database credentials.
    $env:PGPASSWORD = $null
    $env:PGUSER = $null
    $nodePath = (Get-Command node.exe -ErrorAction Stop).Source
    $frontendArgs = '"' + $vitePath + '" preview --host 127.0.0.1 --port 5180 --strictPort'
    $frontend = Start-Process -FilePath $nodePath -ArgumentList $frontendArgs -WorkingDirectory (Join-Path $ReelMindRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $localDir 'frontend.log') -RedirectStandardError (Join-Path $localDir 'frontend-error.log')
    $records += [pscustomobject]@{ Id=$frontend.Id; StartedTicks=$frontend.StartTime.ToUniversalTime().Ticks.ToString(); Kind='frontend' }
    [pscustomobject]@{ Root=$ReelMindRoot; Processes=$records } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $processFile -Encoding UTF8
    $ready = $false
    for ($attempt = 0; $attempt -lt 25; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri ($url + '/api/health') -TimeoutSec 2
            if ($health.status -eq 'ok') { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) { throw 'ReelMind could not start. Check .local logs; apply migrations if missing.' }
    Write-Output ('ReelMind listo: ' + $url)
    Write-Output 'Analisis detenido. Cerrar el navegador no detiene los servicios; usa Detener ReelMind.'
    if ($OpenBrowser) { Start-Process $url }
} catch {
    foreach ($record in $records) {
        $process = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
        if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.StartedTicks) {
            & taskkill.exe /PID $record.Id /T /F | Out-Null
        }
    }
    throw
} finally {
    $env:PGPASSWORD = $previousPassword
    $env:PGUSER = $previousUser
    $env:REELMIND_DATA_ROOT = $previousDataRoot
    $credential = $null
}
