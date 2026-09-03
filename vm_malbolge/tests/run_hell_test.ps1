<#
.SYNOPSIS
  Compile a .hell file with LMAO and execute it on the classic Malbolge
  runner with stdin bytes, asserting expected output.

#>
param(
    [string]$HellFile,
    [byte[]]$StdinBytes = @(),
    [byte[]]$Expect = @(),
    [int]$MaxSteps = 900000
)
$ErrorActionPreference = "Stop"
$RepoRoot = (Split-Path -Parent $PSScriptRoot)
$LmaoExe = Join-Path $RepoRoot "third_party\lmao\bin\lmao.exe"
$RunnerExe = Join-Path $RepoRoot "runners\malbolge-original\malbolge.exe"

$tmp = [System.IO.Path]::GetTempFileName()
$tmp = [System.IO.Path]::ChangeExtension($tmp, ".mb")
[string]$hexin = ($StdinBytes | ForEach-Object { $_.ToString("x2") }) -join " "
[string]$hexout = ($Expect | ForEach-Object { $_.ToString("x2") }) -join " "
Write-Host "stdin: [$hexin]"
Write-Host "expect: [$hexout]"

& $LmaoExe -f -o $tmp $HellFile | Out-String | Write-Host
if (-not (Test-Path $tmp)) { throw "lmao failed" }

$stdinPath = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllBytes($stdinPath, $StdinBytes)

$outRaw = & cmd /c "`"$RunnerExe`" `"$tmp`" $MaxSteps < `"$stdinPath`"" 2>&1 | Out-String
# The runner native stdout gets passed through; PowerShell returns full text.
Write-Host "raw runner output:"
Write-Host $outRaw
