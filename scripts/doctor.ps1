param(
    [switch]$RequireDocker,
    [switch]$RequireGodotMcp
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$failures = 0

function Write-Check([string]$Name, [bool]$Healthy, [string]$Detail) {
    $status = if ($Healthy) { "OK" } else { "FAIL" }
    Write-Host ("[{0}] {1}: {2}" -f $status, $Name, $Detail)
    if (-not $Healthy) {
        $script:failures++
    }
}

$requiredTools = [ordered]@{
    "PowerShell 7" = "C:\Tools\PowerShell\7.6.2\pwsh.exe"
    ".NET SDK" = "C:\Tools\dotnet-sdk\dotnet.exe"
    "Godot 4.3" = "C:\Tools\Godot\Godot_v4.3-stable_mono_win64\Godot_v4.3-stable_mono_win64.exe"
    "Git" = "C:\Tools\MinGit\cmd\git.exe"
    "just" = "C:\Tools\just\just.exe"
    "Node.js" = "C:\Tools\nodejs\node.exe"
    "uv" = "C:\Users\agga\.local\bin\uv.exe"
    "Python venv" = "$Root\.venv\Scripts\python.exe"
}

foreach ($tool in $requiredTools.GetEnumerator()) {
    Write-Check $tool.Key (Test-Path $tool.Value) $tool.Value
}

$postgresReady = Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet
Write-Check "PostgreSQL" $postgresReady "127.0.0.1:5432"

$dockerReady = $false
try {
    docker info *> $null
    $dockerReady = $LASTEXITCODE -eq 0
} catch {
    $dockerReady = $false
}
if ($RequireDocker) {
    Write-Check "Docker daemon" $dockerReady "Docker Desktop Linux engine"
} else {
    Write-Host ("[{0}] Docker daemon: optional" -f $(if ($dockerReady) { "OK" } else { "WARN" }))
}

$mcpReady = $false
try {
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:6507/status" -TimeoutSec 2
    $mcpReady = [bool]$status.godot_connected
} catch {
    $mcpReady = $false
}
if ($RequireGodotMcp) {
    Write-Check "Godot MCP" $mcpReady "http://127.0.0.1:6507/status"
} else {
    Write-Host ("[{0}] Godot MCP: optional" -f $(if ($mcpReady) { "OK" } else { "WARN" }))
}

if ($failures -gt 0) {
    Write-Host "Doctor found $failures required issue(s)."
    exit 1
}

Write-Host "Doctor checks passed."
