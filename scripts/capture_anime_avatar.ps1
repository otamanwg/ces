param(
    [string]$OutputPath = "",
    [ValidateSet("idle", "walk", "sit", "phone", "talk")]
    [string]$Activity = "talk",
    [ValidateSet("cinematic", "street", "distance", "marker")]
    [string]$Lod = "street",
    [ValidateSet("body_standard", "body_sturdy")]
    [string]$Body = "body_standard",
    [ValidatePattern("^face_(0[1-9]|1[0-9]|20)$")]
    [string]$Face = "face_01",
    [ValidatePattern("^skin_0[1-6]$")]
    [string]$Skin = "skin_03",
    [ValidateSet("hair_short_01", "hair_short_02", "hair_medium_01", "hair_medium_02", "hair_long_01", "hair_long_02", "hair_buzz_01", "hair_bald")]
    [string]$Hair = "hair_short_01",
    [ValidateSet("hair_black", "hair_brown", "hair_blond", "hair_auburn", "hair_gray", "hair_white")]
    [string]$HairColor = "hair_brown",
    [double]$DelaySeconds = 2.0,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$env:PATH = "C:\Tools\PowerShell\7.6.2;C:\tools\dotnet-sdk;C:\Tools\MinGit\cmd;" + $env:PATH
$env:DOTNET_ROOT = "C:\tools\dotnet-sdk"

$godot = "C:\Tools\Godot\Godot_v4.3-stable_mono_win64\Godot_v4.3-stable_mono_win64_console.exe"
$dotnet = "C:\tools\dotnet-sdk\dotnet.exe"
if (-not (Test-Path $godot)) {
    throw "Godot not found at $godot"
}
if (-not (Test-Path $dotnet)) {
    $dotnet = "dotnet"
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $Root ".tools\screenshots\anime-avatar-$Lod-$timestamp.png"
}

$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null

if (-not $SkipBuild) {
    & $dotnet build "$Root\client\city_economic_simulator.csproj" -c Debug -v minimal
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$godotOutputPath = $OutputPath.Replace("\", "/")
$delayArgument = $DelaySeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)
& $godot @(
    "--path", "$Root\client",
    "--windowed",
    "--resolution", "1280x720",
    "res://tools/anime_avatar_capture.tscn",
    "--",
    "--output=$godotOutputPath",
    "--delay=$delayArgument",
    "--activity=$Activity",
    "--lod=$Lod",
    "--body=$Body",
    "--face=$Face",
    "--skin=$Skin",
    "--hair=$Hair",
    "--hair-color=$HairColor"
)
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path $OutputPath)) {
    throw "Anime avatar screenshot was not created at $OutputPath"
}

$bytes = [System.IO.File]::ReadAllBytes($OutputPath)
$pngSignature = [byte[]](137, 80, 78, 71, 13, 10, 26, 10)
$hasPngSignature = [System.Linq.Enumerable]::SequenceEqual[byte]($pngSignature, [byte[]]$bytes[0..7])
if ($bytes.Length -lt 1024 -or -not $hasPngSignature) {
    throw "Anime avatar screenshot is not a valid non-empty PNG: $OutputPath"
}

$width = [System.Net.IPAddress]::NetworkToHostOrder([System.BitConverter]::ToInt32($bytes, 16))
$height = [System.Net.IPAddress]::NetworkToHostOrder([System.BitConverter]::ToInt32($bytes, 20))
if ($width -ne 1280 -or $height -ne 720) {
    throw "Anime avatar screenshot has unexpected dimensions ${width}x${height}: $OutputPath"
}

Write-Host "Anime avatar screenshot saved: $OutputPath"
Write-Output $OutputPath
