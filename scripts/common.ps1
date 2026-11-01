$ReelMindRoot = Split-Path -Parent $PSScriptRoot

function Initialize-ReelMindFrontendModules($runtime) {
    $taskSource=[IO.Path]::GetFullPath((Join-Path $ReelMindRoot 'frontend\node_modules'))
    $taskLocalRoot=[IO.Path]::GetFullPath((Split-Path -Parent (Split-Path -Parent $runtime.CredentialPath)))
    $taskDestination=[IO.Path]::GetFullPath((Join-Path $taskLocalRoot 'dependencies\frontend\node_modules'))
    $taskProjectRoot=[IO.Path]::GetFullPath($ReelMindRoot).TrimEnd('\')+'\'
    if(-not $taskSource.StartsWith($taskProjectRoot,[StringComparison]::OrdinalIgnoreCase) -or
       -not $taskDestination.StartsWith($taskLocalRoot.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase) -or
       $taskDestination.StartsWith($taskProjectRoot,[StringComparison]::OrdinalIgnoreCase)) {throw 'Destino de dependencias no válido.'}
    foreach($taskCloudRoot in @($env:OneDrive,$env:OneDriveConsumer,$env:OneDriveCommercial)) {
        if($taskCloudRoot -and $taskDestination.StartsWith([IO.Path]::GetFullPath($taskCloudRoot).TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) {throw 'Las dependencias deben quedar fuera de OneDrive.'}
    }
    if(Test-Path -LiteralPath $taskSource) {
        $taskItem=Get-Item -LiteralPath $taskSource
        if($taskItem.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            if([IO.Path]::GetFullPath([string]$taskItem.Target) -ne $taskDestination){throw 'El enlace de dependencias apunta a otro destino. No se modifica.'}
            return
        }
        if(Test-Path -LiteralPath $taskDestination){throw 'Existen dos carpetas de dependencias. No se sobrescribe ninguna.'}
        New-Item -ItemType Directory -Path (Split-Path -Parent $taskDestination) -Force | Out-Null
        # Both absolute targets were checked above. Preserve every existing file.
        Move-Item -LiteralPath $taskSource -Destination $taskDestination
    } else {New-Item -ItemType Directory -Path $taskDestination -Force | Out-Null}
    New-Item -ItemType Junction -Path $taskSource -Target $taskDestination | Out-Null
}

function Get-ReelMindDataRoot($runtime) {
    if ($runtime.DataRoot) { return $runtime.DataRoot }
    # Derive from the persisted runtime, not a possibly redirected LOCALAPPDATA.
    $runtimeRoot = Split-Path -Parent (Split-Path -Parent $runtime.CredentialPath)
    return Join-Path $runtimeRoot 'data'
}

function Get-ReelMindRuntime {
    $runtimeFile = Join-Path $ReelMindRoot '.local\runtime.json'
    if (Test-Path -LiteralPath $runtimeFile) {
        return Get-Content -LiteralPath $runtimeFile -Raw | ConvertFrom-Json
    }
    # Fallback for installations created before the runtime manifest was introduced.
    return [pscustomobject]@{
        PythonPath = (Join-Path $env:LOCALAPPDATA 'ReelMind\venvs\backend\Scripts\python.exe')
        CredentialPath = (Join-Path $env:LOCALAPPDATA 'ReelMind\secrets\postgres-app.xml')
        AdminCredentialPath = (Join-Path $env:LOCALAPPDATA 'ReelMind\secrets\postgres-admin.xml')
    }
}

function Get-ReelMindDatabaseName($runtime) {
    $taskDatabase=if($runtime.DatabaseName){[string]$runtime.DatabaseName}else{'reelmind'}
    if($taskDatabase -notmatch '^[A-Za-z_][A-Za-z0-9_]{0,62}$'){throw 'Nombre de base local no válido.'}
    return $taskDatabase
}
