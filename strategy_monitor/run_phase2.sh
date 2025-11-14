#!/bin/bash
# Run Phase 2 Dashboard (Production Version)
# Bash script for Linux/Mac

echo -e "\033[1;32m🚀 Starting Strategy Monitor - Phase 2 Dashboard\033[0m"
echo -e "\033[1;32m================================================\033[0m"
echo ""
echo -e "\033[1;36mDashboard Features:\033[0m"
echo "  - Real-time institutional positioning signals"
echo "  - Order book liquidity analysis"
echo "  - Whale tracking (5 addresses loaded)"
echo "  - Signal convergence alerts"
echo ""
echo -e "\033[1;33mAccess the dashboard at: http://localhost:8501\033[0m"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Run Streamlit
streamlit run app_phase2.py
