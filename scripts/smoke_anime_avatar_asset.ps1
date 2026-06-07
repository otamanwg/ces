param(
    [switch]$SkipBuild
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
$importSettings = Join-Path $Root "client\assets\visual\anime\avatar\canonical_anime_avatar.glb.import"
if (-not (Test-Path $godot)) {
    throw "Godot not found at $godot"
}
if (-not (Test-Path $importSettings)) {
    throw "Godot import settings not found: $importSettings"
}
if ((Get-Content -Raw $importSettings) -notmatch "meshes/generate_lods=true") {
    throw "Canonical avatar import must keep generated mesh LOD enabled."
}

if (-not $SkipBuild) {
    & $dotnet build "$Root\client\city_economic_simulator.csproj" -c Debug -v minimal
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& $godot `
    --path "$Root\client" `
    "res://tools/canonical_avatar_asset_smoke.tscn"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Canonical anime avatar asset smoke passed."
