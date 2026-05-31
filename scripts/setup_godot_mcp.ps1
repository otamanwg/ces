# Install Godot MCP plugin + portable Node for Cursor MCP (Windows)
# Usage: .\scripts\setup_godot_mcp.ps1

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$toolsDir = Join-Path $Root ".tools"
$zipPath = Join-Path $toolsDir "godot-mcp.zip"
$extractDir = Join-Path $toolsDir "godot-mcp-src"
$addonDest = Join-Path $Root "client\addons\godot_mcp"
$repoUrl = "https://github.com/colinfizgig/godot-mcp/archive/refs/heads/main.zip"
$nodeVersion = "v22.14.0"
$nodeZip = Join-Path $toolsDir "node-$nodeVersion-win-x64.zip"
$nodeDir = Join-Path $toolsDir "node"
$nodeUrl = "https://nodejs.org/dist/$nodeVersion/node-$nodeVersion-win-x64.zip"
$npxCmd = Join-Path $nodeDir "npx.cmd"
$mcpJsonPath = Join-Path $Root ".cursor\mcp.json"
$clientPath = Join-Path $Root "client"

New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $mcpJsonPath) | Out-Null

if (-not (Test-Path $addonDest)) {
    Write-Host "Downloading godot-mcp addon..."
    Invoke-WebRequest -Uri $repoUrl -OutFile $zipPath -UseBasicParsing
    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    Expand-Archive -Path $zipPath -DestinationPath $toolsDir -Force
    $srcRoot = Get-ChildItem $toolsDir -Directory | Where-Object { $_.Name -like "godot-mcp-*" } | Select-Object -First 1
    if (-not $srcRoot) {
        throw "Extracted folder not found."
    }
    Write-Host "Installing Godot addon -> client/addons/godot_mcp"
    Copy-Item -Recurse (Join-Path $srcRoot.FullName "addons\godot_mcp") $addonDest
} else {
    Write-Host "Godot addon already present."
}

if (-not (Test-Path $npxCmd)) {
    Write-Host "Downloading portable Node.js $nodeVersion..."
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeZip -UseBasicParsing
    if (Test-Path $nodeDir) {
        Remove-Item -Recurse -Force $nodeDir
    }
    Expand-Archive -Path $nodeZip -DestinationPath $toolsDir -Force
    Rename-Item (Join-Path $toolsDir "node-$nodeVersion-win-x64") "node"
}

$npxForJson = ($npxCmd -replace '\\', '\\')
$clientForJson = ($clientPath -replace '\\', '\\')

$mcpConfig = @"
{
  "mcpServers": {
    "godot": {
      "command": "$npxForJson",
      "args": ["-y", "godot-mcp-server"],
      "env": {
        "GODOT_PROJECT_PATH": "$clientForJson"
      }
    }
  }
}
"@

Set-Content -Path $mcpJsonPath -Value $mcpConfig -Encoding UTF8
Write-Host "Wrote $mcpJsonPath"

Write-Host ""
Write-Host "Setup complete. Required once per machine:"
Write-Host "  1. Restart Cursor (loads MCP from .cursor/mcp.json)"
Write-Host "  2. Open Godot from repo root: .\scripts\play.ps1"
Write-Host "  3. Plugin enabled in project.godot; Restart Project in Godot"
Write-Host "  4. Top-right in Godot: MCP Connected (green)"
Write-Host "  5. Cursor Settings -> Tools & MCP -> godot should be green"
