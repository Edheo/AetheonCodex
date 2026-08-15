$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================"
Write-Host " AETHEON RELEASE TAG"
Write-Host "======================================"
Write-Host ""

# --------------------------------------------------
# Determine current branch
# --------------------------------------------------

$branch = git branch --show-current

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Unable to determine current Git branch."
    exit 1
}

$branch = $branch.Trim()

Write-Host "[INFO] Current branch: $branch"

# --------------------------------------------------
# Validate release branch
# Expected format: release/vX.Y.Z
# --------------------------------------------------

if ($branch -notmatch '^release/(\d+\.\d+\.\d+)$') {
    Write-Host ""
    Write-Host "[ERROR] Current branch is not a release branch."
    Write-Host "[ERROR] Expected format: release/vX.Y.Z"
    Write-Host ""
    exit 1
}

$tag = $Matches[1]

Write-Host "[INFO] Release detected: $tag"

# --------------------------------------------------
# Require clean working tree
# --------------------------------------------------

$status = git status --porcelain

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Unable to determine Git status."
    exit 1
}

if ($status) {
    Write-Host ""
    Write-Host "[ERROR] Working tree is not clean."
    Write-Host "[ERROR] Commit or discard pending changes before tagging."
    Write-Host ""
    git status --short
    exit 1
}

# --------------------------------------------------
# Ensure tag does not already exist locally
# --------------------------------------------------

$existingTag = git tag --list $tag

if ($existingTag) {
    Write-Host ""
    Write-Host "[ERROR] Tag '$tag' already exists locally."
    Write-Host ""
    exit 1
}

# --------------------------------------------------
# Ensure tag does not already exist remotely
# --------------------------------------------------

$remoteTag = git ls-remote --tags origin "refs/tags/$tag"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Unable to check remote tags."
    exit 1
}

if ($remoteTag) {
    Write-Host ""
    Write-Host "[ERROR] Tag '$tag' already exists on origin."
    Write-Host ""
    exit 1
}

# --------------------------------------------------
# Confirmation
# --------------------------------------------------

Write-Host ""
Write-Host "Release tag to create:"
Write-Host ""
Write-Host "    Branch : $branch"
Write-Host "    Tag    : $tag"
Write-Host ""

$confirmation = Read-Host "Create and push this tag? [y/N]"

if ($confirmation -notmatch '^[yY]$') {
    Write-Host ""
    Write-Host "[INFO] Tag creation cancelled."
    exit 0
}

# --------------------------------------------------
# Create annotated tag
# --------------------------------------------------

Write-Host ""
Write-Host "[TAG] Creating $tag..."

git tag -a $tag -m "Release $tag"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Unable to create tag '$tag'."
    exit 1
}

# --------------------------------------------------
# Push tag
# --------------------------------------------------

Write-Host "[TAG] Pushing $tag to origin..."

git push origin $tag

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Unable to push tag '$tag'."
    Write-Host "[WARNING] The tag exists locally but was not pushed."
    exit 1
}

Write-Host ""
Write-Host "======================================"
Write-Host " RELEASE TAG CREATED"
Write-Host "======================================"
Write-Host ""
Write-Host "Branch : $branch"
Write-Host "Tag    : $tag"
Write-Host ""