$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $env:LOCALAPPDATA 'ReelMind\venvs\backend'
$pythonPath = Join-Path $venvPath 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    & py -3.13 -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.13 environment could not be created.' }
}
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
$manifest = & $pythonPath -c $manifestCode
if ($LASTEXITCODE -ne 0) { throw 'Cannot locate runtime.' }
$localDir = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Path $localDir -Force | Out-Null
$manifest | Set-Content -LiteralPath (Join-Path $localDir 'runtime.json') -Encoding UTF8
Push-Location -LiteralPath (Join-Path $projectRoot 'frontend')
try {
    & npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
Write-Output 'Dependencies ready. Run scripts/backend.ps1 -Action Migrate, then scripts/start.ps1.'
