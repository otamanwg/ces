param(
    [string]$OutputPath = "",
    [string]$BlendPath = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$blender = "C:\Tools\Blender\blender-4.5.4-windows-x64\blender.exe"
if (-not (Test-Path $blender)) {
    throw "Portable Blender 4.5.4 LTS not found at $blender"
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $Root "client\assets\visual\anime\avatar\canonical_anime_avatar.glb"
}
if ([string]::IsNullOrWhiteSpace($BlendPath)) {
    $BlendPath = Join-Path $Root ".tools\blender\canonical_anime_avatar.blend"
}

$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$BlendPath = [System.IO.Path]::GetFullPath($BlendPath)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BlendPath) | Out-Null

& $blender `
    --background `
    --factory-startup `
    --python "$Root\tools\blender\generate_canonical_anime_avatar.py" `
    -- `
    --output $OutputPath `
    --blend $BlendPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not (Test-Path $OutputPath)) {
    throw "Canonical anime avatar was not created at $OutputPath"
}

$bytes = [System.IO.File]::ReadAllBytes($OutputPath)
$glbSignature = [System.Text.Encoding]::ASCII.GetString($bytes, 0, 4)
if ($bytes.Length -lt 10240 -or $glbSignature -ne "glTF") {
    throw "Generated avatar is not a valid non-empty GLB: $OutputPath"
}

Write-Host "Canonical anime avatar generated: $OutputPath"
Write-Output $OutputPath
