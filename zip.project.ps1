git ls-files --cached --others --exclude-standard > zipaetheon.txt
$files = Get-Content zipaetheon.txt
Compress-Archive -Path $files -DestinationPath Aetheon.zip -Force
pause