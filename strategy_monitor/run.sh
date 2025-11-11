#!/bin/bash
# Launch the Strategy Monitor UI

echo "Starting Hyperliquid Strategy Monitor..."
echo "The UI will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")"
streamlit run app.py
