param(
    [string]$OutputPath = "",
    [double]$DelaySeconds = 3.0,
    [switch]$SkipBuild,
    [switch]$StressText
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$env:PATH = "C:\Tools\dotnet;C:\Tools\MinGit\cmd;" + $env:PATH
$env:DOTNET_ROOT = "C:\Tools\dotnet"

$godot = "C:\Tools\Godot\Godot_v4.3-stable_mono_win64\Godot_v4.3-stable_mono_win64_console.exe"
$dotnet = "C:\Tools\dotnet\dotnet.exe"
if (-not (Test-Path $godot)) {
    throw "Godot not found at $godot"
}
if (-not (Test-Path $dotnet)) {
    $dotnet = "dotnet"
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $OutputPath = Join-Path $Root ".tools\screenshots\dashboard-$timestamp.png"
}

$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

if (-not $SkipBuild) {
    Write-Host "Building Godot C# project..."
    & $dotnet build "$Root\client\city_economic_simulator.csproj" -c Debug -v minimal
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& "$Root\scripts\start_backend.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$godotOutputPath = $OutputPath.Replace("\", "/")
$delayArgument = $DelaySeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)
Write-Host "Capturing dashboard at 1280x720..."
$godotArguments = @(
    "--path", "$Root\client",
    "--windowed",
    "--resolution", "1280x720",
    "res://tools/dashboard_capture.tscn",
    "--",
    "--output=$godotOutputPath",
    "--delay=$delayArgument"
)
if ($StressText) {
    $godotArguments += "--stress-text"
}

& $godot @godotArguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path $OutputPath)) {
    throw "Dashboard screenshot was not created at $OutputPath"
}

$bytes = [System.IO.File]::ReadAllBytes($OutputPath)
$pngSignature = [byte[]](137, 80, 78, 71, 13, 10, 26, 10)
$hasPngSignature = [System.Linq.Enumerable]::SequenceEqual[byte]($pngSignature, [byte[]]$bytes[0..7])
if ($bytes.Length -lt 1024 -or -not $hasPngSignature) {
    throw "Dashboard screenshot is not a valid non-empty PNG: $OutputPath"
}

$width = [System.Net.IPAddress]::NetworkToHostOrder([System.BitConverter]::ToInt32($bytes, 16))
$height = [System.Net.IPAddress]::NetworkToHostOrder([System.BitConverter]::ToInt32($bytes, 20))
if ($width -ne 1280 -or $height -ne 720) {
    throw "Dashboard screenshot has unexpected dimensions ${width}x${height}: $OutputPath"
}

Write-Host "Dashboard screenshot saved: $OutputPath"
Write-Output $OutputPath
