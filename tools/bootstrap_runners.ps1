<#
.SYNOPSIS
  Build (or refresh) Malbolge runner binaries from source and verify their
  SHA256 matches the committed manifests.

.DESCRIPTION
  Runner binaries are git-ignored; the manifests record provenance
  (source, commit, build command, expected SHA256). This script reproduces
  the binaries from source so the SHA256 can be independently re-verified.

  It does NOT modify the manifests. If a rebuilt binary does not match the
  manifest hash, the script fails loudly (provenance broken).

.PARAMETER RepoRoot
  Repo root. Defaults to the parent of the script's directory.

.PARAMETER ZigExe
  Zig compiler path. Auto-detected if omitted.

.PARAMETER GccExe
  GCC compiler path (for the C engine). Auto-detected if omitted.

.EXAMPLE
  py powershell tools/bootstrap_runners.ps1
#>
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ZigExe = "",
    [string]$GccExe = ""
)

$ErrorActionPreference = "Stop"
$script:FAIL = 0
$script:PASS = 0

function Check([string]$name, [bool]$ok, [string]$detail = "") {
    if ($ok) { $script:PASS++; Write-Host "  PASS: $name" }
    else { $script:FAIL++; Write-Host "  FAIL: $name $detail" }
}

function Get-Hash([string]$path) {
    return (Get-FileHash -Path $path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Find-Tool {
    param([string]$Name)
    $found = Get-Command $Name -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
    return $found
}

# --- Resolve toolchains ---
if (-not $ZigExe) { $ZigExe = Find-Tool "zig" }
if (-not $GccExe) { $GccExe = Find-Tool "gcc" }
Write-Host "Repo root: $RepoRoot"
Write-Host "zig: $ZigExe"
Write-Host "gcc: $GccExe"

# --- bolge19 (Unshackled) from Zig source ---
Write-Host ""
Write-Host "=== bolge19 (Unshackled) ==="
$unshManifest = Get-Content -LiteralPath (Join-Path $RepoRoot "runners/malbolge-unshackled/manifest.json") -Raw | ConvertFrom-Json
$targetBin = Join-Path $RepoRoot "runners/malbolge-unshackled/bolge19.exe"

# Source lives outside the repo (malbolge-lisp-forensics). Prefer env var; else relative sibling.
$unshSrc = $env:MALBOLGE_LISP_FORENSICS
if (-not $unshSrc -or -not (Test-Path -LiteralPath "$unshSrc\src\bolge19\main.zig")) {
    $candidate = Join-Path (Split-Path -Parent $RepoRoot) "malbolge-lisp-forensics"
    if (Test-Path -LiteralPath "$candidate\src\bolge19\main.zig") { $unshSrc = $candidate }
}
$mainZig = if ($unshSrc) { Join-Path $unshSrc "src/bolge19/main.zig" } else { "" }

if (-not $ZigExe) {
    Check "zig toolchain present" $false "zig not found; set -ZigExe or put zig on PATH"
} elseif (-not (Test-Path -LiteralPath $mainZig)) {
    Check "bolge19 source present" $false "set MALBOLGE_LISP_FORENSICS or place malbolge-lisp-forensics beside the repo"
} else {
    Check "bolge19 source present" $true $mainZig
    $tmpBin = Join-Path $env:TEMP "bolge19_build_$PID.exe"
    Write-Host "  building: zig build-exe ... -femit-bin=$tmpBin"
    $buildOut = & $ZigExe build-exe -O ReleaseFast $mainZig "-femit-bin=$tmpBin" 2>&1 | Out-String
    Write-Host $buildOut
    if (-not (Test-Path -LiteralPath $tmpBin)) {
        Check "bolge19 build succeeded" $false "zig build failed: $buildOut"
    } else {
        $hash = Get-Hash $tmpBin
        $want = $unshManifest.binary_sha256.ToUpperInvariant()
        if ($hash -eq $want) {
            Copy-Item -LiteralPath $tmpBin -Destination $targetBin -Force
            Check "bolge19 SHA256 matches manifest + installed" $true
        } else {
            # Reproducibility mismatch: do NOT clobber a matching committed binary.
            Check "bolge19 rebuild reproducible" $false "rebuild=$hash want=$want; committed binary preserved"
        }
        Remove-Item -LiteralPath $tmpBin -Force -ErrorAction SilentlyContinue
    }
}

# --- malbolge-engine (Classic) from C source ---
Write-Host ""
Write-Host "=== malbolge-engine (Classic) ==="
$origManifest = Get-Content -LiteralPath (Join-Path $RepoRoot "runners/malbolge-original/manifest.json") -Raw | ConvertFrom-Json
$targetBin2 = Join-Path $RepoRoot "runners/malbolge-original/malbolge.exe"

# Source outside repo (Malbolge-Engine). Prefer env var; else relative sibling.
$engSrc = $env:MALBOLGE_ENGINE
if (-not $engSrc -or -not (Test-Path -LiteralPath "$engSrc\src\vm.c")) {
    $candidate = Join-Path (Split-Path -Parent $RepoRoot) "Malbolge-Engine"
    if (Test-Path -LiteralPath "$candidate\src\vm.c") { $engSrc = $candidate }
}
$vmC = if ($engSrc) { Join-Path $engSrc "src/vm.c" } else { "" }

if (-not $GccExe) {
    Check "gcc toolchain present" $false "gcc not found; set -GccExe"
} elseif (-not (Test-Path -LiteralPath $vmC)) {
    Check "malbolge-engine source present" $false "set MALBOLGE_ENGINE or place Malbolge-Engine beside the repo"
} else {
    Check "malbolge-engine source present" $true $vmC
    # main() lives in src/malbolge.c; vm.c is the library. Compile both.
    $mainC = Join-Path $engSrc "src/malbolge.c"
    $tmpBin2 = Join-Path $env:TEMP "malbolge_build_$PID.exe"
    Write-Host "  building: gcc -O2 -std=c11 $vmC $mainC -o $tmpBin2"
    $buildOut2 = & $GccExe -O2 -std=c11 $vmC $mainC -o $tmpBin2 2>&1 | Out-String
    Write-Host $buildOut2
    if (-not (Test-Path -LiteralPath $tmpBin2)) {
        Check "malbolge-engine build succeeded" $false "gcc build failed: $buildOut2"
    } else {
        $hash2 = Get-Hash $tmpBin2
        $want2 = $origManifest.binary_sha256.ToUpperInvariant()
        if ($hash2 -eq $want2) {
            Copy-Item -LiteralPath $tmpBin2 -Destination $targetBin2 -Force
            Check "malbolge-engine SHA256 matches manifest + installed" $true
        } else {
            # Reproducibility mismatch: do NOT clobber a matching committed binary.
            Check "malbolge-engine rebuild reproducible" $false "rebuild=$hash2 want=$want2; committed binary preserved"
        }
        Remove-Item -LiteralPath $tmpBin2 -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "=============================="
Write-Host "PASS: $script:PASS"
Write-Host "FAIL: $script:FAIL"
Write-Host "=============================="
Write-Host ""
Write-Host "Run tools/runner_doctor.ps1 next to verify the built binaries."
if ($script:FAIL -gt 0) {
    Write-Host "Bootstrap had failures."
    exit 1
} else {
    Write-Host "Bootstrap OK (or source/toolchain not present to attempt rebuild)."
    exit 0
}