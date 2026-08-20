[CmdletBinding()]
param(
    [switch]$Patch,
    [switch]$Minor,
    [switch]$Major
)

. "$PSScriptRoot\release-tools.ps1"

$originalLocation = Get-Location
try {
    Set-Location $PSScriptRoot

    $selected = @($Patch, $Minor, $Major).Where({ $_ }).Count
    if ($selected -ne 1) {
        throw "Choose exactly one release increment: -Patch, -Minor or -Major."
    }

    $bump = if ($Patch) { "Patch" } elseif ($Minor) { "Minor" } else { "Major" }
    $branch = Get-AetheonCurrentBranch
    if ($branch -ne "develop") {
        throw "A release must start from 'develop'. Current branch: '$branch'."
    }

    Assert-AetheonCleanWorktree
    Invoke-AetheonGit -Arguments @("fetch", "origin", "--prune", "--tags") | Out-Null
    Update-AetheonBranchFromRemote -Local "develop" -Remote "origin/develop"

    $latest = Get-AetheonLatestTagVersion
    $publishedVersion = "$($latest.Major).$($latest.Minor).$($latest.Patch)"
    $canonicalVersion = Get-AetheonVersion -Root $PSScriptRoot
    if ($canonicalVersion -ne $publishedVersion) {
        throw "VERSION ($canonicalVersion) does not match the latest release tag ($($latest.Tag))."
    }

    $version = Get-AetheonNextVersion -Current $latest -Bump $bump
    $releaseBranch = "release/$version"
    if (Test-AetheonRefExists -Ref "refs/heads/$releaseBranch") {
        throw "Local branch '$releaseBranch' already exists."
    }
    if (Test-AetheonRefExists -Ref "refs/remotes/origin/$releaseBranch") {
        throw "Remote branch 'origin/$releaseBranch' already exists."
    }
    if (Test-AetheonRefExists -Ref "refs/tags/$version") {
        throw "Tag '$version' already exists."
    }

    Write-Host ""
    Write-Host "AETHEON RELEASE PREPARATION"
    Write-Host "  Published version : $publishedVersion"
    Write-Host "  Increment         : $bump"
    Write-Host "  New version       : $version"
    Write-Host "  New branch        : $releaseBranch"
    $answer = Read-Host "Create this release? [y/N]"
    if ($answer -notmatch '^[yY]$') {
        Write-Host "Release preparation cancelled."
        exit 0
    }

    Invoke-AetheonGit -Arguments @("switch", "-c", $releaseBranch) | Out-Null
    [System.IO.File]::WriteAllText(
        (Join-Path $PSScriptRoot "VERSION"),
        "$version`n",
        [System.Text.UTF8Encoding]::new($false)
    )
    Invoke-AetheonPython -Root $PSScriptRoot -Arguments @("scripts/build.py")

    Write-Host ""
    Write-Host "Release '$version' prepared on '$releaseBranch'."
    Write-Host "Review and commit VERSION and the generated docs before publishing the release branch."
    Invoke-AetheonGit -Arguments @("status", "--short") | ForEach-Object { Write-Host $_ }
}
catch {
    Write-Error $_
    exit 1
}
finally {
    Set-Location $originalLocation
}
