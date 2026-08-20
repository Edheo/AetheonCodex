[CmdletBinding()]
param()

. "$PSScriptRoot\release-tools.ps1"

$originalLocation = Get-Location
try {
    Set-Location $PSScriptRoot

    $releaseBranch = Get-AetheonCurrentBranch
    if ($releaseBranch -notmatch '^release/(\d+\.\d+\.\d+)$') {
        throw "A release must finish from release/X.Y.Z. Current branch: '$releaseBranch'."
    }
    $version = $Matches[1]

    Assert-AetheonCleanWorktree
    $canonicalVersion = Get-AetheonVersion -Root $PSScriptRoot
    if ($canonicalVersion -ne $version) {
        throw "VERSION ($canonicalVersion) does not match branch '$releaseBranch'."
    }

    Invoke-AetheonGit -Arguments @("fetch", "origin", "--prune", "--tags") | Out-Null
    Assert-AetheonRefSynchronized -Local $releaseBranch -Remote "origin/$releaseBranch"
    Update-AetheonBranchFromRemote -Local "master" -Remote "origin/master"
    Update-AetheonBranchFromRemote -Local "develop" -Remote "origin/develop"

    if (Test-AetheonRefExists -Ref "refs/tags/$version") {
        throw "Tag '$version' already exists."
    }

    Invoke-AetheonPython -Root $PSScriptRoot -Arguments @("-m", "unittest", "discover", "tests")
    Invoke-AetheonPython -Root $PSScriptRoot -Arguments @("scripts/build.py")
    Assert-AetheonCleanWorktree

    $commits = (Invoke-AetheonGit -Arguments @("log", "--oneline", "master..$releaseBranch") -Quiet) -join "`n"
    Write-Host ""
    Write-Host "AETHEON RELEASE PUBLICATION"
    Write-Host "  Release branch : $releaseBranch"
    Write-Host "  Version        : $version"
    Write-Host "  Operations     : merge into master, tag, merge master into develop, atomic push"
    Write-Host ""
    Write-Host "Commits included:"
    Write-Host $commits
    $answer = Read-Host "Finish and publish this release? [y/N]"
    if ($answer -notmatch '^[yY]$') {
        Write-Host "Release publication cancelled."
        exit 0
    }

    Invoke-AetheonGit -Arguments @("switch", "master") | Out-Null
    Invoke-AetheonGit -Arguments @("merge", "--no-ff", $releaseBranch, "-m", "Merge branch '$releaseBranch'") | Out-Null
    $releaseCommit = ((Invoke-AetheonGit -Arguments @("rev-parse", "HEAD") -Quiet) -join "").Trim()
    Invoke-AetheonGit -Arguments @("tag", "-a", $version, $releaseCommit, "-m", "Release $version") | Out-Null

    Invoke-AetheonGit -Arguments @("switch", "develop") | Out-Null
    Invoke-AetheonGit -Arguments @("merge", "--no-ff", "master", "-m", "Merge branch 'master' into develop") | Out-Null

    $pushArguments = @(
        "push", "--atomic", "origin",
        "refs/heads/master:refs/heads/master",
        "refs/heads/develop:refs/heads/develop",
        "refs/tags/$version:refs/tags/$version"
    )
    if (Test-AetheonRefExists -Ref "refs/remotes/origin/$releaseBranch") {
        $pushArguments += ":refs/heads/$releaseBranch"
    }
    Invoke-AetheonGit -Arguments $pushArguments | Out-Null
    Invoke-AetheonGit -Arguments @("branch", "-d", $releaseBranch) | Out-Null

    Write-Host ""
    Write-Host "Release $version published successfully."
    Write-Host "Tag $version points to published master commit $releaseCommit."
    Write-Host "Current branch: develop."
}
catch {
    Write-Error $_
    Write-Host "No automatic rollback was attempted. Inspect the current Git state before retrying."
    exit 1
}
finally {
    Set-Location $originalLocation
}
