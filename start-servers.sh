#!/bin/bash

# SEC Document Scraper - Google Cloud Compute Engine Startup Script
# This script starts both the backend (Flask) and frontend (React) servers
# 
# Usage: ./start-servers.sh
# 
# Author: Brett Shaulson
# Last Updated: 2025-07-27

echo "🚀 Starting SEC Document Scraper on Google Cloud Compute Engine"
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
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check for required dependencies
echo -e "\n${BLUE}🔍 Checking dependencies...${NC}"

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Installing...${NC}"
    sudo apt update && sudo apt install -y python3 python3-pip
else
    echo -e "${GREEN}✅ Python3 found${NC}"
fi

# Check Node.js and npm
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ Node.js/npm not found. Installing...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo -e "${GREEN}✅ Node.js and npm found${NC}"
fi

# Check Google Cloud authentication
echo -e "\n${BLUE}🔐 Checking Google Cloud authentication...${NC}"
if gcloud auth application-default print-access-token &> /dev/null; then
    echo -e "${GREEN}✅ Google Cloud authentication configured${NC}"
else
    echo -e "${YELLOW}⚠️  Google Cloud authentication not configured${NC}"
    echo -e "${YELLOW}   Run: gcloud auth application-default login${NC}"
fi

# Start Backend (Flask)
echo -e "\n${BLUE}🐍 Starting Flask Backend...${NC}"
cd "$SCRIPT_DIR/backend"

# Check if backend port is already in use
if check_port 8080; then
    echo -e "${YELLOW}⚠️  Port 8080 already in use. Stopping existing process...${NC}"
    sudo pkill -f "python3 app.py" || true
    sleep 2
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

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
    exit 1
fi

# Start Frontend (React)
echo -e "\n${BLUE}⚛️  Starting React Frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

# Check if frontend port is already in use
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 already in use. Stopping existing process...${NC}"
    sudo pkill -f "react-scripts start" || true
    sleep 2
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Start frontend in background
echo "🚀 Starting React development server on port 3000..."
nohup npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment and check if frontend started successfully
sleep 5
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Frontend started successfully (PID: $FRONTEND_PID)${NC}"
    echo "📄 Frontend logs: $SCRIPT_DIR/frontend.log"
else
    echo -e "${RED}❌ Frontend failed to start. Check logs: $SCRIPT_DIR/frontend.log${NC}"
    exit 1
fi

# Get external IP
echo -e "\n${BLUE}🌐 Getting external IP address...${NC}"
EXTERNAL_IP=$(curl -s ifconfig.me)
INTERNAL_IP=$(hostname -I | awk '{print $1}')

echo -e "\n${GREEN}🎉 SEC Document Scraper is now running!${NC}"
echo "=================================================="
echo -e "${GREEN}Frontend:${NC} http://$EXTERNAL_IP:3000"
echo -e "${GREEN}Backend API:${NC} http://$EXTERNAL_IP:8080"
echo -e "${GREEN}Health Check:${NC} http://$EXTERNAL_IP:8080/healthz"
echo ""
echo -e "${BLUE}Internal Access:${NC}"
echo -e "Frontend: http://$INTERNAL_IP:3000"
echo -e "Backend: http://$INTERNAL_IP:8080"
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

# Make sure firewall rules allow the ports
echo -e "\n${BLUE}🔥 Checking firewall rules...${NC}"
if gcloud compute firewall-rules describe allow-frontend-3000 --project=sentiment-analysis-379200 &> /dev/null; then
    echo -e "${GREEN}✅ Frontend firewall rule exists${NC}"
else
    echo -e "${YELLOW}⚠️  Creating firewall rule for frontend (port 3000)...${NC}"
    gcloud compute firewall-rules create allow-frontend-3000 \
        --allow tcp:3000 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow React frontend access" \
        --project=sentiment-analysis-379200
fi

if gcloud compute firewall-rules describe allow-backend-8080 --project=sentiment-analysis-379200 &> /dev/null; then
    echo -e "${GREEN}✅ Backend firewall rule exists${NC}"
else
    echo -e "${YELLOW}⚠️  Creating firewall rule for backend (port 8080)...${NC}"
    gcloud compute firewall-rules create allow-backend-8080 \
        --allow tcp:8080 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow Flask backend access" \
        --project=sentiment-analysis-379200
fi

echo -e "\n${GREEN}✅ Setup complete! Your SEC Document Scraper is ready to use.${NC}" 
