# 1-SMW ????????
# ??????????????

param(
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipNginx
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  1-SMW ??????" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---- Python ?? ----
if (-not $SkipPython) {
    Write-Host "[Python] ?? Python ??..." -ForegroundColor Yellow
    $pythonDir = "$ProjectRoot\offline-deps\python"
    if (Test-Path $pythonDir) {
        python -m venv "$ProjectRoot\.venv" 2>&1 | Out-Null
        if (Test-Path "$ProjectRoot\.venv\Scripts\pip.exe") {
            & "$ProjectRoot\.venv\Scripts\pip.exe" install --no-index --find-links $pythonDir -r "$ProjectRoot\backend\requirements.txt" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ? Python ??????" -ForegroundColor Green
            } else {
                Write-Host "  ? Python ?????????????..." -ForegroundColor Yellow
                & "$ProjectRoot\.venv\Scripts\pip.exe" install -r "$ProjectRoot\backend\requirements.txt" 2>&1
            }
        }
    } else {
        Write-Host "  ? ?????????: $pythonDir" -ForegroundColor Yellow
        Write-Host "  ??????..." -ForegroundColor Yellow
        python -m venv "$ProjectRoot\.venv" 2>&1 | Out-Null
        & "$ProjectRoot\.venv\Scripts\pip.exe" install -r "$ProjectRoot\backend\requirements.txt" 2>&1
    }
}

# ---- NPM ?? ----
if (-not $SkipNode) {
    Write-Host "[Node.js] ??????..." -ForegroundColor Yellow
    $frontendDir = "$ProjectRoot\frontend"
    if (Test-Path "$frontendDir\package.json") {
        Set-Location $frontendDir
        if (Test-Path "$frontendDir\node_modules") {
            Write-Host "  ? node_modules ??????" -ForegroundColor Green
        } else {
            npm install 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ? NPM ??????" -ForegroundColor Green
            } else {
                Write-Host "  ? NPM ??????" -ForegroundColor Red
            }
        }
        # ????
        Write-Host "[Node.js] ????..." -ForegroundColor Yellow
        npm run build 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ? ??????" -ForegroundColor Green
        } else {
            Write-Host "  ? ??????" -ForegroundColor Red
        }
    }
}

# ---- Nginx ----
if (-not $SkipNginx) {
    $nginxZip = "$ProjectRoot\offline-deps\nginx-1.26.2.zip"
    $nginxDir = "$ProjectRoot\nginx"
    if (-not (Test-Path $nginxDir)) {
        if (Test-Path $nginxZip) {
            Write-Host "[Nginx] ?? Nginx..." -ForegroundColor Yellow
            Expand-Archive -Path $nginxZip -DestinationPath "$ProjectRoot\temp-nginx" -Force
            Get-ChildItem "$ProjectRoot\temp-nginx\nginx-*" | Move-Item -Destination $nginxDir
            Remove-Item "$ProjectRoot\temp-nginx" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  ? Nginx ????" -ForegroundColor Green
        } else {
            Write-Host "  ? Nginx ????????????" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ? Nginx ?????" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ???????" -ForegroundColor Green
Write-Host "  ?? deploy\start-all.ps1 ????" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
