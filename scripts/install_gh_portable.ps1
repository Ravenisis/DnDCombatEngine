param(
    [string]$InstallRoot = ".tools\gh"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$targetRoot = Join-Path $repoRoot $InstallRoot
$downloadRoot = Join-Path $repoRoot ".tmp\downloads"
New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
New-Item -ItemType Directory -Force -Path $downloadRoot | Out-Null

$release = Invoke-RestMethod -Uri "https://api.github.com/repos/cli/cli/releases/latest"
$asset = $release.assets | Where-Object {
    $_.name -match "^gh_[0-9.]+_windows_amd64\.zip$"
} | Select-Object -First 1

if ($null -eq $asset) {
    throw "Could not find a Windows amd64 GitHub CLI zip asset in the latest release."
}

$archive = Join-Path $downloadRoot $asset.name
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $archive

$extractRoot = Join-Path $downloadRoot "gh-extract"
if (Test-Path $extractRoot) {
    Remove-Item -LiteralPath $extractRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
Expand-Archive -Path $archive -DestinationPath $extractRoot -Force

$bin = Get-ChildItem -Path $extractRoot -Recurse -Filter "gh.exe" | Select-Object -First 1
if ($null -eq $bin) {
    throw "Downloaded archive did not contain gh.exe."
}

Copy-Item -Path $bin.FullName -Destination (Join-Path $targetRoot "gh.exe") -Force

$installed = Join-Path $targetRoot "gh.exe"
& $installed --version
Write-Host "Installed GitHub CLI portable executable at $installed"
