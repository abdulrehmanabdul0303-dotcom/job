# JobPilot AI Backend - Production Readiness Verification Script
# Run this script to verify all production readiness checks

param(
    [switch]$Quick = $false,
    [switch]$Full = $false
)

$PythonPath = "C:\Users\REHMAN\AppData\Local\Programs\Python\Python311\python.exe"
$ApiPath = "D:\idea\jobpilot-ai\apps\api"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JobPilot AI - Production Readiness Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check 1: Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = & $PythonPath --version
Write-Host "  $pythonVersion" -ForegroundColor Green

# Check 2: Pytest version
Write-Host "[2/6] Checking pytest version..." -ForegroundColor Yellow
$pytestVersion = & $PythonPath -m pytest --version
Write-Host "  $pytestVersion" -ForegroundColor Green

# Check 3: Run QA Tests
Write-Host "[3/6] Running QA Test Suite..." -ForegroundColor Yellow
Push-Location $ApiPath
Remove-Item -Force jobpilot_test.db -ErrorAction SilentlyContinue

if ($Quick) {
    Write-Host "  Running QUICK mode (core suites only)..." -ForegroundColor Cyan
    & $PythonPath run_qa_tests.py --quick 2>&1 | Select-Object -Last 10
} elseif ($Full) {
    Write-Host "  Running FULL mode (including E2E)..." -ForegroundColor Cyan
    & $PythonPath run_qa_tests.py 2>&1 | Select-Object -Last 10
} else {
    Write-Host "  Running QUICK mode (default)..." -ForegroundColor Cyan
    & $PythonPath run_qa_tests.py --quick 2>&1 | Select-Object -Last 10
}

# Check 4: Core test suites
Write-Host "[4/6] Verifying core test suites..." -ForegroundColor Yellow
$suites = @(
    "tests/test_config.py",
    "tests/test_auth.py",
    "tests/test_security.py",
    "tests/test_resume_comprehensive.py",
    "tests/test_ai_features.py"
)

foreach ($suite in $suites) {
    $result = & $PythonPath -m pytest $suite -q --tb=line 2>&1 | Select-Object -Last 1
    Write-Host "  $suite: $result" -ForegroundColor Green
}

# Check 5: Security checks
Write-Host "[5/6] Running security checks..." -ForegroundColor Yellow
Write-Host "  Checking for hardcoded secrets..." -ForegroundColor Cyan
$secrets = Select-String -Path "app/core/config.py" -Pattern "secret.*=" | Select-Object -First 3
if ($secrets) {
    Write-Host "  [WARNING] Found potential hardcoded secrets:" -ForegroundColor Yellow
    $secrets | ForEach-Object { Write-Host "    $_" }
} else {
    Write-Host "  [OK] No obvious hardcoded secrets found" -ForegroundColor Green
}

# Check 6: Docker readiness
Write-Host "[6/6] Checking Docker readiness..." -ForegroundColor Yellow
if (Test-Path "infra/docker-compose.yml") {
    Write-Host "  [OK] docker-compose.yml found" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] docker-compose.yml not found" -ForegroundColor Red
}

if (Test-Path ".env.example") {
    Write-Host "  [OK] .env.example found" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] .env.example not found" -ForegroundColor Red
}

Pop-Location

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Production Readiness Check Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review PRODUCTION_READINESS_REPORT.md" -ForegroundColor White
Write-Host "2. Review RELEASE_HARDENING_PLAN.md" -ForegroundColor White
Write-Host "3. Deploy to production with confidence!" -ForegroundColor White
Write-Host ""
