#!/bin/bash
# Run Phase 2 Dashboard

echo "🚀 Starting Strategy Monitor - Phase 2 Dashboard"
echo "================================================"
echo ""
echo "Dashboard Features:"
echo "  - Real-time institutional positioning signals"
echo "  - Order book liquidity analysis"
echo "  - Whale tracking (5 addresses loaded)"
echo "  - Signal convergence alerts"
echo ""
echo "Access the dashboard at: http://localhost:8501"
echo ""

cd "$(dirname "$0")"
streamlit run app_phase2.py
