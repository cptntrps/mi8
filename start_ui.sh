#!/bin/bash

# AgenticSeek UI Quick Start Script
# Launches FastAPI backend + Open WebUI integration

echo "🚀 Starting AgenticSeek Hybrid UI System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Create necessary directories
mkdir -p logs data nginx webui-config db

# Create nginx configuration
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream agenticsseek-api {
        server agenticsseek-api:8000;
    }
    
    upstream open-webui {
        server open-webui:8080;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # AgenticSeek API
        location /api/ {
            proxy_pass http://agenticsseek-api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # WebSocket support
        location /ws {
            proxy_pass http://agenticsseek-api/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
        
        # Open WebUI (default)
        location / {
            proxy_pass http://open-webui/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

# Create database initialization script
cat > db/init.sql << 'EOF'
-- AgenticSeek Database Schema
CREATE DATABASE IF NOT EXISTS agenticsseek;
USE agenticsseek;

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent sessions table  
CREATE TABLE agent_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    agent_type VARCHAR(100) NOT NULL,
    session_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent logs table
CREATE TABLE agent_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    agent_type VARCHAR(100) NOT NULL,
    request_data JSONB,
    response_data JSONB,
    execution_time FLOAT,
    success BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

echo "📦 Installing Python dependencies..."
cd api && pip install -r requirements.txt && cd ..

echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check API health
API_HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "unhealthy")
if [ "$API_HEALTH" = "healthy" ]; then
    echo "✅ AgenticSeek API is healthy"
else
    echo "⚠️ AgenticSeek API may still be starting..."
fi

# Check WebUI
WEBUI_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$WEBUI_HEALTH" = "200" ]; then
    echo "✅ Open WebUI is accessible"
else
    echo "⚠️ Open WebUI may still be starting..."
fi

echo ""
echo "🎉 AgenticSeek Hybrid UI System Started!"
echo ""
echo "📱 Access Points:"
echo "   🌐 Open WebUI (Chat):       http://localhost:3000"
echo "   🔧 AgenticSeek API:         http://localhost:8000"
echo "   📊 API Documentation:       http://localhost:8000/docs"
echo "   🎤 WebSocket Test:           ws://localhost:8000/ws"
echo ""
echo "🤖 Available Models in Open WebUI:"
echo "   • agenticsseek-enhanced     (General purpose)"
echo "   • agenticsseek-database     (Database operations)"
echo "   • agenticsseek-voice        (Voice enabled)"
echo ""
echo "💡 Quick Test Commands:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/v1/models"
echo "   curl http://localhost:8000/agents"
echo ""
echo "📋 To stop the system:"
echo "   docker-compose down"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Create an account in Open WebUI"
echo "   3. Select an AgenticSeek model"
echo "   4. Start chatting with your agents!"
echo ""

# Show running containers
echo "🐳 Running Containers:"
docker-compose ps