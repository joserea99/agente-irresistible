#!/bin/bash
echo "=== IRRESISTIBLE AGENT STARTUP ==="
echo "PORT variable: $PORT"
echo "Starting Streamlit..."
python -m streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false
