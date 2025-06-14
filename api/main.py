#!/usr/bin/env python3
"""
AgenticSeek FastAPI Backend
RESTful API for AgenticSeek agent ecosystem with real-time WebSocket support
"""

import os
import sys
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sources.agents.enhanced_mcp_agent import EnhancedMCPAgent
from sources.agents.database_agent import DatabaseAgent
from sources.utility import pretty_print
from openai_compatibility import add_openai_compatibility

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instances
agents: Dict[str, Any] = {}
active_connections: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup agents"""
    try:
        # Initialize agents
        logger.info("🚀 Initializing AgenticSeek agents...")
        
        agents["enhanced_mcp"] = EnhancedMCPAgent(
            "Enhanced MCP Agent",
            "prompts/base/mcp_agent.txt",
            None,  # No LLM provider for API mode
            verbose=True,
            voice_enabled=True
        )
        
        agents["database"] = DatabaseAgent(
            "Database Agent", 
            "prompts/base/database_agent.txt",
            None,
            verbose=True,
            voice_enabled=True
        )
        
        logger.info("✅ Agents initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize agents: {e}")
        yield
    finally:
        # Cleanup
        logger.info("🔄 Shutting down agents...")
        for agent_name, agent in agents.items():
            try:
                if hasattr(agent, 'shutdown'):
                    agent.shutdown()
                if hasattr(agent, 'stop_voice_control'):
                    agent.stop_voice_control()
            except Exception as e:
                logger.error(f"Error shutting down {agent_name}: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="AgenticSeek API",
    description="RESTful API for AgenticSeek multi-agent system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add OpenAI API compatibility
add_openai_compatibility(app)

# Security
security = HTTPBearer(auto_error=False)

# Pydantic models
class AgentRequest(BaseModel):
    prompt: str
    agent_type: str = "enhanced_mcp"
    parameters: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    success: bool
    response: str
    agent_type: str
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.now)

class DatabaseRequest(BaseModel):
    action: str  # connect, query, list_tables, etc.
    connection_id: Optional[str] = None
    parameters: Dict[str, Any] = {}

class VoiceRequest(BaseModel):
    action: str  # start_listening, stop_listening, etc.
    agent_type: str = "enhanced_mcp"

class AgentStatus(BaseModel):
    agent_type: str
    status: str
    uptime: float
    requests_handled: int
    last_activity: datetime

# Authentication dependency (simplified for demo)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple token validation - implement proper auth for production"""
    if credentials is None:
        return {"user_id": "anonymous", "permissions": ["read"]}
    
    # TODO: Implement proper JWT validation
    return {"user_id": "demo_user", "permissions": ["read", "write", "admin"]}

# Agent management endpoints
@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "AgenticSeek API is running",
        "version": "1.0.0",
        "agents": list(agents.keys()),
        "timestamp": datetime.now()
    }

@app.get("/agents", response_model=List[str])
async def list_agents(user: dict = Depends(get_current_user)):
    """List available agents"""
    return list(agents.keys())

