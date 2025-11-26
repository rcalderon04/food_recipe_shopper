# Quick activation script
# Run this to activate the virtual environment

& .\venv\Scripts\Activate.ps1

Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host "Python location: $(python -c 'import sys; print(sys.prefix)')" -ForegroundColor Cyan
