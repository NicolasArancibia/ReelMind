$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$taskRuntime=Get-ReelMindRuntime
$taskPython=Join-Path (Split-Path -Parent $taskRuntime.PythonPath) 'pythonw.exe'
if(-not (Test-Path -LiteralPath $taskPython)){throw 'Falta pythonw en el runtime. Revisa la instalación de Python 3.13.'}
Start-Process -FilePath $taskPython -ArgumentList '-m app.maintenance_window' -WorkingDirectory (Join-Path $ReelMindRoot 'backend') -WindowStyle Normal
