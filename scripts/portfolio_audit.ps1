param([switch]$PreCommit, [switch]$BeforePush)
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$passes = New-Object System.Collections.Generic.List[string]

function Add-Fail {
    param([string]$Message)
    $failures.Add($Message) | Out-Null
}

function Add-Warn {
    param([string]$Message)
    $warnings.Add($Message) | Out-Null
}

function Add-Pass {
    param([string]$Message)
    $passes.Add($Message) | Out-Null
}

function From-Codes {
    param([int[]]$Codes)
    return -join ($Codes | ForEach-Object { [char]$_ })
}

function Get-RelativeRepoPath {
    param([string]$FullPath)
    $rootWithSep = $RepoRoot.TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    return $FullPath.Substring($rootWithSep.Length).Replace("\", "/")
}

$ExcludedPrefixes = @(
    ".git/",
    ".venv/",
    "examples/index/",
    "output/",
    "work/",
    "raw/"
)

function Test-ExcludedRelPath {
    param([string]$RelPath)
    $normalized = $RelPath.Replace("\", "/")
    foreach ($prefix in $ExcludedPrefixes) {
        if ($normalized -eq $prefix.TrimEnd("/")) {
            return $true
        }
        if ($normalized.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Get-CandidateFiles {
    $files = New-Object System.Collections.Generic.List[string]
    $stack = New-Object System.Collections.Generic.Stack[string]
    $stack.Push($RepoRoot)

    while ($stack.Count -gt 0) {
        $dir = $stack.Pop()
        foreach ($item in Get-ChildItem -LiteralPath $dir -Force) {
            $rel = Get-RelativeRepoPath $item.FullName
            if ($item.PSIsContainer) {
                if (-not (Test-ExcludedRelPath ($rel + "/"))) {
                    $stack.Push($item.FullName)
                }
            } else {
                if (-not (Test-ExcludedRelPath $rel)) {
                    $files.Add($item.FullName) | Out-Null
                }
            }
        }
    }

    return $files
}

function Get-ScanFiles {
    $gitDir = Join-Path $RepoRoot ".git"
    if (Test-Path -LiteralPath $gitDir) {
        $tracked = @(& git -C $RepoRoot ls-files 2>$null)
        if ($LASTEXITCODE -eq 0 -and $tracked.Count -gt 0) {
            Add-Pass "Using tracked files from git ls-files."
            return @($tracked | ForEach-Object { Join-Path $RepoRoot $_ })
        }
        Add-Warn "No tracked files found; scanning repository candidates only."
    } else {
        Add-Warn "Git repository not initialized; scanning repository candidates only."
    }

    return @(Get-CandidateFiles)
}

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-RepoSlugFromRemote {
    param([string]$RemoteUrl)
    if (-not $RemoteUrl) {
        return $null
    }
    $clean = $RemoteUrl.Trim()
    if ($clean -match "github.com[:/]([^/]+)/([^/.]+)(\.git)?$") {
        return "$($matches[1])/$($matches[2])"
    }
    return $null
}

function Check-GitHubState {
    $gitDir = Join-Path $RepoRoot ".git"
    if (-not (Test-Path -LiteralPath $gitDir)) {
        Add-Warn "Git repository is not initialized yet; remote checks are pending."
        return
    }

    $remoteNames = @(& git -C $RepoRoot remote)
    if ($remoteNames -notcontains "origin") {
        Add-Warn "No origin remote found; public visibility and sync checks are pending."
    } else {
        $remoteUrl = (& git -C $RepoRoot remote get-url origin)
        $slug = Get-RepoSlugFromRemote $remoteUrl
        if (-not $slug) {
            Add-Warn "Origin remote is not a recognized GitHub URL."
        } elseif (Test-CommandExists "gh") {
            $visibilityJson = (& gh repo view $slug --json visibility 2>$null)
            if ($LASTEXITCODE -eq 0 -and $visibilityJson) {
                $visibility = ($visibilityJson | ConvertFrom-Json).visibility
                if ($visibility -eq "PUBLIC") {
                    Add-Pass "GitHub repository visibility is PUBLIC."
                } else {
                    Add-Fail "GitHub repository visibility is not PUBLIC."
                }
            } else {
                Add-Fail "Unable to verify GitHub repository visibility with gh."
            }
        } else {
            Add-Fail "GitHub CLI is unavailable; cannot verify repository visibility."
        }
    }

    $status = @(& git -C $RepoRoot status --porcelain 2>$null)
    if ($LASTEXITCODE -eq 0) {
        if ($status.Count -eq 0) {
            Add-Pass "Working tree is clean."
        } elseif ($PreCommit) {
            & git -C $RepoRoot diff --quiet
            if ($LASTEXITCODE -ne 0) {
                Add-Fail "Pre-commit audit requires all tracked edits staged."
            } else {
                $untracked = @(& git -C $RepoRoot ls-files --others --exclude-standard)
                if ($untracked.Count -gt 0) {
                    Add-Fail "Pre-commit audit requires new publication files staged."
                } else {
                    Add-Pass "Auditing fully staged changes before commit. Clean-tree release audit remains required."
                }
            }
        } else {
            Add-Fail "Working tree has uncommitted changes."
        }
    } else {
        Add-Warn "Unable to read git status."
    }

    $currentBranch = (& git -C $RepoRoot branch --show-current)
    if ([string]::IsNullOrWhiteSpace($currentBranch)) {
        Add-Warn "No current branch found; remote sync check is pending."
        return
    }

    $upstream = (& git -C $RepoRoot for-each-ref "--format=%(upstream:short)" "refs/heads/$currentBranch")
    if ([string]::IsNullOrWhiteSpace($upstream)) {
        Add-Warn "No upstream branch configured; remote sync check is pending."
        return
    }

    $localHead = (& git -C $RepoRoot rev-parse HEAD)
    $remoteHead = (& git -C $RepoRoot rev-parse $upstream)
    if ($LASTEXITCODE -eq 0 -and $localHead -eq $remoteHead) {
        Add-Pass "Local branch and upstream are synchronized."
    } elseif ($BeforePush) {
        & git -C $RepoRoot merge-base --is-ancestor $upstream HEAD
        if ($LASTEXITCODE -eq 0) {
            Add-Pass "Upstream is an ancestor; local commits are ready for a fast-forward push."
        } else {
            Add-Fail "Upstream changed or diverged; resolve before publishing."
        }
    } else {
        Add-Fail "Local branch and upstream are not synchronized."
    }
}

$BlockedExtensions = @(".pdf", ".docx", ".xlsx", ".zip", ".mp4", ".mov", ".mkv", ".wav", ".mp3")
$MaxFileBytes = 1MB

$SensitiveTerms = @(
    (From-Codes @(69,117,114,111,108,105,110,107)),
    (From-Codes @(78,101,119,32,70,97,100,97)),
    (From-Codes @(82,88,32,67,111,110,115,117,108,116)),
    (From-Codes @(30495,23454,20844,21496)),
    (From-Codes @(30495,23454,23458,25143)),
    (From-Codes @(30495,23454,21512,20316,26041)),
    (From-Codes @(21830,19994,38381,29615)),
    (From-Codes @(30408,21033,27169,24335)),
    (From-Codes @(35746,38405)),
    (From-Codes @(28857,25968)),
    (From-Codes @(67,82,77)),
    (From-Codes @(20869,37096,36335,24452)),
    (From-Codes @(67,58,92,85,115,101,114,115)),
    (From-Codes @(83,97,103,105,115,116,97,114,105,97,109)),
    (From-Codes @(103,104,112,95)),
    (From-Codes @(103,105,116,104,117,98,95,112,97,116,95)),
    (From-Codes @(65,78,84,72,82,79,80,73,67,95,65,85,84,72,95,84,79,75,69,78))
)

$SecretRegexes = @(
    "(?i)(^|[^a-z0-9])" + [regex]::Escape((From-Codes @(115,107,45))) + "[a-z0-9_-]{8,}",
    "(?i)(^|[^a-z0-9])" + [regex]::Escape((From-Codes @(103,104,112,95))) + "[a-z0-9_]{8,}",
    "(?i)(^|[^a-z0-9])" + [regex]::Escape((From-Codes @(103,105,116,104,117,98,95,112,97,116,95))) + "[a-z0-9_]{8,}"
)

$scanFiles = @(Get-ScanFiles)
Add-Pass "Scanning $($scanFiles.Count) file(s) within repository boundary."

foreach ($file in $scanFiles) {
    if (-not (Test-Path -LiteralPath $file)) {
        continue
    }

    $item = Get-Item -LiteralPath $file
    $rel = Get-RelativeRepoPath $item.FullName
    $ext = $item.Extension.ToLowerInvariant()

    if ($BlockedExtensions -contains $ext) {
        Add-Fail "Blocked file type found: $rel"
    }

    if ($item.Length -gt $MaxFileBytes) {
        Add-Fail "Large file found: $rel ($($item.Length) bytes)"
    }

    try {
        $content = Get-Content -LiteralPath $item.FullName -Raw -Encoding UTF8 -ErrorAction Stop
    } catch {
        Add-Warn "Could not read file as UTF-8 text: $rel"
        continue
    }

    foreach ($term in $SensitiveTerms) {
        if ($content.IndexOf($term, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            Add-Fail "Sensitive term found in: $rel"
            break
        }
    }

    foreach ($pattern in $SecretRegexes) {
        if ($content -match $pattern) {
            Add-Fail "Credential-like pattern found in: $rel"
            break
        }
    }
}

Check-GitHubState

Write-Host "Portfolio Audit"
Write-Host "Repository: $RepoRoot"
Write-Host ""

foreach ($message in $passes) {
    Write-Host "PASS: $message"
}
foreach ($message in $warnings) {
    Write-Host "WARN: $message"
}
foreach ($message in $failures) {
    Write-Host "FAIL: $message"
}

if ($failures.Count -gt 0) {
    Write-Host "AUDIT RESULT: FAIL"
    exit 1
}

Write-Host "AUDIT RESULT: PASS"
exit 0
