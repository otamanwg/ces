param(
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

if (-not $SkipBuild) {
    & $dotnet build "$Root\client\city_economic_simulator.csproj" -c Debug -v minimal
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$output = & $godot `
    --headless `
    --path "$Root\client" `
    "res://tools/api_dispatch_runtime_smoke.tscn" 2>&1
$exitCode = $LASTEXITCODE
$output | ForEach-Object { $_ }

if ($exitCode -ne 0) { exit $exitCode }
if (($output -join "`n") -notmatch "API_DISPATCH_RUNTIME_SMOKE_OK") {
    throw "Godot API dispatch smoke did not emit its success marker."
}

Write-Host "Godot API dispatch runtime smoke passed."
