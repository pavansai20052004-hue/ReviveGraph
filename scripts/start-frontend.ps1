$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try { npm --prefix frontend run dev } finally { Pop-Location }
