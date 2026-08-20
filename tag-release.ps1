$ErrorActionPreference = "Stop"

Write-Error @"
tag-release.ps1 has been replaced by the integrity-preserving release flow.

Start a release from develop with one of:
  .\start-release.ps1 -Patch
  .\start-release.ps1 -Minor
  .\start-release.ps1 -Major

Finish a prepared release from release/X.Y.Z with:
  .\finish-release.ps1
"@
exit 1
