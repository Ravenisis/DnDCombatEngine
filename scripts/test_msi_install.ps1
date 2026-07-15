param(
    [string]$MsiPath = "",
    [string]$InstallFolder = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

if (-not $MsiPath) {
    $MsiPath = Join-Path $ProjectRoot "dist\msi\DnDCombatEngine-1.0.3-x64.msi"
}
if (-not $InstallFolder) {
    $InstallFolder = Join-Path $ProjectRoot "build\msi-smoke\DnDCombatEngine"
}
$MsiPath = [System.IO.Path]::GetFullPath($MsiPath)
$InstallFolder = [System.IO.Path]::GetFullPath($InstallFolder)
$LogFolder = Join-Path $ProjectRoot "build\msi-smoke"
$DataPath = Join-Path $ProjectRoot "build\msi-smoke\user-data"

if (-not (Test-Path -LiteralPath $MsiPath)) {
    throw "MSI installer not found: $MsiPath"
}
New-Item -ItemType Directory -Force -Path $LogFolder | Out-Null

function Invoke-Msi {
    param(
        [string]$Operation,
        [string]$LogName,
        [string[]]$AdditionalArguments = @()
    )

    $LogPath = Join-Path $LogFolder "msiexec-$LogName.log"
    $Arguments = @(
        $Operation,
        "`"$MsiPath`"",
        "/qn",
        "/norestart",
        "/l*v",
        "`"$LogPath`""
    ) + $AdditionalArguments
    $Process = Start-Process "msiexec.exe" `
        -ArgumentList $Arguments `
        -Wait `
        -PassThru `
        -WindowStyle Hidden
    if ($Process.ExitCode -notin @(0, 3010)) {
        throw "Windows Installer exited with code $($Process.ExitCode). See $LogPath."
    }
}

$Application = $null
$Installed = $false
$PreviousDataPath = $env:DND_COMBAT_ENGINE_DATA
try {
    Invoke-Msi "/i" "install" @("INSTALLFOLDER=`"$InstallFolder`"")
    $Installed = $true
    $Executable = Join-Path $InstallFolder "DnDCombatEngine.exe"
    if (-not (Test-Path -LiteralPath $Executable)) {
        throw "MSI did not install the application executable at $Executable."
    }

    $env:DND_COMBAT_ENGINE_DATA = $DataPath
    $Application = Start-Process $Executable -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 8
    if ($Application.HasExited) {
        throw "MSI-installed application exited during its startup smoke test."
    }
    Write-Host "MSI install and application launch smoke test passed."
}
finally {
    if ($null -ne $Application -and -not $Application.HasExited) {
        Stop-Process -Id $Application.Id -Force
    }
    if ($null -eq $PreviousDataPath) {
        Remove-Item Env:DND_COMBAT_ENGINE_DATA -ErrorAction SilentlyContinue
    }
    else {
        $env:DND_COMBAT_ENGINE_DATA = $PreviousDataPath
    }
    if ($Installed) {
        Invoke-Msi "/x" "uninstall"
    }
}
