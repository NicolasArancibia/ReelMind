# Diagnostico de lectura; no instala programas ni muestra credenciales.
$ErrorActionPreference = 'Continue'
$projectRoot = Split-Path -Parent $PSScriptRoot
Write-Output ('Proyecto: ' + $projectRoot)

foreach ($toolName in @('git', 'node', 'npm.cmd')) {
    $toolCommand = Get-Command $toolName -ErrorAction SilentlyContinue
    if ($toolCommand) {
        Write-Output ('Herramienta: ' + $toolName)
        & $toolCommand.Source --version
    } else {
        Write-Output ('NO DETECTADO: ' + $toolName)
    }
}

$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pythonLauncher) {
    & $pythonLauncher.Source -0p
    & $pythonLauncher.Source -3.13 --version
    & $pythonLauncher.Source -3.13 -m pip --version
} else {
    Write-Output 'NO DETECTADO: lanzador py'
}

$pgBin = Join-Path $env:ProgramFiles 'PostgreSQL\18\bin'
$psqlPath = Join-Path $pgBin 'psql.exe'
$readyPath = Join-Path $pgBin 'pg_isready.exe'
if (Test-Path -LiteralPath $psqlPath) {
    & $psqlPath --version
    & $readyPath -h 127.0.0.1 -p 5432
    Write-Output 'pg_isready comprueba disponibilidad, no autenticacion ni persistencia.'
} else {
    Write-Output 'PostgreSQL 18 no detectado en su ruta estandar.'
}

$vsCodePath = Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\Code.exe'
if (Test-Path -LiteralPath $vsCodePath) {
    Write-Output ('VS Code: ' + (Get-Item -LiteralPath $vsCodePath).VersionInfo.ProductVersion)
} else {
    Write-Output 'VS Code no detectado en su ruta por usuario.'
}

$driveLetter = [IO.Path]::GetPathRoot($projectRoot).TrimEnd('\').TrimEnd(':')
$projectDrive = Get-PSDrive -Name $driveLetter -ErrorAction SilentlyContinue
if ($projectDrive) {
    Write-Output ('Espacio libre (GiB): ' + [math]::Round($projectDrive.Free / 1GB, 1))
}
if (Test-Path -LiteralPath (Join-Path $projectRoot '.git')) {
    & git -C $projectRoot status --short --branch
} else {
    Write-Output 'Repositorio Git no inicializado.'
}
