# 1-SMW ?????? (????)
# ? Windows ????????????

param(
    [string]$NginxPort = "3201",
    [string]$BackendPort = "8000",
    [string]$SandboxPort = "3000"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
$NginxPath = "$ProjectRoot\nginx\nginx.exe"
$NginxConf = "$ProjectRoot\deploy\nginx.conf"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  1-SMW ???????? - ????" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---- Step 1: ?????? ----
Write-Host "[Step 1/4] ????..." -ForegroundColor Yellow
$ports = @($NginxPort, $BackendPort, $SandboxPort)
foreach ($p in $ports) {
    $conn = netstat -ano | Select-String ":$p\s+.*LISTENING"
    if ($conn) {
        Write-Host "  ? ?? $p ???????????????????" -ForegroundColor Red
    } else {
        Write-Host "  ? ?? $p ??" -ForegroundColor Green
    }
}

# ---- Step 2: ?????? ----
Write-Host "[Step 2/4] ????..." -ForegroundColor Yellow

# Python
$pyVer = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ? Python: $pyVer" -ForegroundColor Green
} else {
    Write-Host "  ? Python ???????? Python 3.11+" -ForegroundColor Red
    exit 1
}

# Node
$nodeVer = node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ? Node.js: $nodeVer" -ForegroundColor Green
} else {
    Write-Host "  ? Node.js ???????? Node.js 18+" -ForegroundColor Red
    exit 1
}

# Nginx
if (Test-Path $NginxPath) {
    Write-Host "  ? Nginx ??" -ForegroundColor Green
} else {
    Write-Host "  ? Nginx ??????????+???????" -ForegroundColor Yellow
}

# ---- Step 3: ???? ----
Write-Host "[Step 3/4] ??????..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($dir, $port)
    Set-Location $dir
    & ".\deploy\start-backend.ps1" -Port $port
} -ArgumentList $ProjectRoot, $BackendPort

Start-Sleep -Seconds 3
$backendStatus = Receive-Job -Job $backendJob
if ($backendStatus) { Write-Host $backendStatus }

# ---- Step 4: ?? Nginx ----
Write-Host "[Step 4/4] ?? Nginx ????..." -ForegroundColor Yellow
if (Test-Path $NginxPath) {
    $nginxLogs = "$ProjectRoot\nginx\logs"
    if (-not (Test-Path $nginxLogs)) { New-Item -ItemType Directory -Path $nginxLogs -Force | Out-Null }
    
    $proc = Start-Process -FilePath $NginxPath -ArgumentList "-c `"$NginxConf`" -p `"$ProjectRoot\nginx`"" -NoNewWindow -PassThru
    Start-Sleep -Seconds 1
    Write-Host "  ? Nginx ??? (PID: $($proc.Id))" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  1-SMW ??????" -ForegroundColor Green
Write-Host "  ????: http://localhost:$NginxPort" -ForegroundColor White
Write-Host "  ?? API: http://localhost:$BackendPort/api" -ForegroundColor Gray
if (Test-Path $NginxPath) {
    Write-Host "  ????: http://localhost:$NginxPort/sandbox/" -ForegroundColor Gray
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "? Ctrl+C ??????" -ForegroundColor Gray
Write-Host "?? Nginx: nginx -s stop (? nginx ???)" -ForegroundColor Gray

# ??????
Wait-Job -Job $backendJob | Out-Null
