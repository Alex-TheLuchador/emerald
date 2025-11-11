# Run Phase 2 Dashboard
# PowerShell script for Windows

Write-Host "🚀 Starting Strategy Monitor - Phase 2 Dashboard" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard Features:" -ForegroundColor Cyan
Write-Host "  - Real-time institutional positioning signals"
Write-Host "  - Order book liquidity analysis"
Write-Host "  - Whale tracking (5 addresses loaded)"
Write-Host "  - Signal convergence alerts"
Write-Host ""
Write-Host "Access the dashboard at: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Run Streamlit
streamlit run app_phase2.py
