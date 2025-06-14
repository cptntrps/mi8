#!/usr/bin/env python3
"""
Enhanced Router for AgenticSeek with MCP Integration
Provides intelligent agent selection with MCP ecosystem support
"""

import os
import sys
import json
import configparser
from typing import List, Dict, Any, Optional

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sources.router import AgentRouter
from sources.agents.enhanced_mcp_agent import EnhancedMCPAgent
from sources.agents.code_agent import CoderAgent
from sources.agents.browser_agent import BrowserAgent
from sources.agents.casual_agent import CasualAgent
from sources.agents.planner_agent import FileAgent
from sources.utility import pretty_print
from sources.logger import Logger

class EnhancedAgentRouter(AgentRouter):
    """
    Enhanced Agent Router with MCP integration and improved capabilities.
    """
    
    def __init__(self, config_path: str = "enhanced_config.ini"):
        self.config_path = config_path
        self.config = self.load_enhanced_config()
        self.logger = Logger("enhanced_router.log")
        
        # Initialize with enhanced configuration
        supported_languages = self.config.get('MAIN', 'languages', fallback='en').split()
        agents = self.create_enhanced_agents()
        
        super().__init__(agents, supported_languages)
        
        # Enhanced features
        self.mcp_integration = self.config.getboolean('ENHANCED', 'mcp_integration', fallback=True)
        self.smart_routing = self.config.getboolean('ENHANCED', 'smart_routing', fallback=True)
        self.confidence_threshold = self.config.getfloat('ENHANCED', 'confidence_threshold', fallback=0.7)
        self.performance_monitoring = self.config.getboolean('ENHANCED', 'performance_monitoring', fallback=True)
        
        self.logger.info("Enhanced Agent Router initialized")
    
    def load_enhanced_config(self) -> configparser.ConfigParser:
        """Load enhanced configuration with fallbacks."""
        config = configparser.ConfigParser()
        
        # Try enhanced config first, fallback to standard config
        config_files = [self.config_path, "config.ini"]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                config.read(config_file)
                self.logger.info(f"Loaded configuration from {config_file}")
                break
        else:
            # Create default configuration
            self.create_default_config(config)
            self.logger.warning("Using default configuration")
        
        return config
    
    def create_default_config(self, config: configparser.ConfigParser):
        """Create default enhanced configuration."""
        config.add_section('MAIN')
        config.set('MAIN', 'is_local', 'True')
        config.set('MAIN', 'provider_name', 'ollama')
        config.set('MAIN', 'provider_model', 'deepseek-r1:14b')
        config.set('MAIN', 'languages', 'en')
        
        config.add_section('ENHANCED')
        config.set('ENHANCED', 'mcp_integration', 'True')
        config.set('ENHANCED', 'smart_routing', 'True')
        config.set('ENHANCED', 'confidence_threshold', '0.7')
        
        config.add_section('BROWSER')
        config.set('BROWSER', 'headless_browser', 'True')
        config.set('BROWSER', 'stealth_mode', 'True')
    
    def create_enhanced_agents(self) -> List:
        """Create enhanced agent instances with MCP integration."""
        agents = []
        
        # Enhanced MCP Agent (NEW)
        if self.mcp_integration:
            try:
                mcp_agent = EnhancedMCPAgent(
                    "Enhanced MCP Assistant",
                    "prompts/base/mcp_agent.txt",
                    None,  # Provider will be set later
                    verbose=self.config.getboolean('ENHANCED', 'debug_mode', fallback=False)
                )
                agents.append(mcp_agent)
                self.logger.info("Enhanced MCP Agent created")
            except Exception as e:
                self.logger.error(f"Failed to create Enhanced MCP Agent: {e}")
                pretty_print(f"Warning: MCP Agent creation failed: {e}", color="warning")
        
        # Standard agents with enhanced configuration
        try:
            # Casual Agent
            casual_agent = CasualAgent(
                "Casual Assistant",
                "prompts/base/casual_agent.txt",
                None,
                verbose=self.config.getboolean('ENHANCED', 'debug_mode', fallback=False)
            )
            agents.append(casual_agent)
            
            # Code Agent
            code_agent = CoderAgent(
                "Code Assistant",
                "prompts/base/coder_agent.txt",
                None,
                verbose=self.config.getboolean('ENHANCED', 'debug_mode', fallback=False)
            )
            agents.append(code_agent)
            
            # Browser Agent
            browser_agent = BrowserAgent(
                "Web Assistant",
                "prompts/base/browser_agent.txt",
                None,
                verbose=self.config.getboolean('ENHANCED', 'debug_mode', fallback=False)
            )
            agents.append(browser_agent)
            
            # File Agent
            file_agent = FileAgent(
                "File Assistant",
                "prompts/base/file_agent.txt",
                None,
                verbose=self.config.getboolean('ENHANCED', 'debug_mode', fallback=False)
            )
            agents.append(file_agent)
            
            self.logger.info(f"Created {len(agents)} agents successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating standard agents: {e}")
            pretty_print(f"Error creating agents: {e}", color="failure")
        
        return agents
    
    def enhanced_select_agent(self, text: str, context: Optional[Dict] = None) -> Any:
        """
        Enhanced agent selection with context awareness and MCP routing.
        """
        if self.performance_monitoring:
            import time
            start_time = time.time()
        
        try:
            # Check for MCP-specific requests first
            if self.mcp_integration and self.is_mcp_request(text):
                mcp_agent = self.get_mcp_agent()
                if mcp_agent:
                    self.logger.info("Routed to Enhanced MCP Agent")
                    if self.performance_monitoring:
                        elapsed = time.time() - start_time
                        pretty_print(f"Agent selection time: {elapsed:.3f}s", color="info")
                    return mcp_agent
            
            # Use enhanced routing logic
            if self.smart_routing:
                agent = self.smart_agent_selection(text, context)
            else:
                agent = self.select_agent(text)  # Fallback to standard routing
            
            if self.performance_monitoring:
                elapsed = time.time() - start_time
                pretty_print(f"Agent selection time: {elapsed:.3f}s", color="info")
            
            return agent
            
        except Exception as e:
            self.logger.error(f"Enhanced agent selection failed: {e}")
            pretty_print(f"Agent selection error: {e}", color="failure")
            return self.get_fallback_agent()
    
    def is_mcp_request(self, text: str) -> bool:
        """Check if the request is MCP-related."""
        mcp_keywords = [
            'cursor', 'open file', 'memory', 'remember', 'save context',
            'watch', 'monitor', 'file changes', 'mcp', 'tool'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in mcp_keywords)
    
    def get_mcp_agent(self):
        """Get the Enhanced MCP Agent."""
        for agent in self.agents:
            if hasattr(agent, 'type') and agent.type == "enhanced_mcp_agent":
                return agent
        return None
    
    def smart_agent_selection(self, text: str, context: Optional[Dict] = None):
        """
        Smart agent selection using enhanced logic.
        """
        # Analyze request complexity
        complexity = self.estimate_complexity(text)
        
        # Get standard agent selection
        standard_agent = self.select_agent(text)
        
        # Enhanced routing based on context
        if context:
            # Consider conversation history
            if 'previous_agent' in context:
                prev_agent = context['previous_agent']
                # Stick with same agent type for related tasks
                if self.is_related_task(text, context.get('previous_request', '')):
                    self.logger.info(f"Continuing with {prev_agent} for related task")
                    return self.get_agent_by_type(prev_agent)
        
        # Check confidence level
        confidence = self.get_routing_confidence(text)
        if confidence < self.confidence_threshold:
            self.logger.info(f"Low confidence ({confidence:.2f}), using planner agent")
            return self.find_planner_agent()
        
        return standard_agent
    
    def is_related_task(self, current_text: str, previous_text: str) -> bool:
        """Check if current task is related to previous task."""
        # Simple similarity check
        current_words = set(current_text.lower().split())
        previous_words = set(previous_text.lower().split())
        
        if not previous_words:
            return False
        
        overlap = len(current_words.intersection(previous_words))
        similarity = overlap / len(previous_words)
        
        return similarity > 0.3  # 30% word overlap threshold
    
    def get_routing_confidence(self, text: str) -> float:
        """Get routing confidence score."""
        try:
            # Use the router vote system to get confidence
            labels = [agent.role for agent in self.agents]
            result_bart = self.pipelines['bart'](text, labels)
            result_llm = self.llm_router(text)
            
            # Calculate weighted confidence
            confidence_bart = result_bart['scores'][0]
            confidence_llm = result_llm[1]
            
            # Weighted average
            total_confidence = (confidence_bart + confidence_llm) / 2
            return total_confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating routing confidence: {e}")
            return 0.5  # Default medium confidence
    
    def get_agent_by_type(self, agent_type: str):
        """Get agent by type name."""
        for agent in self.agents:
            if hasattr(agent, 'type') and agent.type == agent_type:
                return agent
            elif hasattr(agent, 'role') and agent.role == agent_type:
                return agent
        return None
    
    def get_fallback_agent(self):
        """Get fallback agent when routing fails."""
        # Try to return casual agent as fallback
        for agent in self.agents:
            if hasattr(agent, 'role') and agent.role == 'talk':
                return agent
        
        # If no casual agent, return first available agent
        return self.agents[0] if self.agents else None
    
    def get_router_status(self) -> Dict[str, Any]:
        """Get enhanced router status information."""
        status = {
            "total_agents": len(self.agents),
            "mcp_integration": self.mcp_integration,
            "smart_routing": self.smart_routing,
            "confidence_threshold": self.confidence_threshold,
            "performance_monitoring": self.performance_monitoring,
            "agents": []
        }
        
        for agent in self.agents:
            agent_info = {
                "name": agent.get_agent_name,
                "type": getattr(agent, 'type', 'unknown'),
                "role": getattr(agent, 'role', 'unknown')
            }
            
            # Add MCP-specific information
            if hasattr(agent, 'mcp_servers'):
                agent_info["mcp_servers"] = len(agent.mcp_servers)
                agent_info["available_tools"] = sum(len(tools) for tools in agent.available_tools.values())
            
            status["agents"].append(agent_info)
        
        return status
    
    def print_status(self):
        """Print enhanced router status."""
        status = self.get_router_status()
        
        pretty_print("🔧 Enhanced Agent Router Status", color="info")
        pretty_print("=" * 40, color="status")
        pretty_print(f"Total Agents: {status['total_agents']}", color="output")
        pretty_print(f"MCP Integration: {'✅' if status['mcp_integration'] else '❌'}", color="output")
        pretty_print(f"Smart Routing: {'✅' if status['smart_routing'] else '❌'}", color="output")
        pretty_print(f"Confidence Threshold: {status['confidence_threshold']}", color="output")
        
        pretty_print("\n📋 Available Agents:", color="info")
        for agent_info in status["agents"]:
            pretty_print(f"- {agent_info['name']} ({agent_info['type']})", color="output")
            if "mcp_servers" in agent_info:
                pretty_print(f"  📡 MCP Servers: {agent_info['mcp_servers']}", color="status")
                pretty_print(f"  🛠️ Available Tools: {agent_info['available_tools']}", color="status")

def main():
    """Test the enhanced router."""
    router = EnhancedAgentRouter()
    router.print_status()
    
    # Test routing
    test_queries = [
        "Open main.py in Cursor",
        "Remember that I'm working on a web scraping project",
        "Watch my src directory for changes", 
        "Write a Python script to sort a list",
        "Search the web for Python tutorials",
        "Hello, how are you?",
        "Find the config.json file on my system"
    ]
    
    pretty_print("\n🧪 Testing Enhanced Routing:", color="info")
    for query in test_queries:
        pretty_print(f"\nQuery: {query}", color="warning")
        agent = router.enhanced_select_agent(query)
        if agent:
            pretty_print(f"Selected: {agent.get_agent_name} ({agent.type})", color="success")
        else:
            pretty_print("No agent selected", color="failure")

if __name__ == "__main__":
    main()