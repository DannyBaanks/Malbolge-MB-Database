<#
.SYNOPSIS
  Build the vendored LMAO assembler (third_party/lmao) into bin/lmao.exe.

.DESCRIPTION
  Compiles the C source of LMAO 0.6.0 with win_flex + bison + gcc, producing
  bin/lmao.exe. Records the source commit hash for provenance.

.PARAMETER FlexExe
  Path to win_flex.exe. ELSE: env:WIN_FLEX_EXE. ELSE: PATH lookup.

.PARAMETER BisonExe
  Path to win_bison.exe. ELSE: env:WIN_BISON_EXE. ELSE: PATH lookup.

.PARAMETER GccExe
  Path to gcc. Auto-detected if omitted.
#>
param(
    [string]$FlexExe = $env:WIN_FLEX_EXE,
    [string]$BisonExe = $env:WIN_BISON_EXE,
    [string]$GccExe = ""
)

$ErrorActionPreference = "Stop"
if (-not $FlexExe) { $FlexExe = (Get-Command win_flex -ErrorAction SilentlyContinue).Source }
if (-not $BisonExe) { $BisonExe = (Get-Command win_bison -ErrorAction SilentlyContinue).Source }
if (-not $GccExe) { $GccExe = (Get-Command gcc -ErrorAction SilentlyContinue).Source }
if (-not $GccExe) { throw "gcc not found" }
if (-not (Test-Path -LiteralPath $FlexExe)) { throw "win_flex not found: $FlexExe" }
if (-not (Test-Path -LiteralPath $BisonExe)) { throw "win_bison not found: $BisonExe" }

$LmaoRoot = Join-Path (Split-Path -Parent $PSScriptRoot) "third_party\lmao"
$BinDir = Join-Path $LmaoRoot "bin"
New-Item -ItemType Directory -Force $BinDir | Out-Null

Write-Host "bison: $BisonExe"
Write-Host "flex : $FlexExe"
Write-Host "gcc  : $GccExe"

Write-Host "[1/3] bison -> bin/lmao.tab.c"
& $BisonExe -d -v -o (Join-Path $BinDir "lmao.tab.c") (Join-Path $LmaoRoot "src\lmao.y") | Out-Null

Write-Host "[2/3] flex -> bin/lex.yy.c"
& $FlexExe -o (Join-Path $BinDir "lex.yy.c") (Join-Path $LmaoRoot "src\lmao.l") | Out-Null

Write-Host "[3/3] gcc -> bin/lmao.exe"
$sources = @(
    (Join-Path $BinDir "lex.yy.c"),
    (Join-Path $BinDir "lmao.tab.c")
) + (Get-ChildItem (Join-Path $LmaoRoot "src") -Filter *.c | ForEach-Object { $_.FullName })
& $GccExe -O2 -I (Join-Path $LmaoRoot "src") -o (Join-Path $BinDir "lmao.exe") $sources

if (-not (Test-Path -LiteralPath (Join-Path $BinDir "lmao.exe"))) { throw "build failed" }
$hash = (Get-FileHash (Join-Path $BinDir "lmao.exe") -Algorithm SHA256).Hash
Write-Host ""
Write-Host "Built: $(Join-Path $BinDir 'lmao.exe')"
Write-Host "SHA256: $hash"
Write-Host "provenance: https://github.com/esoteric-programmer/LMAO @ 3ea747e16b45ea7627018b291409b12c1f9ca3dc"
