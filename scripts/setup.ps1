$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'common.ps1')
$taskProcessFile=Join-Path $projectRoot '.local\processes.json'
if(Test-Path -LiteralPath $taskProcessFile) {
    $taskState=Get-Content -LiteralPath $taskProcessFile -Raw | ConvertFrom-Json
    if($taskState.Root -ne $projectRoot){throw 'El registro de procesos pertenece a otro proyecto.'}
    # Process visibility varies inside app sandboxes. Require the stop launcher to
    # clear its record rather than assuming an invisible process is absent.
    throw 'REELMIND_RUNNING: Ejecuta Detener ReelMind antes de reinstalar dependencias, incluso si el registro quedó de un cierre anterior.'
}
$existingManifest = Test-Path -LiteralPath (Join-Path $projectRoot '.local\runtime.json')
$venvPath = Join-Path $env:LOCALAPPDATA 'ReelMind\venvs\backend'
$pythonPath = if ($existingManifest) { (Get-ReelMindRuntime).PythonPath } else { Join-Path $venvPath 'Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $pythonPath)) {
    if ($existingManifest) { throw 'El entorno guardado no existe. Revisa runtime.json antes de crear otro.' }
    & py -3.13 -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.13 environment could not be created.' }
}
@'
import sys
assert sys.version_info[:2] == (3,13), 'Python 3.13 requerido'
'@ | & $pythonPath -
if ($LASTEXITCODE -ne 0) { throw 'El entorno debe usar Python 3.13.' }
& $pythonPath -m pip install -r (Join-Path $projectRoot 'backend\requirements.lock')
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
$manifestCode = @'
import json, os, sys
from pathlib import Path
root = Path(os.environ['LOCALAPPDATA']) / 'ReelMind'
print(json.dumps({
    'PythonPath': str(Path(sys.executable).resolve()),
    'CredentialPath': str((root / 'secrets/postgres-app.xml').resolve()),
    'AdminCredentialPath': str((root / 'secrets/postgres-admin.xml').resolve()),
}))
'@
if (-not $existingManifest) {
$manifest = & $pythonPath -c $manifestCode
if ($LASTEXITCODE -ne 0) { throw 'Cannot locate runtime.' }
$localDir = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Path $localDir -Force | Out-Null
$manifest | Set-Content -LiteralPath (Join-Path $localDir 'runtime.json') -Encoding UTF8
}
Initialize-ReelMindFrontendModules (Get-ReelMindRuntime)
$taskModules=Get-Item -LiteralPath (Join-Path $projectRoot 'frontend\node_modules')
$taskDependencyRoot=Split-Path -Parent ([string]$taskModules.Target)
foreach($taskPackageFile in @('package.json','package-lock.json')) {
    Copy-Item -LiteralPath (Join-Path $projectRoot ('frontend\'+$taskPackageFile)) -Destination (Join-Path $taskDependencyRoot $taskPackageFile) -Force
}
# npm ci removes junctions when run against them. Install at the real external location.
Push-Location -LiteralPath $taskDependencyRoot
try {
    & npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
} finally { Pop-Location }
Push-Location -LiteralPath (Join-Path $projectRoot 'frontend')
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
Write-Output 'Dependencies ready. Run scripts/backend.ps1 -Action Migrate, then scripts/start.ps1.'
