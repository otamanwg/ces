param(
    [switch]$ResetDb,
    [switch]$RunCheck
)

# One-click dev launch for City Economic Simulator
# Usage: .\scripts\play.ps1 [-ResetDb] [-RunCheck]

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$env:PATH = "C:\tools\dotnet;C:\tools\MinGit\cmd;" + $env:PATH
$env:DOTNET_ROOT = "C:\tools\dotnet"

$python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$godot = "C:\Tools\Godot\Godot_v4.3-stable_mono_win64\Godot_v4.3-stable_mono_win64.exe"

if (-not (Test-Path $godot)) {
    Write-Host "Godot not found at $godot"
    exit 1
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

if ($ResetDb) {
    Write-Host "Resetting dev database before playtest..."
    & "$Root\scripts\reset_dev_db.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($RunCheck) {
    Write-Host "Running local checks before playtest..."
    & "$Root\scripts\check.ps1"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Building Godot C# project..."
Push-Location client
dotnet build city_economic_simulator.csproj -c Debug -v q
Pop-Location

& "$Root\scripts\start_backend.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Opening Godot project..."
Write-Host "Godot MCP: keep editor open for Cursor AI (MCP Connected top-right)."
Write-Host "Press F5 in Godot to play."
Start-Process $godot -ArgumentList @("--editor", "--path", "$Root\client")
