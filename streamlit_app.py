#!/usr/bin/env python3
"""
AgenticSeek Streamlit Interface - Local Ollama Edition
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import List, Dict

# Page configuration
st.set_page_config(
    page_title="AgenticSeek Local",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #696969;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .status-card {
        background: linear-gradient(90deg, #2E8B57, #32CD32);
        color: white !important;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .status-card h4, .status-card p {
        color: white !important;
        margin: 0.25rem 0;
    }
    .agent-card {
        background: #F0F8FF;
        border-left: 5px solid #2E8B57;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: #333333 !important;
    }
    .agent-card h4, .agent-card p {
        color: #333333 !important;
        margin: 0.25rem 0;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        color: #333333 !important;
    }
    .user-message {
        background: #E3F2FD;
        border-left: 4px solid #2196F3;
        color: #1565C0 !important;
    }
    .assistant-message {
        background: #F1F8E9;
        border-left: 4px solid #4CAF50;
        color: #2E7D32 !important;
    }
    .chat-message strong {
        color: inherit !important;
    }
    
    /* Fix Streamlit's default text colors */
    .stMarkdown p {
        color: #333333 !important;
    }
    .element-container .stMarkdown {
        color: #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"
AVAILABLE_MODELS = {
    "agenticsseek-enhanced": {
        "name": "Enhanced Agent",
        "description": "File management, Cursor IDE integration, memory management",
        "icon": "🚀"
    },
    "agenticsseek-database": {
        "name": "Database Specialist", 
        "description": "SQL operations, schema analysis, query optimization",
        "icon": "🗄️"
    },
    "agenticsseek-general": {
        "name": "General Assistant",
        "description": "Web browsing, code generation, task planning",
        "icon": "🧠"
    }
}

def check_api_health():
    """Check if AgenticSeek API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_available_models():
    """Get available models from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            return response.json()["data"]
        return []
    except:
        return []

def send_chat_message(model: str, messages: List[Dict], temperature: float = 0.7):
    """Send chat message to API"""
    try:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "agenticsseek-enhanced"

# Header
st.markdown('<div class="main-header">🤖 AgenticSeek Local</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Powered by Local Ollama on your RTX 4090</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🔧 System Status")
    
    # Check API health
    health = check_api_health()
    if health:
        st.markdown(f"""
        <div class="status-card">
            <h4>✅ System Healthy</h4>
            <p><strong>Ollama:</strong> {health.get('ollama_status', 'unknown')}</p>
            <p><strong>Mode:</strong> {'Local' if health.get('local_mode') else 'Cloud'}</p>
            <p><strong>Connections:</strong> {health.get('websocket_connections', 0)}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("❌ AgenticSeek API not accessible")
        st.info("Make sure the API is running: `python api/ollama_main.py`")
    
    st.divider()
    
    # Model selection
    st.header("🤖 Select Agent")
    
    for model_id, model_info in AVAILABLE_MODELS.items():
        if st.button(
            f"{model_info['icon']} {model_info['name']}", 
            key=model_id,
            use_container_width=True
        ):
            st.session_state.selected_model = model_id
            st.rerun()
    
    # Show selected model info
    if st.session_state.selected_model in AVAILABLE_MODELS:
        selected = AVAILABLE_MODELS[st.session_state.selected_model]
        st.markdown(f"""
        <div class="agent-card">
            <h4>{selected['icon']} {selected['name']}</h4>
            <p>{selected['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Settings
    st.header("⚙️ Settings")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.header(f"💬 Chat with {AVAILABLE_MODELS[st.session_state.selected_model]['name']}")

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>{AVAILABLE_MODELS[st.session_state.selected_model]['icon']} Agent:</strong> {message["content"]}
        </div>
        """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message immediately
    st.markdown(f"""
    <div class="chat-message user-message">
        <strong>You:</strong> {prompt}
    </div>
    """, unsafe_allow_html=True)
    
    # Get AI response
    with st.spinner(f"🤖 {AVAILABLE_MODELS[st.session_state.selected_model]['name']} is thinking..."):
        response = send_chat_message(
            st.session_state.selected_model,
            st.session_state.messages,
            temperature
        )
    
    if "error" in response:
        st.error(f"Error: {response['error']}")
    else:
        # Extract response content
        assistant_message = response["choices"][0]["message"]["content"]
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        
        # Display assistant message
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <strong>{AVAILABLE_MODELS[st.session_state.selected_model]['icon']} Agent:</strong> {assistant_message}
        </div>
        """, unsafe_allow_html=True)
    
    # Rerun to update the display
    st.rerun()

# Footer with quick examples
if not st.session_state.messages:
    st.markdown("---")
    st.subheader("💡 Try these examples:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🚀 Enhanced Agent:**
        - "Tell me about your file management capabilities"
        - "How do you integrate with Cursor IDE?"
        - "What memory management features do you have?"
        """)
    
    with col2:
        st.markdown("""
        **🗄️ Database Specialist:**
        - "Help me design a database schema"
        - "Optimize this SQL query"
        - "Explain database normalization"
        """)
    
    with col3:
        st.markdown("""
        **🧠 General Assistant:**
        - "Write a Python script for data analysis"
        - "Help me plan a complex project"
        - "Explain machine learning concepts"
        """)

# System info at bottom
if health:
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔥 GPU", "RTX 4090")
    with col2:
        st.metric("⚡ Status", "Local")
    with col3:
        st.metric("🔒 Privacy", "100%")
    with col4:
        st.metric("🌐 Mode", "Offline")