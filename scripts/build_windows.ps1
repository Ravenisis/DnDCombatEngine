param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not $SkipInstall) {
    python -m pip install -e ".[gui,installer]"
}

python -m PyInstaller packaging/DnDCombatEngine.spec --noconfirm --clean
Write-Host "Built dist/DnDCombatEngine/DnDCombatEngine.exe"
