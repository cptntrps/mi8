#!/usr/bin/env python3
"""
AgenticSeek FastAPI Backend using Local Ollama
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
import ollama

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the tool executor
try:
    from tools.tool_executor import get_tool_executor
    TOOLS_AVAILABLE = True
    print("✅ Real tools loaded successfully!")
except ImportError as e:
    print(f"❌ Failed to load tools: {e}")
    TOOLS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="AgenticSeek Local API",
    description="AgenticSeek with Local Ollama Integration",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_MODEL = "llama3:latest"  # Start with available model
AVAILABLE_MODELS = [
    "agenticsseek-enhanced",
    "agenticsseek-database",
    "agenticsseek-general"
]

# Model mapping to actual Ollama models
MODEL_MAPPING = {
    "agenticsseek-enhanced": "llama3:latest",
    "agenticsseek-database": "llama3:latest", 
    "agenticsseek-general": "llama3:latest"
}

# Request/Response Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "agenticsseek"

# Global state
active_connections: List[WebSocket] = []
agent_status = {
    "enhanced_mcp": "running",
    "database": "running",
    "general": "running"
}

def get_system_prompt(model_name: str) -> str:
    """Get system prompt based on model type"""
    tool_instructions = ""
    if TOOLS_AVAILABLE:
        executor = get_tool_executor()
        tool_instructions = executor.get_tool_usage_instructions()
    
    base_prompts = {
        "agenticsseek-enhanced": """You are an enhanced AI agent with REAL functional capabilities:
        - ACTUAL file management and Cursor IDE integration
        - REAL memory management for conversation context  
        - ACTUAL voice command processing
        - REAL multi-tool coordination
        
        You can perform ACTUAL operations on the user's system using tools.""",
        
        "agenticsseek-database": """You are a database specialist AI agent with REAL capabilities:
        - ACTUAL SQL query execution and optimization
        - REAL database schema analysis and connections
        - ACTUAL data relationship mapping
        - REAL performance tuning and operations
        
        You can connect to and operate on REAL databases using tools.""",
        
        "agenticsseek-general": """You are AgenticSeek, a helpful AI assistant with REAL system access:
        - ACTUAL web browsing and research
        - REAL code generation and execution
        - ACTUAL task planning and execution
        - REAL local file operations and shell commands
        
        You can perform ACTUAL operations on the local system."""
    }
    
    base_prompt = base_prompts.get(model_name, base_prompts["agenticsseek-general"])
    
    if TOOLS_AVAILABLE:
        return base_prompt + "\n\n" + tool_instructions
    else:
        return base_prompt + "\n\nNOTE: Tools are not available - you can only provide text responses."

async def call_ollama(model: str, messages: List[ChatMessage], temperature: float = 0.7) -> Dict[str, Any]:
    """Call local Ollama API and process tools"""
    try:
        # Get the actual Ollama model
        ollama_model = MODEL_MAPPING.get(model, "llama3:latest")
        
        # Prepare messages for Ollama
        ollama_messages = []
        
        # Add system prompt
        system_prompt = get_system_prompt(model)
        ollama_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add conversation messages
        for msg in messages:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Call Ollama
        response = ollama.chat(
            model=ollama_model,
            messages=ollama_messages,
            options={
                "temperature": temperature,
                "num_predict": 1000
            }
        )
        
        ai_response = response['message']['content']
        
        # Process tools if available
        if TOOLS_AVAILABLE:
            executor = get_tool_executor()
            tool_result = executor.process_ai_response(ai_response)
            
            if tool_result.get("has_tool_calls"):
                # Format response with tool results
                final_response = ai_response + "\n\n" + "🛠️ **TOOL EXECUTION RESULTS:**\n"
                
                for i, tool_call in enumerate(tool_result["tool_calls"], 1):
                    tool_name = tool_call.get("tool", "unknown")
                    result = tool_call.get("result", {})
                    
                    final_response += f"\n**{i}. {tool_name}:**\n"
                    
                    if "error" in result:
                        final_response += f"❌ Error: {result['error']}\n"
                    elif result.get("success"):
                        # Format successful results nicely
                        if "content" in result:
                            final_response += f"✅ Content: {result['content'][:200]}...\n"
                        elif "results" in result:
                            final_response += f"✅ Found {len(result['results'])} results\n"
                        elif "message" in result:
                            final_response += f"✅ {result['message']}\n"
                        else:
                            final_response += f"✅ Success: {str(result)[:200]}...\n"
                    else:
                        final_response += f"⚠️ Result: {str(result)[:200]}...\n"
                
                return {
                    "content": final_response,
                    "tools_used": True,
                    "tool_count": len(tool_result["tool_calls"])
                }
            else:
                return {
                    "content": ai_response,
                    "tools_used": False,
                    "tool_count": 0
                }
        else:
            return {
                "content": ai_response,
                "tools_used": False, 
                "tool_count": 0
            }
        
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return {
            "content": f"I apologize, but I encountered an error: {str(e)}. Please ensure Ollama is running with the model '{ollama_model}' available.",
            "tools_used": False,
            "tool_count": 0,
            "error": True
        }

@app.get("/")
async def root():
    return {"message": "AgenticSeek Local API - Running with Ollama", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Ollama connection
        models = ollama.list()
        ollama_status = "running" if models else "unavailable"
    except:
        ollama_status = "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": agent_status,
        "ollama_status": ollama_status,
        "websocket_connections": len(active_connections),
        "local_mode": True
    }

@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint"""
    models = []
    for model_id in AVAILABLE_MODELS:
        models.append(ModelInfo(
            id=model_id,
            created=1699999999,
            owned_by="agenticsseek"
        ))
    
    return {"object": "list", "data": models}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, authorization: Optional[str] = Header(None)):
    """OpenAI-compatible chat completions endpoint"""
    try:
        logger.info(f"Chat request for model: {request.model}")
        
        # Validate model
        if request.model not in MODEL_MAPPING:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not available")
        
        # Get response from Ollama
        ollama_result = await call_ollama(
            request.model, 
            request.messages, 
            request.temperature or 0.7
        )
        
        response_content = ollama_result["content"]
        
        # Format OpenAI-compatible response
        response = ChatCompletionResponse(
            id=f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created=int(datetime.now().timestamp()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": sum(len(msg.content.split()) for msg in request.messages),
                "completion_tokens": len(response_content.split()),
                "total_tokens": sum(len(msg.content.split()) for msg in request.messages) + len(response_content.split())
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to AgenticSeek Local API",
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back for now
            await websocket.send_text(json.dumps({
                "type": "response",
                "message": f"Received: {message}",
                "timestamp": datetime.now().isoformat()
            }))
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    print("🚀 Starting AgenticSeek Local API with Ollama")
    print(f"📍 Available at: http://localhost:8000")
    print(f"🤖 Using Ollama models: {list(MODEL_MAPPING.values())}")
    print(f"📖 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )