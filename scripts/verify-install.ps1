# Reproduces dependencies/build in an isolated external fixture, never in global Python.
param([string]$Resume)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$taskRuntime=Get-ReelMindRuntime
$taskInstall=Join-Path (Split-Path -Parent (Get-ReelMindDataRoot $taskRuntime)) ('verification-phase7\install-'+[guid]::NewGuid().ToString('N'))
if($Resume) {
    $taskExpected=[IO.Path]::GetFullPath((Split-Path -Parent $taskInstall))
    $taskInstall=[IO.Path]::GetFullPath($Resume)
    if((Split-Path -Parent $taskInstall) -ne $taskExpected -or (Split-Path -Leaf $taskInstall) -notmatch '^install-[a-f0-9]{32}$') {throw 'Solo se retoma un entorno aislado de esta verificación.'}
} else {New-Item -ItemType Directory -Path $taskInstall | Out-Null}
$taskPython=Join-Path $taskInstall 'venv\Scripts\python.exe'
if(-not $Resume) {
& $taskRuntime.PythonPath -m venv (Join-Path $taskInstall 'venv')
if($LASTEXITCODE -ne 0){throw 'No se pudo crear el entorno aislado.'}
& $taskPython -m pip install --disable-pip-version-check -q -r (Join-Path $ReelMindRoot 'backend\requirements.lock')
if($LASTEXITCODE -ne 0){throw 'Falló la instalación fijada; se conserva el entorno para diagnóstico.'}
}
& $taskPython -m pip check
if($LASTEXITCODE -ne 0){throw 'Dependencias Python incompatibles.'}
@'
import sys, fastapi, sqlalchemy, psycopg, av, faster_whisper, httpx
assert sys.version_info[:2] == (3,13)
print('Python 3.13 e importaciones verificadas.')
'@ | & $taskPython -
if($LASTEXITCODE -ne 0){throw 'Falló la comprobación de importaciones.'}
$taskFrontend=Join-Path $taskInstall 'frontend'
New-Item -ItemType Directory -Path $taskFrontend | Out-Null
foreach($taskFile in @('package.json','package-lock.json','index.html','tsconfig.json','vite.config.ts')) {
    Copy-Item -LiteralPath (Join-Path $ReelMindRoot ('frontend\'+$taskFile)) -Destination (Join-Path $taskFrontend $taskFile)
}
Copy-Item -LiteralPath (Join-Path $ReelMindRoot 'frontend\src') -Destination (Join-Path $taskFrontend 'src') -Recurse
if(Test-Path -LiteralPath (Join-Path $ReelMindRoot 'frontend\public')) {
    Copy-Item -LiteralPath (Join-Path $ReelMindRoot 'frontend\public') -Destination (Join-Path $taskFrontend 'public') -Recurse
}
Push-Location -LiteralPath $taskFrontend
try {
    & npm.cmd ci --no-audit --no-fund
    if($LASTEXITCODE -ne 0){throw 'Falló npm ci del entorno aislado.'}
    & npm.cmd run build
    if($LASTEXITCODE -ne 0){throw 'Falló la compilación reproducida.'}
} finally {Pop-Location}
$taskReport=[pscustomobject]@{verified=$true;python='3.13';backend_lock_sha256=(Get-FileHash -LiteralPath (Join-Path $ReelMindRoot 'backend\requirements.lock')).Hash;frontend_lock_sha256=(Get-FileHash -LiteralPath (Join-Path $taskFrontend 'package-lock.json')).Hash;fixture=$taskInstall;models_downloaded=$false;global_changes=$false}
$taskReport | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskInstall 'verification.json') -Encoding UTF8
$taskReport | ConvertTo-Json
