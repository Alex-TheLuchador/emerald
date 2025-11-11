# Launch the Strategy Monitor UI
# PowerShell script for Windows

Write-Host "Starting Hyperliquid Strategy Monitor..." -ForegroundColor Cyan
Write-Host "The UI will open in your browser at http://localhost:8501"
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Launch Streamlit
streamlit run app.py
