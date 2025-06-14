#!/usr/bin/env python3
"""
Test AgenticSeek's ACTUAL capabilities vs claims
"""

import requests
import json
import os

API_BASE_URL = "http://localhost:8000"

def test_file_operations():
    """Test if agent can actually interact with files"""
    print("🧪 Testing File Operations...")
    
    # Create a test file
    test_file = "/tmp/agenticseek_test.txt"
    with open(test_file, "w") as f:
        f.write("This is a test file for AgenticSeek")
    
    # Ask agent to read it
    response = requests.post(f"{API_BASE_URL}/v1/chat/completions", json={
        "model": "agenticsseek-enhanced",
        "messages": [
            {"role": "user", "content": f"Read the contents of {test_file} and tell me what it says"}
        ]
    })
    
    result = response.json()["choices"][0]["message"]["content"]
    print(f"Agent response: {result[:200]}...")
    
    # Check if it actually read the file
    if "This is a test file for AgenticSeek" in result:
        print("✅ Can actually read files")
        return True
    else:
        print("❌ Cannot actually read files - just hallucinating")
        return False

def test_directory_listing():
    """Test if agent can list actual directories"""
    print("\n🧪 Testing Directory Operations...")
    
    response = requests.post(f"{API_BASE_URL}/v1/chat/completions", json={
        "model": "agenticsseek-enhanced", 
        "messages": [
            {"role": "user", "content": "List the actual files in /tmp directory"}
        ]
    })
    
    result = response.json()["choices"][0]["message"]["content"]
    print(f"Agent response: {result[:200]}...")
    
    # Check actual /tmp contents
    actual_files = os.listdir("/tmp")
    print(f"Actual /tmp contents: {actual_files[:5]}...")  # Show first 5
    
    # See if agent mentions any real files
    real_file_mentioned = any(f in result for f in actual_files[:10])
    if real_file_mentioned:
        print("✅ Can access real directories")
        return True
    else:
        print("❌ Cannot access real directories - making up fake ones")
        return False

def test_cursor_integration():
    """Test if agent can actually control Cursor"""
    print("\n🧪 Testing Cursor IDE Integration...")
    
    response = requests.post(f"{API_BASE_URL}/v1/chat/completions", json={
        "model": "agenticsseek-enhanced",
        "messages": [
            {"role": "user", "content": "Open /home/gui/test.py in Cursor IDE"}
        ]
    })
    
    result = response.json()["choices"][0]["message"]["content"]
    print(f"Agent response: {result[:200]}...")
    
    # Since we can't easily test if Cursor actually opened,
    # check if response seems realistic vs generic
    if any(phrase in result.lower() for phrase in ["opened", "cursor", "ide", "file"]):
        print("⚠️ Claims to use Cursor but cannot verify")
        return "unknown"
    else:
        print("❌ Doesn't even pretend to use Cursor properly")
        return False

def test_database_operations():
    """Test database agent capabilities"""
    print("\n🧪 Testing Database Operations...")
    
    response = requests.post(f"{API_BASE_URL}/v1/chat/completions", json={
        "model": "agenticsseek-database",
        "messages": [
            {"role": "user", "content": "Connect to SQLite database at /tmp/test.db and show tables"}
        ]
    })
    
    result = response.json()["choices"][0]["message"]["content"]
    print(f"Agent response: {result[:200]}...")
    
    # Check if it's just providing generic SQL advice vs actual connection
    if any(phrase in result.lower() for phrase in ["connected", "tables:", "sqlite"]):
        print("⚠️ Claims database access but likely hallucinating")
        return "unknown"
    else:
        print("❌ Just provides generic database advice")
        return False

def main():
    print("🚀 TESTING AGENTICSEEK ACTUAL CAPABILITIES")
    print("="*50)
    
    results = {
        "file_ops": test_file_operations(),
        "directory_ops": test_directory_listing(), 
        "cursor": test_cursor_integration(),
        "database": test_database_operations()
    }
    
    print("\n" + "="*50)
    print("📊 RESULTS SUMMARY:")
    print("="*50)
    
    for test, result in results.items():
        if result is True:
            status = "✅ WORKING"
        elif result is False:
            status = "❌ FAKE/HALLUCINATING"
        else:
            status = "⚠️ UNKNOWN/UNVERIFIED"
        
        print(f"{test.upper().replace('_', ' ')}: {status}")
    
    print("\n🎯 CONCLUSION:")
    working_count = sum(1 for r in results.values() if r is True)
    if working_count == 0:
        print("❌ AgenticSeek is just a fancy chatbot - no real tool integration")
    elif working_count < len(results) // 2:
        print("⚠️ Some capabilities work, many are hallucinated")
    else:
        print("✅ Most capabilities appear to work as advertised")

if __name__ == "__main__":
    main()