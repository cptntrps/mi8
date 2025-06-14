#!/usr/bin/env python3
"""
Simplified AgenticSeek FastAPI Backend for Demo
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from sources.agents.enhanced_mcp_agent import EnhancedMCPAgent
    from sources.agents.database_agent import DatabaseAgent
    from sources.utility import pretty_print
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"Agent imports failed: {e}")
    AGENTS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instances
agents: Dict[str, Any] = {}
active_connections: List[WebSocket] = []

# Initialize FastAPI app
app = FastAPI(
    title="AgenticSeek API",
    description="RESTful API for AgenticSeek multi-agent system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AgentRequest(BaseModel):
    prompt: str
    agent_type: str = "enhanced_mcp"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    global agents
    
    logger.info("🚀 Starting AgenticSeek API...")
    
    if AGENTS_AVAILABLE:
        try:
            # Initialize mock agents for demo
            agents["enhanced_mcp"] = {
                "name": "Enhanced MCP Agent",
                "status": "✅ Ready - MCP tools available",
                "type": "enhanced_mcp"
            }
            
            agents["database"] = {
                "name": "Database Agent", 
                "status": "✅ Ready - SQL operations available",
                "type": "database"
            }
            
            logger.info("✅ Mock agents initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            # Continue with mock data
    else:
        # Mock agents for demo
        agents["enhanced_mcp"] = {
            "name": "Enhanced MCP Agent",
            "status": "⚠️ Demo mode - Limited functionality",
            "type": "enhanced_mcp"
        }

@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "AgenticSeek API is running",
        "version": "1.0.0",
        "agents": list(agents.keys()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents": {name: "running" for name in agents.keys()},
        "websocket_connections": len(active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/agents")
async def list_agents():
    """List available agents"""
    return list(agents.keys())

@app.get("/agents/{agent_type}/status")
async def get_agent_status(agent_type: str):
    """Get agent status"""
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent_info = agents[agent_type]
    return {
        "agent_type": agent_type,
        "name": agent_info["name"],
        "status": agent_info["status"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/agents/{agent_type}/execute")
async def execute_agent_request(agent_type: str, request: AgentRequest):
    """Execute request on specified agent"""
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Mock response for demo
    response_text = f"Agent {agent_type} processed: {request.prompt}\n\n"
    
    if "database" in request.prompt.lower():
        response_text += "🗄️ Database operations available:\n"
        response_text += "- Connect to databases (SQLite, MySQL, PostgreSQL)\n"
        response_text += "- Execute SQL queries with optimization\n"
        response_text += "- Analyze table schemas and relationships\n"
        
    elif "voice" in request.prompt.lower():
        response_text += "🎤 Voice features available:\n"
        response_text += "- 'AgenticSeek connect to database'\n"
        response_text += "- 'AgenticSeek list all tables'\n"
        response_text += "- 'AgenticSeek open main.py in cursor'\n"
        
    elif "cursor" in request.prompt.lower() or "file" in request.prompt.lower():
        response_text += "📝 File operations available:\n"
        response_text += "- Open files in Cursor IDE\n"
        response_text += "- Create and modify files\n"
        response_text += "- Search project files\n"
        
    else:
        response_text += "✅ Enhanced MCP Agent capabilities:\n"
        response_text += "- Database operations and SQL analysis\n"
        response_text += "- File system operations\n"
        response_text += "- Memory management\n"
        response_text += "- Voice command processing\n"
        response_text += "- Real-time file monitoring\n"
    
    # Notify WebSocket clients
    await notify_websocket_clients({
        "type": "agent_execution",
        "agent_type": agent_type,
        "prompt": request.prompt,
        "response": response_text
    })
    
    return {
        "success": True,
        "response": response_text,
        "agent_type": agent_type,
        "timestamp": datetime.now().isoformat()
    }

# OpenAI compatibility endpoints
@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint"""
    models = [
        {
            "id": "agenticsseek-enhanced",
            "object": "model",
            "created": 1699999999,
            "owned_by": "agenticsseek"
        },
        {
            "id": "agenticsseek-database", 
            "object": "model",
            "created": 1699999999,
            "owned_by": "agenticsseek"
        }
    ]
    
    return {"object": "list", "data": models}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, authorization: Optional[str] = Header(None)):
    """OpenAI-compatible chat completions"""
    
    # Extract user message
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    user_prompt = user_messages[-1].content
    
    # Route to appropriate agent
    agent_type = "enhanced_mcp"
    if "database" in request.model:
        agent_type = "database"
    
    # Generate response
    if "hello" in user_prompt.lower():
        response_text = f"Hello! I'm the {request.model} agent. I'm ready to help you with:\n"
        response_text += "• Database operations and SQL queries\n"
        response_text += "• File management and Cursor IDE integration\n" 
        response_text += "• Voice commands and audio processing\n"
        response_text += "• Memory management and context tracking\n\n"
        response_text += "Try asking me to 'connect to database' or 'open a file in cursor'!"
    else:
        # Use the existing agent execution logic
        mock_request = AgentRequest(prompt=user_prompt, agent_type=agent_type)
        result = await execute_agent_request(agent_type, mock_request)
        response_text = result["response"]
    
    return {
        "id": f"chatcmpl-demo-{datetime.now().timestamp()}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(user_prompt.split()),
            "completion_tokens": len(response_text.split()),
            "total_tokens": len(user_prompt.split()) + len(response_text.split())
        }
    }

# Database operations (mock for demo)
@app.post("/database/connect")
async def database_connect(db_type: str = "sqlite", database: str = "demo.db"):
    """Mock database connection"""
    return {
        "success": True,
        "message": f"✅ Connected to {db_type} database: {database}",
        "connection_id": "demo-connection-123"
    }

@app.post("/database/query")
async def database_query():
    """Mock database query"""
    return {
        "success": True,
        "result": "🗄️ Mock query executed successfully\n\nSample data:\n[\n  {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},\n  {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}\n]"
    }

@app.get("/database/tables")
async def database_list_tables():
    """Mock table listing"""
    return {
        "success": True,
        "tables": "📋 Found 3 tables:\n- users\n- products\n- orders"
    }

# Voice control (mock for demo)
@app.post("/voice/control")
async def voice_control(action: str = "start"):
    """Mock voice control"""
    if action == "start":
        return {
            "success": True,
            "result": "🎤 Voice control started. Say 'AgenticSeek' to activate commands."
        }
    else:
        return {
            "success": True,
            "result": "🔇 Voice control stopped."
        }

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "WebSocket connected to AgenticSeek API",
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

async def notify_websocket_clients(message: dict):
    """Send message to all connected WebSocket clients"""
    if not active_connections:
        return
    
    message["timestamp"] = datetime.now().isoformat()
    message_json = json.dumps(message)
    
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(message_json)
        except Exception:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for connection in disconnected:
        if connection in active_connections:
            active_connections.remove(connection)

if __name__ == "__main__":
    print("🚀 Starting AgenticSeek API Demo Server...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0", 
        port=8000,
        reload=False,
        log_level="info"
    )