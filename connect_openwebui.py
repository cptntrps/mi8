#!/usr/bin/env python3
"""
Connect Open WebUI to AgenticSeek API
Sets up proper model configuration
"""

import requests
import json
import time

def setup_openwebui_connection():
    """Configure Open WebUI to use AgenticSeek API"""
    
    print("🔗 Connecting Open WebUI to AgenticSeek...")
    
    # Open WebUI API base
    webui_base = "http://localhost:8080"
    agenticsseek_base = "http://localhost:8000"
    
    # First, let's check if Open WebUI is accessible
    try:
        response = requests.get(f"{webui_base}/health", timeout=5)
        print(f"✅ Open WebUI accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Open WebUI not accessible: {e}")
        return False
    
    # Check our AgenticSeek API
    try:
        response = requests.get(f"{agenticsseek_base}/health", timeout=5)
        print(f"✅ AgenticSeek API accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ AgenticSeek API not accessible: {e}")
        return False
    
    print("\n📋 Instructions to connect Open WebUI to AgenticSeek:")
    print("="*60)
    print("1. Open http://localhost:8080 in your browser")
    print("2. Create an account or sign in")
    print("3. Go to Settings (gear icon) → Connections")
    print("4. In the 'OpenAI API' section:")
    print(f"   - API Base URL: {agenticsseek_base}")
    print("   - API Key: agenticsseek-demo-key")
    print("5. Click 'Verify connection'")
    print("6. Go to Settings → Models")
    print("7. You should see AgenticSeek models available!")
    print("8. Select a model and start chatting")
    
    print("\n🤖 Available AgenticSeek Models:")
    try:
        response = requests.get(f"{agenticsseek_base}/v1/models")
        if response.status_code == 200:
            models = response.json()
            for model in models['data']:
                print(f"   • {model['id']}")
        else:
            print("   ❌ Could not fetch models")
    except Exception as e:
        print(f"   ❌ Error fetching models: {e}")
    
    return True

def test_openai_compatibility():
    """Test OpenAI compatibility with a sample request"""
    
    print("\n🧪 Testing OpenAI Compatibility...")
    
    agenticsseek_base = "http://localhost:8000"
    
    # Test chat completion
    payload = {
        "model": "agenticsseek-enhanced",
        "messages": [
            {"role": "user", "content": "Hello! This is a test from Open WebUI integration."}
        ]
    }
    
    try:
        response = requests.post(
            f"{agenticsseek_base}/v1/chat/completions",
            json=payload,
            headers={"Authorization": "Bearer agenticsseek-demo-key"}
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Chat completion test successful!")
            print(f"📝 Response: {content[:100]}...")
            return True
        else:
            print(f"❌ Chat completion failed: {response.status_code}")
            print(f"📝 Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat completion error: {e}")
        return False

def create_webui_config():
    """Create a configuration file for automatic setup"""
    
    config = {
        "OPENAI_API_BASE_URL": "http://localhost:8000",
        "OPENAI_API_KEY": "agenticsseek-demo-key",
        "models": [
            {
                "id": "agenticsseek-enhanced",
                "name": "AgenticSeek Enhanced",
                "description": "General purpose agent with MCP integration"
            },
            {
                "id": "agenticsseek-database", 
                "name": "AgenticSeek Database",
                "description": "Database specialist for SQL operations"
            }
        ]
    }
    
    with open("openwebui_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"\n📄 Configuration saved to: openwebui_config.json")
    return config

if __name__ == "__main__":
    print("🚀 AgenticSeek + Open WebUI Integration Setup")
    print("="*50)
    
    # Setup connection
    if setup_openwebui_connection():
        
        # Test compatibility  
        test_openai_compatibility()
        
        # Create config
        create_webui_config()
        
        print("\n🎉 Setup Complete!")
        print("\n🌐 Next Steps:")
        print("1. Open http://localhost:8080")
        print("2. Follow the connection instructions above")
        print("3. Start chatting with AgenticSeek models!")
        
    else:
        print("\n❌ Setup failed - check that both services are running")