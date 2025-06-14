#!/usr/bin/env python3
"""
Automatically configure Open WebUI to use AgenticSeek API
"""

import requests
import json
import time
import sys

def check_services():
    """Check if both services are running"""
    print("🔍 Checking services...")
    
    # Check AgenticSeek API
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ AgenticSeek API is running")
        else:
            print(f"❌ AgenticSeek API returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AgenticSeek API not accessible: {e}")
        return False
    
    # Check Open WebUI
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Open WebUI is accessible")
        else:
            print(f"❌ Open WebUI returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Open WebUI not accessible: {e}")
        return False
    
    return True

def configure_openwebui_env():
    """Configure Open WebUI environment variables"""
    print("\n🔧 The issue is that Open WebUI needs to be configured...")
    print("\nOpen WebUI is currently looking for:")
    print("  • Ollama at localhost:11434 (not running)")
    print("  • OpenAI API configuration (not set)")
    print("\n💡 SOLUTION: Configure Open WebUI to use AgenticSeek")
    
    print("\n" + "="*60)
    print("🎯 STEP-BY-STEP FIX:")
    print("="*60)
    
    print("\n1️⃣ STOP Open WebUI container:")
    print("   docker stop open-webui")
    
    print("\n2️⃣ RESTART with AgenticSeek configuration:")
    print("   docker run -d \\")
    print("     --name open-webui-agenticsseek \\")
    print("     -p 3000:8080 \\")
    print("     -e OPENAI_API_BASE_URL=http://host.docker.internal:8000 \\")
    print("     -e OPENAI_API_KEY=agenticsseek-demo-key \\")
    print("     -v open-webui:/app/backend/data \\")
    print("     ghcr.io/open-webui/open-webui:main")
    
    print("\n3️⃣ ACCESS reconfigured Open WebUI:")
    print("   http://localhost:3000")
    
    print("\n4️⃣ VERIFY models appear in dropdown")
    
    print("\n" + "="*60)
    print("🚀 AUTOMATED SOLUTION:")
    print("="*60)
    
    return input("\nWould you like me to automatically fix this? (y/n): ").lower().startswith('y')

def fix_openwebui_integration():
    """Automatically fix Open WebUI integration"""
    print("\n🔄 Fixing Open WebUI integration...")
    
    import subprocess
    
    try:
        # Stop existing Open WebUI
        print("1. Stopping existing Open WebUI...")
        subprocess.run(["docker", "stop", "open-webui"], 
                      capture_output=True, check=False)
        
        # Remove existing container
        print("2. Removing old container...")
        subprocess.run(["docker", "rm", "open-webui"], 
                      capture_output=True, check=False)
        
        # Start new Open WebUI with AgenticSeek configuration
        print("3. Starting Open WebUI with AgenticSeek configuration...")
        cmd = [
            "docker", "run", "-d",
            "--name", "open-webui-agenticsseek",
            "-p", "3000:8080",
            "-e", "OPENAI_API_BASE_URL=http://host.docker.internal:8000",
            "-e", "OPENAI_API_KEY=agenticsseek-demo-key",
            "--add-host", "host.docker.internal:host-gateway",
            "-v", "open-webui:/app/backend/data",
            "ghcr.io/open-webui/open-webui:main"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Open WebUI reconfigured successfully!")
            print("\n🎉 NEW ACCESS POINT:")
            print("   🌐 Open WebUI: http://localhost:3000")
            print("   🤖 AgenticSeek models should now appear!")
            
            print("\n⏳ Waiting for startup...")
            time.sleep(10)
            
            # Test the new configuration
            test_new_config()
            
        else:
            print(f"❌ Failed to start Open WebUI: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during reconfiguration: {e}")
        return False
    
    return True

def test_new_config():
    """Test the new Open WebUI configuration"""
    print("\n🧪 Testing new configuration...")
    
    try:
        # Wait a bit more for startup
        time.sleep(5)
        
        # Test Open WebUI
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ Open WebUI accessible at http://localhost:3000")
        else:
            print(f"⚠️ Open WebUI returned {response.status_code}")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Create account or sign in")
        print("3. Check the model dropdown - AgenticSeek models should appear!")
        print("4. Select 'agenticsseek-enhanced' and start chatting")
        
    except Exception as e:
        print(f"⚠️ Could not test new config immediately: {e}")
        print("Please wait a minute and try http://localhost:3000")

def manual_instructions():
    """Provide manual configuration instructions"""
    print("\n📋 MANUAL CONFIGURATION STEPS:")
    print("="*50)
    
    print("\n🔧 Option 1: Environment Variables (Recommended)")
    print("1. Stop current Open WebUI:")
    print("   docker stop open-webui")
    
    print("\n2. Start with AgenticSeek config:")
    print("   docker run -d \\")
    print("     --name open-webui-agenticsseek \\")
    print("     -p 3000:8080 \\")
    print("     -e OPENAI_API_BASE_URL=http://host.docker.internal:8000 \\")
    print("     -e OPENAI_API_KEY=agenticsseek-demo-key \\")
    print("     --add-host host.docker.internal:host-gateway \\")
    print("     -v open-webui:/app/backend/data \\")
    print("     ghcr.io/open-webui/open-webui:main")
    
    print("\n3. Access: http://localhost:3000")
    
    print("\n🔧 Option 2: Web UI Configuration")
    print("1. Go to http://localhost:8080")
    print("2. Settings ⚙️ → Admin Settings → Connections")
    print("3. OpenAI API:")
    print("   - Base URL: http://host.docker.internal:8000")
    print("   - API Key: agenticsseek-demo-key")
    print("4. Save and refresh")

def main():
    print("🔗 Open WebUI + AgenticSeek Integration Fixer")
    print("="*50)
    
    if not check_services():
        print("\n❌ Required services not running. Please start:")
        print("   • AgenticSeek API: python api/simple_main.py")
        print("   • Open WebUI: docker run ... (see previous instructions)")
        return
    
    print("\n🔍 Diagnosing Open WebUI model dropdown issue...")
    print("The models aren't showing because Open WebUI isn't configured")
    print("to connect to AgenticSeek API instead of Ollama.")
    
    if configure_openwebui_env():
        fix_openwebui_integration()
    else:
        manual_instructions()
    
    print("\n🎊 After configuration, AgenticSeek models will appear in Open WebUI!")

if __name__ == "__main__":
    main()