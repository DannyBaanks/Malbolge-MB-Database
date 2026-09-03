<#
.SYNOPSIS
  Verify Malbolge runner integrity: binary presence, SHA256 vs manifest,
  known-vector execution, variant sanity, and exit/steps capture.

.DESCRIPTION
  The runner doctor turns runner manifests (which are CLAIMS) into verified
  facts. For each declared runner it checks:
    1. binary exists (or reports missing)
    2. binary SHA256 matches the manifest
    3. a known-vector program executes with the expected output
    4. the expected variant is enforced (variant firewall)
    5. exit code / steps / status are captured

  This is REFERENCE / RUNNER_PROVENANCE evidence. Malbolge-runtime evidence
  (MALBOLGE_RUNTIME) requires an actual .mb artifact + runner, which A04 adds.

.PARAMETER Fixture
  Known-vector file to execute (default: tools/fixtures/hello_world_40.mb).

.EXAMPLE
  py powershell tools/runner_doctor.ps1
#>
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
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

function Test-Runner {
    param(
        [string]$RunnerName,
        [string]$Binary,
        [string]$Manifest,
        [string]$ExpectedVariant,
        [object]$ManifestData,
        [string]$KnownOutput,
        [int]$KnownSteps
    )

    Write-Host ""
    Write-Host "=== $RunnerName ($ExpectedVariant) ==="

    # 1. binary presence
    $binPath = Join-Path $RepoRoot $Binary
    Check "$RunnerName binary exists" (Test-Path -LiteralPath $binPath)

    if (-not (Test-Path -LiteralPath $binPath)) {
        Check "$RunnerName SHA256" $false "missing binary"
        Check "$RunnerName known-vector" $false "missing binary"
        Check "$RunnerName variant" $false "missing binary"
        Check "$RunnerName exit/steps" $false "missing binary"
        return
    }

    # 2. SHA256 vs manifest
    $manifestHash = $ManifestData.binary_sha256.ToUpperInvariant()
    $actualHash = Get-Hash $binPath
    Check "$RunnerName SHA256 matches manifest" ($actualHash -eq $manifestHash) "got=$actualHash want=$manifestHash"

    # 3. known-vector execution
    $fixture = Join-Path $RepoRoot "tools/fixtures/hello_world_40.mb"
    $out = ""
    $err = ""
    $exit = -1
    try {
        $tmpOut = Join-Path $env:TEMP "md_$RunnerName.out"
        $tmpErr = Join-Path $env:TEMP "md_$RunnerName.err"
        Remove-Item -LiteralPath $tmpOut, $tmpErr -ErrorAction SilentlyContinue
        $p = Start-Process -FilePath $binPath -ArgumentList @('"' + $fixture + '"') -NoNewWindow -Wait -PassThru -RedirectStandardOutput $tmpOut -RedirectStandardError $tmpErr
        $exit = $p.ExitCode
        $out = Get-Content -LiteralPath $tmpOut -Raw -ErrorAction SilentlyContinue
        $err = Get-Content -LiteralPath $tmpErr -Raw -ErrorAction SilentlyContinue
    } catch {
        $err = $_.Exception.Message
    }

    # Steps/status are reported on stderr by these runners.
    $all = "$out`n$err"

    if ($ExpectedVariant -eq "original") {
        # Classic runner must produce the Classic known output.
        Check "$RunnerName known-vector output" ($all -match [regex]::Escape($KnownOutput)) "got output around: $($all.Substring(0, [Math]::Min(80, $all.Length)))"
        Check "$RunnerName step count" ($all -match "steps:\s*$KnownSteps|steps=$KnownSteps") "got: $all"
    } else {
        # Unshackled runner executes the same program under 19-trit semantics,
        # so it must NOT reproduce the Classic output (variant firewall).
        $hasClassicOut = $all -match [regex]::Escape($KnownOutput)
        Check "$RunnerName executes (exit=$exit)" ($exit -eq 0) "exit=$exit"
        Check "$RunnerName variant enforced (no Classic output on 19-trit)" (-not $hasClassicOut) "unexpectedly reproduced Classic output"
    }

    Check "$RunnerName exit captured" ($exit -ge 0) "exit=$exit"
    Check "$RunnerName status/steps captured" ($all -match "HALT|steps") "no halt/steps marker in output"
}

Write-Host "Repo root: $RepoRoot"

# --- Load manifests ---
$origManifest = Get-Content -LiteralPath (Join-Path $RepoRoot "runners/malbolge-original/manifest.json") -Raw | ConvertFrom-Json
$unshManifest = Get-Content -LiteralPath (Join-Path $RepoRoot "runners/malbolge-unshackled/manifest.json") -Raw | ConvertFrom-Json

Test-Runner -RunnerName "malbolge-engine" `
    -Binary "runners/malbolge-original/malbolge.exe" `
    -Manifest "runners/malbolge-original/manifest.json" `
    -ExpectedVariant "original" `
    -ManifestData $origManifest `
    -KnownOutput "Hello World!" `
    -KnownSteps 40

Test-Runner -RunnerName "bolge19" `
    -Binary "runners/malbolge-unshackled/bolge19.exe" `
    -Manifest "runners/malbolge-unshackled/manifest.json" `
    -ExpectedVariant "unshackled" `
    -ManifestData $unshManifest `
    -KnownOutput "Hello World!" `
    -KnownSteps 40

# --- Independent oracle cross-check (Classic) ---
Write-Host ""
Write-Host "=== oracle_classic.py cross-check (independent 3^10 reference) ==="
$oracleOut = (& py (Join-Path $RepoRoot "tools/oracle_classic.py") (Join-Path $RepoRoot "tools/fixtures/hello_world_40.mb") 2>&1 | Out-String)
$hasHello = $oracleOut -match "Hello World!"
$hasSteps = $oracleOut -match '"steps": 40'
$hasHalted = $oracleOut -match '"status": "HALTED"'
Check "oracle_classic output 'Hello World!'" $hasHello $oracleOut
Check "oracle_classic 40 steps" $hasSteps $oracleOut
Check "oracle_classic HALTED" $hasHalted $oracleOut

Write-Host ""
Write-Host "=============================="
Write-Host "PASS: $script:PASS"
Write-Host "FAIL: $script:FAIL"
Write-Host "=============================="

if ($script:FAIL -gt 0) {
    Write-Host "Runner doctor FAILED."
    exit 1
} else {
    Write-Host "Runner doctor OK."
    exit 0
}