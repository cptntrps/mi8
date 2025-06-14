#!/usr/bin/env python3
"""
Enhanced AgenticSeek Demo
Shows the enhanced MCP integration and smart routing capabilities
"""

import sys
import os

# Add the project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sources.utility import pretty_print
    from sources.agents.enhanced_mcp_agent import EnhancedMCPAgent
    
    def demo_enhanced_features():
        print("\n" + "="*60)
        pretty_print("🚀 Enhanced AgenticSeek Demo", color="info")
        print("="*60)
        
        # Test Enhanced MCP Agent
        pretty_print("\n📡 Testing Enhanced MCP Agent Integration", color="warning")
        
        try:
            # Create enhanced MCP agent
            mcp_agent = EnhancedMCPAgent(
                "Enhanced MCP Demo",
                "prompts/base/mcp_agent.txt",
                None,
                verbose=True
            )
            
            pretty_print("✅ Enhanced MCP Agent created successfully", color="success")
            
            # Show MCP server discovery
            servers = mcp_agent.discover_mcp_servers()
            pretty_print(f"📊 Discovered {len(servers)} MCP servers:", color="info")
            for name, config in servers.items():
                pretty_print(f"  - {name}: {config.get('command', 'unknown')}", color="output")
            
            # Show available tools
            tools = mcp_agent.available_tools
            pretty_print(f"\n🛠️ Available MCP Tools:", color="info")
            for server, tool_list in tools.items():
                pretty_print(f"  {server}:", color="warning")
                for tool, desc in tool_list.items():
                    pretty_print(f"    - {tool}: {desc[:50]}...", color="output")
            
            # Show status
            status = mcp_agent.get_mcp_status()
            pretty_print(f"\n{status}", color="info")
            
        except Exception as e:
            pretty_print(f"❌ Enhanced MCP Agent test failed: {e}", color="failure")
        
        # Test Basic Router Functionality
        pretty_print("\n🧠 Testing Smart Routing System", color="warning")
        
        try:
            from enhanced_router import EnhancedAgentRouter
            
            # Create enhanced router
            router = EnhancedAgentRouter()
            pretty_print("✅ Enhanced Router created successfully", color="success")
            
            # Show router status
            router.print_status()
            
            # Test routing examples
            test_queries = [
                "Open main.py in Cursor",
                "Remember I'm working on authentication",
                "Watch my src directory for changes",
                "Write a Python script",
                "Hello, how are you?"
            ]
            
            pretty_print("\n🧪 Testing Query Routing:", color="info")
            for query in test_queries:
                try:
                    agent = router.enhanced_select_agent(query)
                    if agent:
                        agent_type = getattr(agent, 'type', 'unknown')
                        pretty_print(f"  '{query}' → {agent.get_agent_name} ({agent_type})", color="output")
                    else:
                        pretty_print(f"  '{query}' → No agent selected", color="failure")
                except Exception as e:
                    pretty_print(f"  '{query}' → Error: {str(e)[:50]}...", color="warning")
            
        except Exception as e:
            pretty_print(f"❌ Enhanced Router test failed: {e}", color="failure")
        
        # Show enhancement summary
        pretty_print("\n🎯 Enhancement Summary", color="warning")
        enhancements = [
            "✅ Enhanced MCP Agent with ecosystem integration",
            "✅ Smart agent routing with context awareness", 
            "✅ Automatic MCP server discovery",
            "✅ Tool-specific routing for MCP requests",
            "✅ Performance monitoring and optimization",
            "✅ Advanced error handling and recovery",
            "✅ Streamlined setup and configuration"
        ]
        
        for enhancement in enhancements:
            pretty_print(f"  {enhancement}", color="success")
        
        print("\n" + "="*60)
        pretty_print("🎉 Enhanced AgenticSeek Demo Complete!", color="info")
        print("="*60)
        
        pretty_print("\n📋 Next Steps:", color="warning")
        pretty_print("1. Start Ollama: ollama serve", color="output")
        pretty_print("2. Start Docker services: ./start_services.sh", color="output")
        pretty_print("3. Use enhanced CLI: python3 cli.py", color="output")
        pretty_print("4. Or run web interface: http://localhost:3000", color="output")
    
    if __name__ == "__main__":
        demo_enhanced_features()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("  pip install -r requirements_core.txt")
    print("  pip install termcolor langdetect ollama fake-useragent")
except Exception as e:
    print(f"❌ Demo error: {e}")
    print("Please check the setup and try again.")