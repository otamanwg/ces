param(
    [Parameter(Mandatory = $true)]
    [string]$Tool,

    [string]$ArgsJson = "{}",

    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
$body = @{
    tool = $Tool
    args = (ConvertFrom-Json $ArgsJson -AsHashtable)
    timeout = $TimeoutSeconds
} | ConvertTo-Json -Depth 20

Invoke-RestMethod `
    -Uri "http://127.0.0.1:6507/invoke" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $body |
    ConvertTo-Json -Depth 50
