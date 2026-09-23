[CmdletBinding(SupportsShouldProcess = $true)]
param([switch]$BuildOnly)

. "$PSScriptRoot\release-tools.ps1"

# Destino deliberadamente fijo: nunca aceptar una raiz arbitraria para reemplazarla.
$destination = 'C:\inetpub\AetheonCodex'
$originalLocation = Get-Location
$mutex = $null
$locked = $false

function Assert-PlainDirectory {
    param([string]$Path)
    # Revisar tambien los ancestros antes de copiar o renombrar.
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if (-not $item.PSIsContainer -or
                ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Ruta no segura (archivo o enlace): $current"
            }
        }
        $current = [IO.Path]::GetDirectoryName($current)
    }
    if (Test-Path -LiteralPath $Path) {
        $links = Get-ChildItem -LiteralPath $Path -Force -Recurse |
            Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }
        if ($links) { throw "La carpeta contiene enlaces o junctions: $Path" }
    }
}

try {
    if (-not $PSCmdlet.ShouldProcess($destination, 'Construir Codex y publicar en IIS (BuildOnly omite IIS)')) {
        return
    }
    # Evita dos publicaciones simultaneas, incluso desde distintas sesiones.
    $mutex = New-Object Threading.Mutex($false, 'Global\AetheonCodexLocalDeploy')
    try { $locked = $mutex.WaitOne(0) }
    catch [Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { throw 'Ya hay una publicacion local en curso.' }

    Set-Location $PSScriptRoot
    Invoke-AetheonPython -Root $PSScriptRoot -Arguments @('scripts/build.py')
    $source = Join-Path $PSScriptRoot 'site'
    Assert-PlainDirectory $source
    $index = Join-Path $source 'index.html'
    if (-not (Test-Path -LiteralPath $index -PathType Leaf) -or
        (Get-Item -LiteralPath $index).Length -eq 0) {
        throw 'La construccion no ha producido site/index.html valido.'
    }
    if ($BuildOnly) {
        Write-Host '[OK] Codex construido. IIS no se ha modificado.'
        return
    }

    Assert-PlainDirectory $destination
    $parent = Split-Path -Parent $destination
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        throw "No existe $parent. Prepara primero IIS y sus permisos."
    }
    $null = Get-Command robocopy.exe -ErrorAction Stop
    $suffix = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N')
    $staging = Join-Path $parent "AetheonCodex-staging-$suffix"
    $backup = Join-Path $parent "AetheonCodex-backup-$suffix"
    # Crear el staging comprueba escritura en el padre sin tocar el sitio activo.
    $null = New-Item -ItemType Directory -Path $staging
    if (Test-Path -LiteralPath $destination) {
        # Los ficheros nuevos heredan los permisos de la raiz actual del sitio.
        Set-Acl -LiteralPath $staging -AclObject (Get-Acl -LiteralPath $destination)
    }
    Write-Host "Preparando sitio en $staging"
    & robocopy.exe $source $staging /E /COPY:DAT /DCOPY:DAT /R:2 /W:1 /XJ /NP /NFL /NDL
    $copyExit = $LASTEXITCODE
    if ($copyExit -ge 8) { throw "Robocopy fallo con codigo $copyExit. El sitio anterior sigue activo." }

    $config = Join-Path $destination 'web.config'
    if (Test-Path -LiteralPath $config -PathType Leaf) {
        Copy-Item -LiteralPath $config -Destination (Join-Path $staging 'web.config') -Force
    }
    Assert-PlainDirectory $staging
    Assert-PlainDirectory $destination
    $hadSite = Test-Path -LiteralPath $destination -PathType Container
    if ($hadSite) {
        Move-Item -LiteralPath $destination -Destination $backup
        Write-Host "Copia anterior: $backup"
    }
    try {
        Move-Item -LiteralPath $staging -Destination $destination
    }
    catch {
        $publishError = $_
        if ($hadSite) {
            try {
                Move-Item -LiteralPath $backup -Destination $destination
                Write-Host 'Se ha restaurado el sitio anterior.'
            }
            catch {
                throw "No se pudo publicar ni restaurar. Recupera manualmente $backup en $destination. Error: $_"
            }
        }
        throw $publishError
    }
    Write-Host "[OK] Codex publicado en $destination"
    Write-Host 'Las copias anteriores se conservan fuera del sitio. Revisalas antes de borrarlas.'
}
catch {
    Write-Error -Message "Publicacion local fallida: $_. Comprueba permisos sobre C:\inetpub y el sitio; puede requerir PowerShell como administrador. Las carpetas staging/backup se conservan para diagnostico." -ErrorAction Continue
    exit 1
}
finally {
    Set-Location $originalLocation
    if ($locked) { $mutex.ReleaseMutex() }
    if ($null -ne $mutex) { $mutex.Dispose() }
}
