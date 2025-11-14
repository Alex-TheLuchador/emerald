#!/bin/bash
# Launch the Strategy Monitor UI (Legacy Version)
# Bash script for Linux/Mac

echo -e "\033[1;33m⚠️  DEPRECATED: This launches the legacy single-coin dashboard\033[0m"
echo -e "\033[1;32mFor the modern multi-coin dashboard, use: ./run_phase2.sh\033[0m"
echo ""
echo -e "\033[1;36mStarting Hyperliquid Strategy Monitor (Legacy)...\033[0m"
echo "The UI will open in your browser at http://localhost:8501"
echo ""
echo -e "\033[1;33mPress Ctrl+C to stop\033[0m"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Launch Streamlit
streamlit run app.py
