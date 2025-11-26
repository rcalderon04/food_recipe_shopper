# Shopping List Tool - Setup Script
# This script activates the virtual environment and installs dependencies

Write-Host "Shopping List Tool - Environment Setup" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt

# Install Playwright browsers
Write-Host ""
Write-Host "Installing Playwright browsers (this may take a minute)..." -ForegroundColor Yellow
python -m playwright install chromium

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To use the tool:" -ForegroundColor Cyan
Write-Host "  1. Activate venv: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Run test: python test_run.py" -ForegroundColor White
Write-Host "  3. Run full tool: python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Virtual environment is now active in this session." -ForegroundColor Green
