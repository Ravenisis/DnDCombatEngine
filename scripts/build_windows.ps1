param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Find-Python {
    $Python = Get-Command "python" -ErrorAction SilentlyContinue
    if ($Python) {
        return @($Python.Source)
    }

    $Py = Get-Command "py" -ErrorAction SilentlyContinue
    if ($Py) {
        return @($Py.Source, "-3")
    }

    throw "Python was not found. Install Python or add it to PATH, then re-run this script."
}

$PythonCommand = @(Find-Python)
$PythonExe = $PythonCommand[0]
$PythonArgs = @()
if ($PythonCommand.Length -gt 1) {
    $PythonArgs = $PythonCommand[1..($PythonCommand.Length - 1)]
}

if (-not $SkipInstall) {
    & $PythonExe @PythonArgs -m pip install -e ".[gui,installer]"
}

& $PythonExe @PythonArgs -m PyInstaller packaging/DnDCombatEngine.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE."
}
Write-Host "Built dist/DnDCombatEngine/DnDCombatEngine.exe"
