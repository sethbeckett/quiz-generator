#!/bin/bash

# Quiz Generator Start Script
# This script starts both backend and frontend development servers

set -e

echo "🚀 Starting Quiz Generator development servers..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run setup.sh first."
    exit 1
fi

# Function to start backend
start_backend() {
    echo "🐍 Starting backend server..."
    cd backend
    source venv/bin/activate
    export $(cat ../.env | xargs)
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    echo "✅ Backend server started (PID: $BACKEND_PID)"
}

# Function to start frontend
start_frontend() {
    echo "⚛️  Starting frontend server..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Frontend server started (PID: $FRONTEND_PID)"
}

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "👋 Goodbye!"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Start servers
start_backend
sleep 2  # Give backend time to start
start_frontend

echo ""
echo "🎉 Both servers are starting!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user interrupt
wait
