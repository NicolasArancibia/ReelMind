[CmdletBinding()]
param([switch]$Install)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
$taskRuntime = Get-ReelMindRuntime
$taskDataRoot = Get-ReelMindDataRoot $taskRuntime
$taskSource = Join-Path $taskDataRoot 'tools/pgvector-v0.8.7'
$taskPgRoot = Join-Path $env:ProgramFiles 'PostgreSQL/18'
$taskVswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$taskVsRoot = & $taskVswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $taskVsRoot) { throw 'Faltan herramientas C++ x64. No se instala otro compilador automáticamente.' }
if (-not (Test-Path -LiteralPath (Join-Path $taskPgRoot 'include/server/postgres.h'))) { throw 'Faltan encabezados PostgreSQL 18.' }
if (-not (Test-Path -LiteralPath $taskSource)) {
    New-Item -ItemType Directory -Path (Split-Path $taskSource) -Force | Out-Null
    & git.exe clone --depth 1 --branch v0.8.7 https://github.com/pgvector/pgvector.git $taskSource
    if ($LASTEXITCODE) { throw 'No se pudo recuperar pgvector.' }
}
$taskTag = & git.exe -C $taskSource describe --tags --exact-match
if ($taskTag -ne 'v0.8.7') { throw 'Revision de pgvector inesperada.' }
$taskBuild = Join-Path $taskSource 'build-reelmind.cmd'
@("@echo off", "call `"$(Join-Path $taskVsRoot 'VC/Auxiliary/Build/vcvars64.bat')`" >nul", 'if errorlevel 1 exit /b 1', "set `"PGROOT=$taskPgRoot`"", "cd /d `"$taskSource`"", 'nmake /nologo /F Makefile.win', 'exit /b %errorlevel%') | Set-Content -LiteralPath $taskBuild -Encoding ASCII
& cmd.exe /d /c $taskBuild
if ($LASTEXITCODE) { throw 'Compilacion pgvector fallida.' }
if (-not $Install) { Write-Output 'pgvector compilado; falta instalacion explicita.'; return }
$taskFiles = @(@{Source=(Join-Path $taskSource 'vector.dll');Target=(Join-Path $taskPgRoot 'lib/vector.dll')}, @{Source=(Join-Path $taskSource 'vector.control');Target=(Join-Path $taskPgRoot 'share/extension/vector.control')})
$taskFiles += @(Get-ChildItem -LiteralPath (Join-Path $taskSource 'sql') -Filter 'vector--*.sql' -File | ForEach-Object { @{Source=$_.FullName;Target=(Join-Path $taskPgRoot ('share/extension/'+$_.Name))} })
foreach ($taskFile in $taskFiles) {
    if (Test-Path -LiteralPath $taskFile.Target) {
        if ((Get-FileHash -LiteralPath $taskFile.Source).Hash -ne (Get-FileHash -LiteralPath $taskFile.Target).Hash) { throw 'Existe otra version de pgvector; no se sobrescribe.' }
    } else { Copy-Item -LiteralPath $taskFile.Source -Destination $taskFile.Target }
}
Write-Output 'Archivos de pgvector instalados; habilitar extension solo en ReelMind.'
