param(
    [switch]$SkipExecutableBuild
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not $SkipExecutableBuild) {
    & "$PSScriptRoot\build_windows.ps1"
}

$InnoCandidates = @(
    "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
)
$ISCC = $InnoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ISCC) {
    throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php"
}

& $ISCC packaging/DnDCombatEngine.iss
Write-Host "Built dist/installer/DnDCombatEngine-1.0.2-Setup.exe"
