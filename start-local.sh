#!/bin/bash

# SEC Document Scraper - Local Development Startup Script
# This script starts both the Flask backend and React frontend for local development

echo "🚀 Starting SEC Document Scraper (Local Development)"
echo "=============================================="

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
kill -9 $(lsof -ti:3000,8080) 2>/dev/null || true
sleep 2

# Start Backend (Flask on port 8080)
echo "🐍 Starting Flask Backend (port 8080)..."
cd backend
python3 app.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8080/healthz > /dev/null; then
    echo "✅ Backend started successfully!"
else
    echo "❌ Backend failed to start. Check backend/backend.log for errors."
    exit 1
fi

# Start Frontend (React on port 3000)
echo "⚛️  Starting React Frontend (port 3000)..."
cd frontend
npm start > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to compile..."
sleep 10

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend started successfully!"
else
    echo "❌ Frontend failed to start. Check frontend/frontend.log for errors."
    exit 1
fi

echo ""
echo "🎉 SEC Document Scraper is running!"
echo "=============================================="
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8080"
echo "📊 Health:   http://localhost:8080/healthz"
echo ""
echo "📝 Process IDs:"
echo "   Backend PID:  $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "🛑 To stop services:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or run: kill -9 \$(lsof -ti:3000,8080)"
echo ""

# Auto-open browser (optional)
if command -v open &> /dev/null; then
    echo "🌐 Opening browser..."
    sleep 2
    open http://localhost:3000
fi

echo "✨ Ready to scrape SEC documents!" 