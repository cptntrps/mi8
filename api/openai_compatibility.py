#!/usr/bin/env python3
"""
OpenAI API Compatibility Layer for AgenticSeek
Makes AgenticSeek agents compatible with Open WebUI and other OpenAI API clients
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uuid

# OpenAI API compatible models
class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    user: Optional[str] = None

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "agenticsseek"

class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

# Create router for OpenAI compatibility
openai_router = APIRouter(prefix="/v1")

# Available AgenticSeek models
AGENTICSSEEK_MODELS = {
    "agenticsseek-enhanced": {
        "id": "agenticsseek-enhanced",
        "name": "Enhanced MCP Agent",
        "description": "Multi-purpose agent with MCP integration",
        "agent_type": "enhanced_mcp"
    },
    "agenticsseek-database": {
        "id": "agenticsseek-database", 
        "name": "Database Agent",
        "description": "Specialized database operations and SQL analysis",
        "agent_type": "database"
    },
    "agenticsseek-voice": {
        "id": "agenticsseek-voice",
        "name": "Voice-Enabled Agent", 
        "description": "Voice command processing and audio interaction",
        "agent_type": "enhanced_mcp"
    }
}

@openai_router.get("/models")
async def list_models():
    """List available AgenticSeek models in OpenAI format"""
    models = []
    for model_id, model_info in AGENTICSSEEK_MODELS.items():
        models.append(ModelInfo(
            id=model_id,
            created=int(time.time()),
            owned_by="agenticsseek"
        ))
    
    return ModelsResponse(data=models)

@openai_router.get("/models/{model_id}")
async def get_model(model_id: str):
    """Get specific model information"""
    if model_id not in AGENTICSSEEK_MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_info = AGENTICSSEEK_MODELS[model_id]
    return ModelInfo(
        id=model_id,
        created=int(time.time()),
        owned_by="agenticsseek"
    )

@openai_router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    from main import agents  # Import agents from main module
    
    # Validate model
    if request.model not in AGENTICSSEEK_MODELS:
        raise HTTPException(status_code=400, detail=f"Model {request.model} not found")
    
    model_info = AGENTICSSEEK_MODELS[request.model]
    agent_type = model_info["agent_type"]
    
    if agent_type not in agents:
        raise HTTPException(status_code=500, detail=f"Agent {agent_type} not available")
    
    # Extract user message (last message from user)
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")
    
    user_prompt = user_messages[-1].content
    
    # Add system context from previous messages
    system_messages = [msg for msg in request.messages if msg.role == "system"]
    if system_messages:
        system_context = "\n".join([msg.content for msg in system_messages])
        user_prompt = f"System Context: {system_context}\n\nUser: {user_prompt}"
    
    try:
        # Execute agent request
        agent = agents[agent_type]
        
        if hasattr(agent, 'run'):
            result = await agent.run(user_prompt)
            response_text = result.result if hasattr(result, 'result') else str(result)
        else:
            response_text = f"Agent {agent_type} processed: {user_prompt}"
        
        # Handle streaming vs non-streaming
        if request.stream:
            return StreamingResponse(
                stream_chat_completion(request, response_text),
                media_type="text/plain"
            )
        else:
            return create_chat_completion_response(request, response_text)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

def create_chat_completion_response(request: ChatCompletionRequest, response_text: str) -> ChatCompletionResponse:
    """Create non-streaming chat completion response"""
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    
    choice = ChatCompletionChoice(
        index=0,
        message=ChatMessage(role="assistant", content=response_text),
        finish_reason="stop"
    )
    
    return ChatCompletionResponse(
        id=completion_id,
        created=int(time.time()),
        model=request.model,
        choices=[choice],
        usage={
            "prompt_tokens": len(request.messages[-1].content.split()),
            "completion_tokens": len(response_text.split()),
            "total_tokens": len(request.messages[-1].content.split()) + len(response_text.split())
        }
    )

async def stream_chat_completion(request: ChatCompletionRequest, response_text: str) -> Generator[str, None, None]:
    """Stream chat completion response"""
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    
    # Stream response word by word for better UX
    words = response_text.split()
    
    for i, word in enumerate(words):
        chunk_data = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "delta": {"content": word + " " if i < len(words) - 1 else word},
                "finish_reason": None
            }]
        }
        
        yield f"data: {json.dumps(chunk_data)}\n\n"
        
        # Small delay for realistic streaming
        await asyncio.sleep(0.05)
    
    # Send final chunk
    final_chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk", 
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"

# Additional OpenAI compatibility endpoints
@openai_router.post("/completions")
async def completions(request: dict):
    """Legacy completions endpoint (redirect to chat)"""
    # Convert legacy completion to chat format
    messages = [{"role": "user", "content": request.get("prompt", "")}]
    
    chat_request = ChatCompletionRequest(
        model=request.get("model", "agenticsseek-enhanced"),
        messages=[ChatMessage(**msg) for msg in messages],
        max_tokens=request.get("max_tokens"),
        temperature=request.get("temperature", 0.7),
        stream=request.get("stream", False)
    )
    
    return await chat_completions(chat_request)

@openai_router.get("/engines")
async def list_engines():
    """Legacy engines endpoint (redirect to models)"""
    return await list_models()

# Function to add OpenAI compatibility to main app
def add_openai_compatibility(app):
    """Add OpenAI compatibility routes to FastAPI app"""
    app.include_router(openai_router)