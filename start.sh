#!/bin/bash

# Function to kill processes on exit
cleanup() {
    echo "Shutting down..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

trap cleanup SIGINT

# Start Backend
echo "🚀 Starting Backend on port 8000..."
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 5

# Start Frontend
echo "✨ Starting Frontend on port 3000..."
cd frontend
npm run dev -- -p 3000 &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
