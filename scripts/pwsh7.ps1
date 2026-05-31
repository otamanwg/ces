param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"
$Pwsh = "C:\Tools\PowerShell\7.6.2\pwsh.exe"

if (-not (Test-Path $Pwsh)) {
    throw "PowerShell 7.6.2 not found at $Pwsh"
}

& $Pwsh @Arguments
exit $LASTEXITCODE