@app.get("/agents/{agent_type}/status")
async def get_agent_status(agent_type: str, user: dict = Depends(get_current_user)):
    """Get agent status and capabilities"""
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents[agent_type]
    
    try:
        # Get agent-specific status
        if hasattr(agent, 'get_mcp_status'):
            status = agent.get_mcp_status()
        else:
            status = "Agent running"
        
        # Get voice status if available
        voice_status = None
        if hasattr(agent, 'get_voice_status'):
            voice_status = agent.get_voice_status()
        
        return {
            "agent_type": agent_type,
            "status": status,
            "voice_enabled": hasattr(agent, 'voice_enabled') and agent.voice_enabled,
            "voice_status": voice_status,
            "available_tools": getattr(agent, 'available_tools', {}),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting status for {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/{agent_type}/execute", response_model=AgentResponse)
async def execute_agent_request(
    agent_type: str, 
    request: AgentRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """Execute request on specified agent"""
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents[agent_type]
    start_time = datetime.now()
    
    try:
        # Execute the request
        if hasattr(agent, 'run'):
            result = await agent.run(request.prompt)
            response_text = result.result if hasattr(result, 'result') else str(result)
            success = result.success if hasattr(result, 'success') else True
        else:
            # Fallback for simple agents
            response_text = f"Agent {agent_type} processed: {request.prompt}"
            success = True
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Notify WebSocket connections
        background_tasks.add_task(
            notify_websocket_clients,
            {
                "type": "agent_execution",
                "agent_type": agent_type,
                "prompt": request.prompt,
                "response": response_text,
                "success": success,
                "execution_time": execution_time
            }
        )
        
        return AgentResponse(
            success=success,
            response=response_text,
            agent_type=agent_type,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error executing request on {agent_type}: {e}")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgentResponse(
            success=False,
            response=f"Error: {str(e)}",
            agent_type=agent_type,
            execution_time=execution_time
        )

# Database agent specific endpoints
@app.post("/database/connect")
async def database_connect(
    db_type: str,
    database: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Connect to database"""
    if "database" not in agents:
        raise HTTPException(status_code=404, detail="Database agent not available")
    
    try:
        db_agent = agents["database"]
        kwargs = {}
        if host: kwargs["host"] = host
        if port: kwargs["port"] = port
        if username: kwargs["username"] = username
        if password: kwargs["password"] = password
        
        result = db_agent.connect_to_database(db_type, database, **kwargs)
        
        return {"success": True, "message": result}
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/database/query")
async def database_query(
    connection_id: str,
    query: str,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Execute SQL query"""
    if "database" not in agents:
        raise HTTPException(status_code=404, detail="Database agent not available")
    
    try:
        db_agent = agents["database"]
        result = db_agent.execute_sql_query(connection_id, query, limit=limit)
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Database query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database/tables")
async def database_list_tables(
    connection_id: str,
    user: dict = Depends(get_current_user)
):
    """List database tables"""
    if "database" not in agents:
        raise HTTPException(status_code=404, detail="Database agent not available")
    
    try:
        db_agent = agents["database"]
        result = db_agent.list_database_tables(connection_id)
        
        return {"success": True, "tables": result}
    except Exception as e:
        logger.error(f"Database list tables error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Voice control endpoints
@app.post("/voice/control")
async def voice_control(
    action: str,
    agent_type: str = "enhanced_mcp",
    user: dict = Depends(get_current_user)
):
    """Control voice features"""
    if agent_type not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents[agent_type]
    
    if not hasattr(agent, 'voice_enabled') or not agent.voice_enabled:
        raise HTTPException(status_code=400, detail="Voice not enabled for this agent")
    
    try:
        if action == "start":
            result = agent.start_voice_control()
        elif action == "stop":
            result = agent.stop_voice_control()
        elif action == "toggle_mode":
            result = agent.toggle_voice_mode()
        elif action == "status":
            result = agent.get_voice_status()
        else:
            raise HTTPException(status_code=400, detail="Invalid voice action")
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Voice control error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                # Subscribe to specific agent updates
                await websocket.send_text(json.dumps({
                    "type": "subscription_confirmed",
                    "agent": message.get("agent"),
                    "timestamp": datetime.now().isoformat()
                }))
            elif message.get("type") == "ping":
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
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            disconnected.append(connection)
    
    # Remove disconnected clients
    for connection in disconnected:
        if connection in active_connections:
            active_connections.remove(connection)

# Health and monitoring endpoints
@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "agents": {
            name: "running" for name in agents.keys()
        },
        "websocket_connections": len(active_connections),
        "timestamp": datetime.now()
    }

@app.get("/metrics")
async def get_metrics(user: dict = Depends(get_current_user)):
    """Get system metrics"""
    # TODO: Implement proper metrics collection
    return {
        "agents_count": len(agents),
        "active_connections": len(active_connections),
        "uptime": "N/A",  # Calculate actual uptime
        "requests_processed": "N/A",  # Track actual requests
        "timestamp": datetime.now()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )