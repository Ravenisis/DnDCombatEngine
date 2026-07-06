param(
    [switch]$SkipExecutableBuild
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not $SkipExecutableBuild) {
    & "$PSScriptRoot\build_windows.ps1"
}

$AppSource = Join-Path $ProjectRoot "dist\DnDCombatEngine"
$AppExe = Join-Path $AppSource "DnDCombatEngine.exe"
if (-not (Test-Path $AppExe)) {
    throw "Missing packaged executable at $AppExe. Run .\scripts\build_windows.ps1 first."
}

function Find-WixCli {
    $Command = Get-Command "wix.exe" -ErrorAction SilentlyContinue
    if ($Command) {
        return $Command.Source
    }

    $Candidates = @(
        "${env:ProgramFiles}\WiX Toolset v7.0\bin\wix.exe",
        "${env:ProgramFiles}\WiX Toolset v6.0\bin\wix.exe",
        "${env:ProgramFiles}\WiX Toolset v5.0\bin\wix.exe",
        "${env:ProgramFiles}\WiX Toolset v4.0\bin\wix.exe",
        "${env:LOCALAPPDATA}\Programs\WiX Toolset v7.0\bin\wix.exe",
        "${env:LOCALAPPDATA}\Programs\WiX Toolset v6.0\bin\wix.exe",
        "${env:LOCALAPPDATA}\Programs\WiX Toolset v5.0\bin\wix.exe",
        "${env:LOCALAPPDATA}\Programs\WiX Toolset v4.0\bin\wix.exe"
    )

    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path $Candidate)) {
            return $Candidate
        }
    }

    return $null
}

$Wix = Find-WixCli

if (-not $Wix) {
    throw @"
WiX Toolset command-line tools were not found. Install them, then re-run this script.

Recommended local install:
  winget install --id WiXToolset.WiXCLI --accept-package-agreements --accept-source-agreements

GitHub Actions install:
  winget install --id WiXToolset.WiXCLI --accept-package-agreements --accept-source-agreements
"@
}

$WixBuild = Join-Path $ProjectRoot "build\wix"
$MsiOutput = Join-Path $ProjectRoot "dist\msi"
New-Item -ItemType Directory -Force -Path $WixBuild | Out-Null
New-Item -ItemType Directory -Force -Path $MsiOutput | Out-Null

$HarvestedFiles = Join-Path $WixBuild "ApplicationFiles.wxs"
$MsiPath = Join-Path $MsiOutput "DnDCombatEngine-0.1.1-x64.msi"

function Get-StableHash {
    param([string]$Text)

    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes("DnDCombatEngine|$Text")
    $HashBytes = $Hasher.ComputeHash($Bytes)
    return -join ($HashBytes[0..9] | ForEach-Object { $_.ToString("x2") })
}

function Get-WixId {
    param(
        [string]$Prefix,
        [string]$Text
    )

    return "$Prefix$(Get-StableHash $Text)"
}

function Get-StableGuid {
    param([string]$Text)

    $Hasher = [System.Security.Cryptography.MD5]::Create()
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes("DnDCombatEngine|$Text")
    $HashBytes = $Hasher.ComputeHash($Bytes)
    return "{0}" -f ([Guid]::new([byte[]]$HashBytes).ToString().ToUpperInvariant())
}

function Get-RelativePath {
    param(
        [string]$BasePath,
        [string]$FullPath
    )

    $BaseUri = [Uri]("$([System.IO.Path]::GetFullPath($BasePath).TrimEnd('\'))\")
    $FullUri = [Uri]([System.IO.Path]::GetFullPath($FullPath))
    return [Uri]::UnescapeDataString($BaseUri.MakeRelativeUri($FullUri).ToString()).Replace("/", "\")
}

$ComponentIds = New-Object System.Collections.Generic.List[string]
$Settings = New-Object System.Xml.XmlWriterSettings
$Settings.Indent = $true
$Settings.Encoding = [System.Text.UTF8Encoding]::new($false)

$Writer = [System.Xml.XmlWriter]::Create($HarvestedFiles, $Settings)

function Write-ApplicationDirectory {
    param(
        [System.Xml.XmlWriter]$XmlWriter,
        [System.IO.DirectoryInfo]$Directory,
        [string]$DirectoryId
    )

    $Directories = Get-ChildItem -LiteralPath $Directory.FullName -Directory |
        Sort-Object -Property Name
    $Files = Get-ChildItem -LiteralPath $Directory.FullName -File |
        Sort-Object -Property Name

    foreach ($ChildDirectory in $Directories) {
        $RelativeDirectory = Get-RelativePath $AppSource $ChildDirectory.FullName
        $ChildDirectoryId = Get-WixId "Dir" $RelativeDirectory

        $XmlWriter.WriteStartElement("Directory")
        $XmlWriter.WriteAttributeString("Id", $ChildDirectoryId)
        $XmlWriter.WriteAttributeString("Name", $ChildDirectory.Name)
        Write-ApplicationDirectory $XmlWriter $ChildDirectory $ChildDirectoryId
        $XmlWriter.WriteEndElement()
    }

    foreach ($File in $Files) {
        $RelativeFile = Get-RelativePath $AppSource $File.FullName
        $ComponentId = Get-WixId "Cmp" $RelativeFile
        $FileId = Get-WixId "File" $RelativeFile
        $Source = '$(var.AppSource)\' + $RelativeFile

        $ComponentIds.Add($ComponentId)

        $XmlWriter.WriteStartElement("Component")
        $XmlWriter.WriteAttributeString("Id", $ComponentId)
        $XmlWriter.WriteAttributeString("Guid", (Get-StableGuid $RelativeFile))
        $XmlWriter.WriteStartElement("File")
        $XmlWriter.WriteAttributeString("Id", $FileId)
        $XmlWriter.WriteAttributeString("Source", $Source)
        $XmlWriter.WriteAttributeString("KeyPath", "yes")
        $XmlWriter.WriteEndElement()
        $XmlWriter.WriteEndElement()
    }
}

$Writer.WriteStartDocument()
$Writer.WriteStartElement("Wix", "http://wixtoolset.org/schemas/v4/wxs")
$Writer.WriteStartElement("Fragment")
$Writer.WriteStartElement("DirectoryRef")
$Writer.WriteAttributeString("Id", "INSTALLFOLDER")
Write-ApplicationDirectory $Writer (Get-Item -LiteralPath $AppSource) "INSTALLFOLDER"
$Writer.WriteEndElement()
$Writer.WriteEndElement()

$Writer.WriteStartElement("Fragment")
$Writer.WriteStartElement("ComponentGroup")
$Writer.WriteAttributeString("Id", "ApplicationFiles")
foreach ($ComponentId in $ComponentIds) {
    $Writer.WriteStartElement("ComponentRef")
    $Writer.WriteAttributeString("Id", $ComponentId)
    $Writer.WriteEndElement()
}
$Writer.WriteEndElement()
$Writer.WriteEndElement()
$Writer.WriteEndElement()
$Writer.WriteEndDocument()
$Writer.Close()

& $Wix --acceptEula wix7 build `
    -arch x64 `
    -define "AppSource=$AppSource" `
    -intermediatefolder $WixBuild `
    -out $MsiPath `
    "packaging\DnDCombatEngine.wxs" `
    $HarvestedFiles

if ($LASTEXITCODE -ne 0) {
    throw "WiX build failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path $MsiPath)) {
    throw "MSI build completed without producing $MsiPath."
}

Write-Host "Built MSI installer: $MsiPath"
