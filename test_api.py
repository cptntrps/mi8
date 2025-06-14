#!/usr/bin/env python3
import requests
import json

# Test the API
api_base = "http://localhost:8000"

print("🔍 Testing AgenticSeek API...")
print("="*50)

# Test health
print("1. Health check:")
response = requests.get(f"{api_base}/health")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    health = response.json()
    print(f"   API Status: {health['status']}")
    print(f"   Agents: {list(health['agents'].keys())}")

# Test models
print("\n2. Available models:")
response = requests.get(f"{api_base}/v1/models")
if response.status_code == 200:
    models = response.json()
    for model in models['data']:
        print(f"   - {model['id']}")

# Test agent execution
print("\n3. Agent execution test:")
payload = {
    "prompt": "Hello! What can you help me with?",
    "agent_type": "enhanced_mcp"
}
response = requests.post(f"{api_base}/agents/enhanced_mcp/execute", json=payload)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"   Response: {result['response'][:100]}...")

# Test chat completions
print("\n4. OpenAI compatibility test:")
payload = {
    "model": "agenticsseek-enhanced",
    "messages": [{"role": "user", "content": "Hello! Tell me about your database capabilities."}]
}
response = requests.post(f"{api_base}/v1/chat/completions", json=payload)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"   Chat Response: {result['choices'][0]['message']['content'][:100]}...")

print("\n✅ API Testing Complete!")
print(f"\n🌐 Open these URLs to explore:")
print(f"   • API Docs: http://localhost:8000/docs")
print(f"   • Health: http://localhost:8000/health")
print(f"   • Models: http://localhost:8000/v1/models")