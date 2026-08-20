Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-AetheonGit {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [switch]$Quiet
    )

    if (-not $Quiet) {
        Write-Host "`n> git $($Arguments -join ' ')"
    }

    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        if ($output) { $output | Write-Host }
        throw "Git command failed: git $($Arguments -join ' ')"
    }

    return @($output)
}

function Get-AetheonCurrentBranch {
    $branch = (Invoke-AetheonGit -Arguments @("branch", "--show-current") -Quiet) -join ""
    $branch = $branch.Trim()
    if (-not $branch) {
        throw "Detached HEAD detected. An active branch is required."
    }
    return $branch
}

function Assert-AetheonCleanWorktree {
    $status = (Invoke-AetheonGit -Arguments @("status", "--porcelain") -Quiet) -join "`n"
    if ($status.Trim()) {
        throw "The working tree is not clean. Commit or discard pending changes first."
    }
}

function Get-AetheonVersion {
    param([Parameter(Mandatory = $true)][string]$Root)

    $path = Join-Path $Root "VERSION"
    if (-not (Test-Path -LiteralPath $path)) {
        throw "VERSION does not exist."
    }

    $version = (Get-Content -LiteralPath $path -Raw).Trim()
    if ($version -notmatch '^\d+\.\d+\.\d+$') {
        throw "VERSION must use X.Y.Z format. Current value: '$version'."
    }
    return $version
}

function Get-AetheonLatestTagVersion {
    # origin/develop contiene todas las publicaciones históricas tras el fetch.
    # Los tags nuevos se crean sobre master y pasan a ser alcanzables desde
    # develop al sincronizarlo.
    $versions = foreach ($tag in (Invoke-AetheonGit -Arguments @("tag", "--merged", "origin/develop", "--list") -Quiet)) {
        $value = "$tag".Trim()
        if ($value -match '^v?(\d+)\.(\d+)\.(\d+)$') {
            [PSCustomObject]@{
                Tag = $value
                Major = [int]$Matches[1]
                Minor = [int]$Matches[2]
                Patch = [int]$Matches[3]
            }
        }
    }

    $latest = $versions |
        Sort-Object Major, Minor, Patch -Descending |
        Select-Object -First 1

    if (-not $latest) {
        throw "No semantic release tag (X.Y.Z or vX.Y.Z) was found."
    }
    return $latest
}

function Get-AetheonNextVersion {
    param(
        [Parameter(Mandatory = $true)]$Current,
        [Parameter(Mandatory = $true)]
        [ValidateSet("Patch", "Minor", "Major")]
        [string]$Bump
    )

    $major = [int]$Current.Major
    $minor = [int]$Current.Minor
    $patch = [int]$Current.Patch

    switch ($Bump) {
        "Patch" { $patch += 1 }
        "Minor" { $minor += 1; $patch = 0 }
        "Major" { $major += 1; $minor = 0; $patch = 0 }
    }

    return "$major.$minor.$patch"
}

function Test-AetheonRefExists {
    param([Parameter(Mandatory = $true)][string]$Ref)

    & git show-ref --verify --quiet $Ref
    return $LASTEXITCODE -eq 0
}

function Assert-AetheonRefSynchronized {
    param(
        [Parameter(Mandatory = $true)][string]$Local,
        [Parameter(Mandatory = $true)][string]$Remote
    )

    if (-not (Test-AetheonRefExists -Ref "refs/heads/$Local")) {
        throw "Local branch '$Local' does not exist."
    }
    if (-not (Test-AetheonRefExists -Ref "refs/remotes/$Remote")) {
        throw "Remote branch '$Remote' does not exist."
    }

    $localSha = (Invoke-AetheonGit -Arguments @("rev-parse", $Local) -Quiet) -join ""
    $remoteSha = (Invoke-AetheonGit -Arguments @("rev-parse", $Remote) -Quiet) -join ""
    if ($localSha.Trim() -ne $remoteSha.Trim()) {
        throw "'$Local' is not synchronized with '$Remote'."
    }
}

function Update-AetheonBranchFromRemote {
    param(
        [Parameter(Mandatory = $true)][string]$Local,
        [Parameter(Mandatory = $true)][string]$Remote
    )

    if (-not (Test-AetheonRefExists -Ref "refs/heads/$Local")) {
        throw "Local branch '$Local' does not exist."
    }
    if (-not (Test-AetheonRefExists -Ref "refs/remotes/$Remote")) {
        throw "Remote branch '$Remote' does not exist."
    }

    $localSha = ((Invoke-AetheonGit -Arguments @("rev-parse", $Local) -Quiet) -join "").Trim()
    $remoteSha = ((Invoke-AetheonGit -Arguments @("rev-parse", $Remote) -Quiet) -join "").Trim()
    if ($localSha -eq $remoteSha) { return }

    & git merge-base --is-ancestor $Local $Remote
    if ($LASTEXITCODE -ne 0) {
        throw "'$Local' cannot be fast-forwarded safely to '$Remote'."
    }

    if ((Get-AetheonCurrentBranch) -eq $Local) {
        Invoke-AetheonGit -Arguments @("merge", "--ff-only", $Remote) | Out-Null
    }
    else {
        Invoke-AetheonGit -Arguments @("branch", "-f", $Local, $Remote) | Out-Null
    }
    Write-Host "[OK] '$Local' fast-forwarded to '$Remote'."
}

function Invoke-AetheonPython {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $candidates = @(
        (Join-Path $Root ".venv\Scripts\python.exe"),
        "py",
        "python"
    )
    $python = $null
    foreach ($candidate in $candidates) {
        try {
            & $candidate --version *> $null
            if ($LASTEXITCODE -eq 0) {
                $python = $candidate
                break
            }
        }
        catch {
            continue
        }
    }
    if (-not $python) {
        throw "No working Python runtime was found. Recreate .venv before continuing."
    }

    Write-Host "`n> $python $($Arguments -join ' ')"
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed."
    }
}
