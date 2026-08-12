git ls-files --cached --others --exclude-standard > zipaetheon.txt

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$zipPath = "Aetheon.zip"
$files = Get-Content zipaetheon.txt

if (Test-Path $zipPath) {
    Remove-Item $zipPath
}

$archive = [System.IO.Compression.ZipFile]::Open(
    $zipPath,
    [System.IO.Compression.ZipArchiveMode]::Create
)

foreach ($file in $files) {
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $archive,
        (Resolve-Path $file).Path,
        $file
    ) | Out-Null
}

$archive.Dispose()
pause