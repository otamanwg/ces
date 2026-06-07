param(
    [string]$ScenePath = "res://scenes/city_dashboard.tscn",
    [int]$TimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$env:PATH = "C:\Tools\PowerShell\7.6.2;C:\tools\dotnet-sdk;C:\tools\MinGit\cmd;" + $env:PATH
$env:DOTNET_ROOT = "C:\tools\dotnet-sdk"

$godot = "C:\Tools\Godot\Godot_v4.3-stable_mono_win64\Godot_v4.3-stable_mono_win64.exe"
if (-not (Test-Path $godot)) {
    throw "Godot not found at $godot"
}

& "$Root\scripts\start_backend.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

function Get-McpStatus {
    try {
        return Invoke-RestMethod -Uri "http://127.0.0.1:6507/status" -TimeoutSec 5
    } catch {
        return $null
    }
}

& "$Root\scripts\start_godot_mcp_bridge.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$status = Get-McpStatus
if (-not $status -or -not $status.godot_connected) {
    $godotProcess = Get-Process | Where-Object { $_.ProcessName -match "Godot|godot" } | Select-Object -First 1
    if (-not $godotProcess) {
        Write-Host "Opening Godot editor for MCP smoke..."
        Start-Process $godot -ArgumentList @("--editor", "--path", "$Root\client")
    } else {
        Write-Host "Godot editor is already running; waiting for MCP connection..."
    }
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    $status = Get-McpStatus
    if ($status -and $status.godot_connected) {
        break
    }
    Start-Sleep -Seconds 1
}

$status = Get-McpStatus
if (-not $status -or -not $status.godot_connected) {
    Write-Host "Godot MCP did not connect within $TimeoutSeconds seconds."
    Write-Host "Bridge status:"
    if ($status) { $status | ConvertTo-Json -Depth 10 } else { Write-Host "unavailable" }
    Write-Host "Bridge stdout tail:"
    if (Test-Path ".tools\logs\godot-mcp-bridge.out.log") {
        Get-Content ".tools\logs\godot-mcp-bridge.out.log" -Tail 40
    }
    Write-Host "Bridge stderr tail:"
    if (Test-Path ".tools\logs\godot-mcp-bridge.err.log") {
        Get-Content ".tools\logs\godot-mcp-bridge.err.log" -Tail 40
    }
    exit 1
}

Write-Host "Godot MCP connected."

& "$Root\scripts\invoke_godot_mcp.ps1" -Tool clear_console_log -ArgsJson '{}' -TimeoutSeconds 20
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$Root\scripts\invoke_godot_mcp.ps1" -Tool get_errors -ArgsJson '{"include_warnings":true}' -TimeoutSeconds 20
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$Root\scripts\invoke_godot_mcp.ps1" -Tool run_scene -ArgsJson "{`"scene_path`":`"$ScenePath`"}" -TimeoutSeconds 30
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Start-Sleep -Seconds 5

$playStateJson = & "$Root\scripts\invoke_godot_mcp.ps1" -Tool is_playing -ArgsJson '{}' -TimeoutSeconds 20
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$playStateJson | Write-Output
$playState = $playStateJson | ConvertFrom-Json
if (-not $playState.success -or -not $playState.result.playing) {
    Write-Host "Godot reported run_scene success, but the dashboard is not playing."
    exit 1
}

& "$Root\scripts\invoke_godot_mcp.ps1" -Tool get_errors -ArgsJson '{"include_warnings":true}' -TimeoutSeconds 20
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$Root\scripts\invoke_godot_mcp.ps1" -Tool get_console_log -ArgsJson '{}' -TimeoutSeconds 20
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$Root\scripts\invoke_godot_mcp.ps1" -Tool stop_scene -ArgsJson '{}' -TimeoutSeconds 20
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Godot dashboard smoke passed."
