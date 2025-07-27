#!/bin/bash

# SEC Document Scraper - Local Development Startup Script
# This script starts both the backend (Flask) and frontend (React) servers for local development
# 
# Usage: ./start-local.sh
# 
# Author: AI Assistant
# Last Updated: 2025-07-27

echo "🚀 Starting SEC Document Scraper (Local Development)"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "📁 Working directory: $SCRIPT_DIR"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes without sudo
kill_port_processes() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "  Stopping processes on port $port..."
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Check for required dependencies
echo -e "\n${BLUE}🔍 Checking dependencies...${NC}"

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.7+${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python3 found${NC}"
fi

# Check Node.js and npm
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Node.js/npm not found. Please install Node.js 14+${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Node.js and npm found${NC}"
fi

# Check Google Cloud authentication (optional for local dev)
echo -e "\n${BLUE}🔐 Checking Google Cloud authentication...${NC}"
if gcloud auth application-default print-access-token &> /dev/null; then
    echo -e "${GREEN}✅ Google Cloud authentication configured${NC}"
else
    echo -e "${YELLOW}⚠️  Google Cloud authentication not configured${NC}"
    echo -e "${YELLOW}   This is OK for local development. Firestore features may not work.${NC}"
    echo -e "${YELLOW}   To enable: gcloud auth application-default login${NC}"
fi

# Start Backend (Flask)
echo -e "\n${BLUE}🐍 Starting Flask Backend...${NC}"
cd "$SCRIPT_DIR/backend"

# Check if backend port is already in use
if check_port 8080; then
    echo -e "${YELLOW}⚠️  Port 8080 already in use. Stopping existing process...${NC}"
    kill_port_processes 8080
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt --quiet

# Start backend in background
echo "🚀 Starting Flask server on port 8080..."
nohup python3 app.py > ../backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment and check if backend started successfully
sleep 3
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend started successfully (PID: $BACKEND_PID)${NC}"
    echo "📄 Backend logs: $SCRIPT_DIR/backend.log"
else
    echo -e "${RED}❌ Backend failed to start. Check logs: $SCRIPT_DIR/backend.log${NC}"
    cat "$SCRIPT_DIR/backend.log"
    exit 1
fi

# Start Frontend (React)
echo -e "\n${BLUE}⚛️  Starting React Frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

# Check if frontend port is already in use
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 already in use. Stopping existing process...${NC}"
    kill_port_processes 3000
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install --silent

# Start frontend in background
echo "🚀 Starting React development server on port 3000..."
nohup npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment and check if frontend started successfully
sleep 8
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Frontend started successfully (PID: $FRONTEND_PID)${NC}"
    echo "📄 Frontend logs: $SCRIPT_DIR/frontend.log"
else
    echo -e "${RED}❌ Frontend failed to start. Check logs: $SCRIPT_DIR/frontend.log${NC}"
    cat "$SCRIPT_DIR/frontend.log"
    exit 1
fi

# Get local IP addresses
LOCAL_IP="127.0.0.1"
NETWORK_IP=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)

echo -e "\n${GREEN}🎉 SEC Document Scraper is now running locally!${NC}"
echo "=================================================="
echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
echo -e "${GREEN}Backend API:${NC} http://localhost:8080"
echo -e "${GREEN}Health Check:${NC} http://localhost:8080/healthz"

if [ -n "$NETWORK_IP" ]; then
    echo ""
    echo -e "${BLUE}Network Access:${NC}"
    echo -e "Frontend: http://$NETWORK_IP:3000"
    echo -e "Backend: http://$NETWORK_IP:8080"
fi

echo ""
echo -e "${YELLOW}Process IDs:${NC}"
echo -e "Backend PID: $BACKEND_PID"
echo -e "Frontend PID: $FRONTEND_PID"
echo ""
echo -e "${BLUE}To stop the servers:${NC}"
echo "kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo -e "${BLUE}Log files:${NC}"
echo "Backend: $SCRIPT_DIR/backend.log"
echo "Frontend: $SCRIPT_DIR/frontend.log"
echo ""
echo -e "${BLUE}Monitor logs:${NC}"
echo "tail -f backend.log frontend.log"

echo -e "\n${GREEN}✅ Setup complete! Open http://localhost:3000 in your browser.${NC}"

# Auto-open browser on macOS
if command -v open &> /dev/null; then
    echo "🌐 Opening browser..."
    sleep 2
    open http://localhost:3000
fi 