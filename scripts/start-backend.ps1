$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run scripts\setup.ps1 or the README setup commands first.' }
    & '.\.venv\Scripts\python.exe' -m uvicorn revivegraph.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000 --reload --reload-dir backend
} finally { Pop-Location }
