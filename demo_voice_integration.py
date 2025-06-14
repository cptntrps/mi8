#!/usr/bin/env python3
"""
Voice Integration Demo for Enhanced AgenticSeek
Shows voice command capabilities with MCP integration
"""

import sys
import os
import time
import threading

# Add the project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sources.utility import pretty_print
    from sources.agents.enhanced_mcp_agent import EnhancedMCPAgent
    from sources.voice import VoiceCommandProcessor, VOICE_AVAILABLE
    
    def demo_voice_integration():
        print("\n" + "="*70)
        pretty_print("🎤🤖 Enhanced AgenticSeek - Voice Integration Demo", color="info")
        print("="*70)
        
        # Check voice availability
        if not VOICE_AVAILABLE:
            pretty_print("❌ Voice libraries not available", color="failure")
            pretty_print("Install with: pip install PyAudio SpeechRecognition pyttsx3", color="warning")
            return
        
        pretty_print("✅ Voice libraries available", color="success")
        
        # Create enhanced MCP agent with voice enabled
        try:
            agent = EnhancedMCPAgent(
                "Voice-Enabled MCP Agent",
                "prompts/base/mcp_agent.txt", 
                None,  # No LLM provider for demo
                verbose=True,
                voice_enabled=True
            )
            
            pretty_print("✅ Enhanced MCP Agent with voice integration created", color="success")
        except Exception as e:
            pretty_print(f"❌ Failed to create agent: {e}", color="failure")
            return
        
        # Show agent status
        status = agent.get_mcp_status()
        print(f"\n📊 Agent Status:")
        print(status)
        
        # Show voice status
        voice_status = agent.get_voice_status()
        if voice_status.get("enabled"):
            pretty_print("✅ Voice system ready", color="success")
            print(f"Voice Status: {voice_status['status']}")
        else:
            pretty_print(f"❌ Voice system not available: {voice_status.get('reason', 'Unknown')}", color="failure")
            return
        
        # Demo voice command parsing
        pretty_print("\n🧪 Testing Voice Command Parsing", color="warning")
        
        if agent.voice_processor:
            test_commands = [
                "AgenticSeek open main.py in cursor",
                "AgenticSeek remember I'm working on authentication",
                "AgenticSeek watch the src directory",
                "AgenticSeek create a file called test.py",
                "AgenticSeek search for function in files",
                "AgenticSeek write a Python script",
                "AgenticSeek hello there"
            ]
            
            for test_text in test_commands:
                # Remove wake word for parsing test
                clean_text = test_text.replace("AgenticSeek ", "")
                command = agent.voice_processor.parse_command(clean_text)
                pretty_print(f"  '{test_text}' → {command.command_type.value}:{command.action}", color="output")
        
        # Demo MCP tool integration
        pretty_print("\n🔧 Testing MCP Tool Integration", color="warning")
        
        # Show available tools
        tools = agent.available_tools
        pretty_print(f"Available MCP tools:", color="info")
        for server, tool_list in tools.items():
            pretty_print(f"  {server}:", color="warning")
            for tool, desc in list(tool_list.items())[:3]:  # Show first 3 tools
                pretty_print(f"    - {tool}", color="output")
        
        # Interactive voice demo
        pretty_print("\n🎤 Interactive Voice Demo", color="warning")
        pretty_print("Say one of these commands or 'stop demo' to exit:", color="info")
        
        demo_commands = [
            "AgenticSeek open config.py in cursor",
            "AgenticSeek remember demo session started", 
            "AgenticSeek watch current directory",
            "AgenticSeek hello",
            "AgenticSeek help"
        ]
        
        for cmd in demo_commands:
            pretty_print(f"  '{cmd}'", color="output")
        
        # Setup demo command handler
        def demo_command_handler(command):
            pretty_print(f"\n🎯 Voice Command Received:", color="success")
            pretty_print(f"  Text: '{command.original_text}'", color="output")
            pretty_print(f"  Type: {command.command_type.value}", color="output")
            pretty_print(f"  Action: {command.action}", color="output")
            pretty_print(f"  Parameters: {command.parameters}", color="output")
            
            # Execute the command through the agent
            response = agent._handle_voice_command(command)
            pretty_print(f"  Response: {response}", color="info")
            
            # Check for demo exit
            if "stop demo" in command.original_text.lower():
                agent.stop_voice_control()
                return "Demo stopped"
            
            return response
        
        # Override the command handler for demo
        if agent.voice_processor:
            agent.voice_processor.on_command_detected = demo_command_handler
        
        try:
            # Start voice control
            start_result = agent.start_voice_control()
            pretty_print(f"🎤 {start_result}", color="success")
            
            # Wait for user interaction
            pretty_print("\n⏳ Listening for voice commands... Press Enter to stop demo", color="warning")
            input()
            
        except KeyboardInterrupt:
            pretty_print("\n⏹️ Demo interrupted by user", color="warning")
        except Exception as e:
            pretty_print(f"\n❌ Demo error: {e}", color="failure")
        finally:
            # Stop voice control
            stop_result = agent.stop_voice_control()
            pretty_print(f"🔇 {stop_result}", color="info")
        
        # Show command history
        voice_status = agent.get_voice_status()
        if voice_status.get("enabled") and voice_status.get("recent_commands"):
            pretty_print("\n📋 Recent Voice Commands:", color="warning")
            for cmd in voice_status["recent_commands"]:
                pretty_print(f"  {cmd['text']} → {cmd['type']}:{cmd['action']}", color="output")
        
        print("\n" + "="*70)
        pretty_print("🎉 Voice Integration Demo Complete!", color="info")
        print("="*70)
        
        pretty_print("\n💡 Voice Integration Features:", color="warning")
        features = [
            "✅ Wake word activation ('AgenticSeek')",
            "✅ Natural language command parsing",
            "✅ Direct MCP tool integration",
            "✅ Cursor file operations via voice",
            "✅ Memory management via voice", 
            "✅ File watching via voice",
            "✅ Text-to-speech feedback",
            "✅ Command history tracking"
        ]
        
        for feature in features:
            pretty_print(f"  {feature}", color="success")
        
        pretty_print("\n🚀 Voice Commands Examples:", color="warning")
        examples = [
            "'AgenticSeek open main.py in cursor' - Opens file in Cursor",
            "'AgenticSeek remember I'm working on auth' - Saves to memory",
            "'AgenticSeek watch src directory' - Starts file monitoring",
            "'AgenticSeek create file utils.py' - Creates new file",
            "'AgenticSeek search for function in files' - Searches project"
        ]
        
        for example in examples:
            pretty_print(f"  {example}", color="output")

    if __name__ == "__main__":
        demo_voice_integration()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("  pip install PyAudio SpeechRecognition pyttsx3 sounddevice")
    print("  pip install termcolor langdetect ollama fake-useragent")
except Exception as e:
    print(f"❌ Demo error: {e}")
    print("Please check the setup and try again.")