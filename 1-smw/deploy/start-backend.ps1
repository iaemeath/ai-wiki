# 1-SMW ??????
# ? Windows ??????

param(
    [string]$Port = "8000",
    [string]$AIEndpoint = "http://localhost:19090/api/anthropic/v1/messages",
    [string]$AIKey = "caf4bb9dfcec493fa61e7efb2ac37bb3",
    [string]$AIModel = "glm-5.2"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
$VenvDir = "$ProjectRoot\.venv"

# ??????
if (-not (Test-Path "$VenvDir\Scripts\python.exe")) {
    Write-Host "[1-SMW] ?? Python ????..." -ForegroundColor Cyan
    python -m venv $VenvDir
    Write-Host "[1-SMW] ???? (????)..." -ForegroundColor Cyan
    & "$VenvDir\Scripts\pip.exe" install --no-index --find-links "$ProjectRoot\offline-deps\python" -r "$ProjectRoot\backend\requirements.txt"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[1-SMW] ?????????????..." -ForegroundColor Yellow
        & "$VenvDir\Scripts\pip.exe" install -r "$ProjectRoot\backend\requirements.txt"
    }
}

# ??????
$env:AI_GATEWAY_URL = $AIEndpoint
$env:AI_API_KEY = $AIKey
$env:AI_MODEL = $AIModel
$env:SMW_STORAGE_DIR = "$ProjectRoot\data"

# ????????
if (-not (Test-Path "$ProjectRoot\data")) {
    New-Item -ItemType Directory -Path "$ProjectRoot\data" -Force | Out-Null
}

Write-Host "[1-SMW] ?????? (?? $Port)..." -ForegroundColor Green
Write-Host "[1-SMW] AI ??: $AIEndpoint" -ForegroundColor Gray
Write-Host "[1-SMW] AI ??: $AIModel" -ForegroundColor Gray

# ?? FastAPI
& "$VenvDir\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port $Port --reload --log-level info
