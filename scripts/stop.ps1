$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$processFile = Join-Path $ReelMindRoot '.local\processes.json'
if (-not (Test-Path -LiteralPath $processFile)) {
    Write-Output 'No hay procesos de ReelMind registrados.'
    return
}
$state = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
if ($state.Root -ne $ReelMindRoot) { throw 'The process record belongs to another project. Nothing stopped.' }
foreach ($record in $state.Processes) {
    $process = Get-Process -Id $record.Id -ErrorAction SilentlyContinue
    if ($process -and $process.StartTime.ToUniversalTime().Ticks.ToString() -eq $record.StartedTicks) {
        & taskkill.exe /PID $record.Id /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Cannot stop a ReelMind process. Keep the process record for recovery.' }
    }
}
Remove-Item -LiteralPath $processFile
Write-Output 'ReelMind detenido. PostgreSQL permanece disponible; tus datos estan guardados.'
