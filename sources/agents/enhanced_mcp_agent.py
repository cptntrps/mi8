import os
import sys
import json
import subprocess
import asyncio
from typing import Dict, List, Any, Optional
from sources.agents.agent import Agent
from sources.memory import Memory
from sources.utility import pretty_print
from sources.schemas import executorResult

# Voice integration imports
try:
    from sources.voice import VoiceCommandProcessor, VoiceCommand, CommandType
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

class EnhancedMCPAgent(Agent):
    """
    Enhanced MCP Agent with direct integration to our MCP ecosystem.
    Provides seamless access to Cursor Control, Memory Management, and File Watcher MCPs.
    """
    
    def __init__(self, name: str, prompt_path: str, provider, verbose=False, browser=None, voice_enabled=False) -> None:
        super().__init__(name, prompt_path, provider, verbose, browser)
        self.type = "enhanced_mcp_agent"
        self.role = "mcp"
        self.mcp_servers = self.discover_mcp_servers()
        self.available_tools = self.load_mcp_tools()
        self.memory_session_id = None
        self.active_watchers = {}
        
        # Voice integration
        self.voice_enabled = voice_enabled and VOICE_AVAILABLE
        self.voice_processor = None
        if self.voice_enabled:
            self._initialize_voice_system()
        
    def discover_mcp_servers(self) -> Dict[str, Dict]:
        """
        Discover available MCP servers from our ecosystem.
        """
        mcp_config_paths = [
            os.path.expanduser("~/.config/claude/claude_desktop_config.json"),
            os.path.join(os.getcwd(), ".mcp.json"),
            "/home/gui/Claude_Code/.mcp.json"
        ]
        
        servers = {}
        for config_path in mcp_config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        if 'mcpServers' in config:
                            servers.update(config['mcpServers'])
                            if self.verbose:
                                pretty_print(f"Found MCP servers in {config_path}", color="info")
                except Exception as e:
                    if self.verbose:
                        pretty_print(f"Error reading {config_path}: {e}", color="warning")
        
        return servers
    
    def load_mcp_tools(self) -> Dict[str, Dict]:
        """
        Load available tools from discovered MCP servers.
        """
        tools = {
            "cursor_control": {
                "cursor_open_file": "Open files in Cursor IDE with optional line jumping",
                "cursor_open_directory": "Open directories in Cursor IDE", 
                "cursor_run_command": "Execute terminal commands",
                "cursor_search_files": "Search for text within files",
                "cursor_create_file": "Create new files with content"
            },
            "memory_management": {
                "memory_save_context": "Save important context for future reference",
                "memory_load_context": "Load previously saved context",
                "memory_summarize_conversation": "Create conversation summaries",
                "memory_analyze_tokens": "Analyze token usage and get optimization tips",
                "memory_clean_old_data": "Clean old memory entries"
            },
            "file_watcher": {
                "watcher_start_monitoring": "Start monitoring file system changes",
                "watcher_get_changes": "Get recent file system changes",
                "watcher_stop_monitoring": "Stop file system monitoring",
                "watcher_get_status": "Get status of active watchers"
            }
        }
        return tools
    
    def execute_mcp_tool(self, server_name: str, tool_name: str, args: Dict = None) -> Dict:
        """
        Execute an MCP tool using direct server communication.
        """
        if server_name not in self.mcp_servers:
            return {"error": f"MCP server '{server_name}' not found"}
        
        server_config = self.mcp_servers[server_name]
        command = [server_config["command"]] + server_config.get("args", [])
        
        # Prepare the MCP request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args or {}
            }
        }
        
        try:
            # Execute the MCP server
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=dict(os.environ, **server_config.get("env", {}))
            )
            
            # Send the request
            stdout, stderr = process.communicate(input=json.dumps(request) + "\n", timeout=30)
            
            if process.returncode != 0:
                return {"error": f"MCP server error: {stderr}"}
            
            # Parse response
            for line in stdout.strip().split('\n'):
                if line.strip():
                    try:
                        response = json.loads(line)
                        if 'result' in response:
                            return response['result']
                        elif 'error' in response:
                            return {"error": response['error']}
                    except json.JSONDecodeError:
                        continue
            
            return {"error": "No valid response from MCP server"}
            
        except subprocess.TimeoutExpired:
            process.kill()
            return {"error": "MCP server timeout"}
        except Exception as e:
            return {"error": f"Failed to execute MCP tool: {str(e)}"}
    
    def cursor_open_file(self, file_path: str, line_number: Optional[int] = None) -> str:
        """Open a file in Cursor IDE."""
        args = {"filePath": file_path}
        if line_number:
            args["lineNumber"] = line_number
        
        result = self.execute_mcp_tool("cursor-control", "cursor_open_file", args)
        if "error" in result:
            return f"Error opening file: {result['error']}"
        
        content = result.get("content", [{}])[0].get("text", "")
        try:
            data = json.loads(content)
            return f"✅ {data.get('message', 'File opened successfully')}"
        except:
            return f"✅ File opened: {file_path}"
    
    def cursor_run_command(self, command: str, working_directory: Optional[str] = None) -> str:
        """Execute a command in the terminal."""
        args = {"command": command}
        if working_directory:
            args["workingDirectory"] = working_directory
        
        result = self.execute_mcp_tool("cursor-control", "cursor_run_command", args)
        if "error" in result:
            return f"Error executing command: {result['error']}"
        
        content = result.get("content", [{}])[0].get("text", "")
        return f"Command output:\n{content}"
    
    def memory_save_context(self, content: str, context_type: str = "context", relevance: float = 1.0) -> str:
        """Save context to memory."""
        args = {
            "content": content,
            "type": context_type,
            "relevance": relevance
        }
        if self.memory_session_id:
            args["sessionId"] = self.memory_session_id
        
        result = self.execute_mcp_tool("memory-management", "memory_save_context", args)
        if "error" in result:
            return f"Error saving context: {result['error']}"
        
        content = result.get("content", [{}])[0].get("text", "")
        try:
            data = json.loads(content)
            self.memory_session_id = data.get("sessionId")
            return f"✅ Context saved with {data.get('tokens', 0)} tokens"
        except:
            return "✅ Context saved successfully"
    
    def memory_load_context(self, session_id: Optional[str] = None, context_type: Optional[str] = None) -> str:
        """Load context from memory."""
        args = {"sessionId": session_id or self.memory_session_id or "default"}
        if context_type:
            args["type"] = context_type
        
        result = self.execute_mcp_tool("memory-management", "memory_load_context", args)
        if "error" in result:
            return f"Error loading context: {result['error']}"
        
        content = result.get("content", [{}])[0].get("text", "")
        try:
            data = json.loads(content)
            entries = data.get("entries", [])
            if not entries:
                return "No context found"
            
            context_summary = "📋 Loaded Context:\n"
            for entry in entries[:3]:  # Show top 3 entries
                context_summary += f"- {entry.get('type', 'unknown')}: {entry.get('content', '')[:100]}...\n"
            
            return context_summary
        except:
            return "Context loaded but parsing failed"
    
    def watcher_start_monitoring(self, paths: List[str], patterns: Optional[List[str]] = None) -> str:
        """Start monitoring file system changes."""
        args = {"paths": paths}
        if patterns:
            args["patterns"] = patterns
        
        result = self.execute_mcp_tool("file-watcher", "watcher_start_monitoring", args)
        if "error" in result:
            return f"Error starting watcher: {result['error']}"
        
        content = result.get("content", [{}])[0].get("text", "")
        try:
            data = json.loads(content)
            watcher_id = data.get("watcherId")
            if watcher_id:
                self.active_watchers[watcher_id] = paths
            return f"✅ Started monitoring {len(paths)} path(s) - Watcher ID: {watcher_id}"
        except:
            return "✅ File monitoring started"
    
    def watcher_get_changes(self, watcher_id: Optional[str] = None, limit: int = 10) -> str:
        """Get recent file system changes."""
        args = {"limit": limit}
        if watcher_id:
            args["watcherId"] = watcher_id
        
        result = self.execute_mcp_tool("file-watcher", "watcher_get_changes", args)
        if "error" in result:
            return f"Error getting changes: {result['error']}"
        
        content = result.get("content", [{}])[0].get("text", "")
        try:
            data = json.loads(content)
            summary = data.get("summary", {})
            changes = summary.get("recentChanges", [])
            
            if not changes:
                return "No recent changes detected"
            
            change_summary = f"📁 Recent Changes ({summary.get('totalChanges', 0)} total):\n"
            for change in changes[:5]:
                change_summary += f"- {change.get('type', '?')}: {change.get('path', 'unknown')}\n"
            
            return change_summary
        except:
            return "Changes detected but parsing failed"
    
    def process(self, prompt: str, speech_module=None) -> str:
        """
        Process user input and route to appropriate MCP tools.
        """
        self.memory = Memory()
        self.memory.push('user', prompt)
        
        # Load system prompt
        system_prompt = self.load_prompt(
            os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "base", "mcp_agent.txt")
        )
        
        # Enhance prompt with available tools
        tools_description = "\n".join([
            f"**{server}**: {', '.join(tools.keys())}"
            for server, tools in self.available_tools.items()
        ])
        
        enhanced_prompt = f"{system_prompt}\n\nAvailable MCP Tools:\n{tools_description}\n\nUser Request: {prompt}"
        self.memory.push('system', enhanced_prompt)
        
        try:
            # Get LLM response
            response, reasoning = asyncio.run(self.llm_request())
            self.last_answer = response
            self.last_reasoning = reasoning
            
            # Parse and execute MCP commands
            if "cursor_open_file" in response.lower():
                return self.parse_and_execute_cursor_commands(response)
            elif "memory_" in response.lower():
                return self.parse_and_execute_memory_commands(response)
            elif "watcher_" in response.lower():
                return self.parse_and_execute_watcher_commands(response)
            else:
                return response
                
        except Exception as e:
            error_msg = f"Error processing MCP request: {str(e)}"
            self.success = False
            return error_msg
    
    def parse_and_execute_cursor_commands(self, response: str) -> str:
        """Parse and execute Cursor control commands."""
        # Simple parsing for demonstration
        if "open file" in response.lower():
            # Extract file path from response
            words = response.split()
            for i, word in enumerate(words):
                if word.endswith(('.py', '.js', '.ts', '.md', '.txt', '.json')):
                    return self.cursor_open_file(word)
        
        return response + "\n\n💡 Enhanced MCP integration available for Cursor commands!"
    
    def parse_and_execute_memory_commands(self, response: str) -> str:
        """Parse and execute memory management commands."""
        if "save" in response.lower() and "context" in response.lower():
            # Save the current conversation context
            context = f"User request: {self.memory.get()[-2]['content'] if len(self.memory.get()) > 1 else 'Unknown'}"
            return self.memory_save_context(context, "conversation")
        elif "load" in response.lower() and "context" in response.lower():
            return self.memory_load_context()
        
        return response + "\n\n💡 Enhanced MCP integration available for memory commands!"
    
    def parse_and_execute_watcher_commands(self, response: str) -> str:
        """Parse and execute file watcher commands."""
        if "start monitoring" in response.lower() or "watch" in response.lower():
            # Default to current directory
            return self.watcher_start_monitoring([os.getcwd()])
        elif "get changes" in response.lower() or "changes" in response.lower():
            return self.watcher_get_changes()
        
        return response + "\n\n💡 Enhanced MCP integration available for file watching!"
    
    def get_mcp_status(self) -> str:
        """Get status of all MCP integrations."""
        status = "🔧 **Enhanced MCP Agent Status**\n\n"
        
        # MCP Servers
        status += f"**Discovered MCP Servers**: {len(self.mcp_servers)}\n"
        for name, config in self.mcp_servers.items():
            status += f"- {name}: {config.get('command', 'unknown')}\n"
        
        # Active watchers
        status += f"\n**Active File Watchers**: {len(self.active_watchers)}\n"
        for watcher_id, paths in self.active_watchers.items():
            status += f"- {watcher_id}: monitoring {len(paths)} path(s)\n"
        
        # Memory session
        status += f"\n**Memory Session**: {self.memory_session_id or 'Not started'}\n"
        
        # Voice integration status
        if self.voice_enabled:
            voice_status = self.voice_processor.get_status() if self.voice_processor else {}
            status += f"\n**Voice Integration**: {'Enabled' if self.voice_enabled else 'Disabled'}\n"
            if voice_status:
                status += f"- Listening: {voice_status.get('listening', False)}\n"
                status += f"- Wake word mode: {voice_status.get('wake_word_mode', False)}\n"
                status += f"- Commands processed: {voice_status.get('command_history_count', 0)}\n"
        
        return status
    
    def _initialize_voice_system(self):
        """Initialize voice command processing system"""
        if not VOICE_AVAILABLE:
            if self.verbose:
                pretty_print("Voice libraries not available", color="warning")
            return
        
        try:
            self.voice_processor = VoiceCommandProcessor(
                stt_engine="google",
                tts_rate=180,
                tts_volume=0.8,
                wake_word="agenticsseek"
            )
            
            # Set up voice command handler
            self.voice_processor.on_command_detected = self._handle_voice_command
            
            if self.verbose:
                pretty_print("Voice system initialized successfully", color="success")
                
        except Exception as e:
            if self.verbose:
                pretty_print(f"Failed to initialize voice system: {e}", color="failure")
            self.voice_enabled = False
    
    def _handle_voice_command(self, command: VoiceCommand) -> str:
        """Handle voice commands and route to appropriate MCP tools"""
        try:
            if self.verbose:
                pretty_print(f"Voice command: {command.original_text}", color="info")
            
            if command.command_type == CommandType.MCP_CONTROL:
                return self._execute_mcp_voice_command(command)
            elif command.command_type == CommandType.AGENT_REQUEST:
                return self._execute_agent_voice_command(command)
            else:
                return f"Command received: {command.action}"
                
        except Exception as e:
            error_msg = f"Error processing voice command: {e}"
            if self.verbose:
                pretty_print(error_msg, color="failure")
            return "Sorry, I encountered an error processing that voice command."
    
    def _execute_mcp_voice_command(self, command: VoiceCommand) -> str:
        """Execute MCP-specific voice commands"""
        action = command.action
        params = command.parameters
        
        try:
            if action == "cursor_open_file":
                file_path = params.get("file_path", "")
                result = self.cursor_open_file(file_path)
                return f"Opening {file_path} in Cursor. {result}"
            
            elif action == "cursor_create_file":
                file_name = params.get("file_name", "")
                result = self.cursor_create_file(file_name, "")
                return f"Creating file {file_name}. {result}"
            
            elif action == "cursor_search_files":
                query = params.get("query", "")
                result = self.cursor_search_files(query)
                return f"Searching for '{query}' in files. {result}"
            
            elif action == "memory_save":
                content = params.get("content", "")
                result = self.memory_save_context(content, "voice_note")
                return f"Saved to memory: {content[:50]}... {result}"
            
            elif action == "file_watch":
                path = params.get("path", "")
                result = self.watcher_start_monitoring([path])
                return f"Watching {path} for changes. {result}"
            
            else:
                return f"MCP command '{action}' not implemented"
                
        except Exception as e:
            return f"Error executing MCP command: {e}"
    
    def _execute_agent_voice_command(self, command: VoiceCommand) -> str:
        """Execute general agent voice commands"""
        action = command.action
        params = command.parameters
        
        try:
            if action == "code_request":
                description = params.get("description", "")
                # Route to code agent or process request
                return f"I'll help you write {description}. Let me process this request."
            
            elif action == "web_browse":
                url = params.get("url", "")
                return f"I'll browse to {url} for you."
            
            elif action == "web_search":
                query = params.get("query", "")
                return f"Searching the web for '{query}'."
            
            elif action == "translate":
                text = params.get("text", "")
                target = params.get("target_language", "")
                return f"Translating '{text[:30]}...' to {target}."
            
            else:
                return f"Agent command '{action}' not implemented"
                
        except Exception as e:
            return f"Error executing agent command: {e}"
    
    def start_voice_control(self):
        """Start voice command listening"""
        if not self.voice_enabled:
            return "Voice control not available"
        
        if not self.voice_processor:
            self._initialize_voice_system()
        
        if self.voice_processor:
            self.voice_processor.start_listening()
            return "Voice control started. Say 'AgenticSeek' to get my attention."
        else:
            return "Failed to start voice control"
    
    def stop_voice_control(self):
        """Stop voice command listening"""
        if self.voice_processor:
            self.voice_processor.stop_listening()
            return "Voice control stopped"
        return "Voice control was not active"
    
    def toggle_voice_mode(self):
        """Toggle between wake word and continuous listening"""
        if self.voice_processor:
            self.voice_processor.toggle_wake_word_mode()
            mode = "wake word" if self.voice_processor.wake_word_mode else "continuous"
            return f"Switched to {mode} mode"
        return "Voice control not available"
    
    def get_voice_status(self) -> Dict[str, Any]:
        """Get voice system status"""
        if not self.voice_enabled or not self.voice_processor:
            return {"enabled": False, "reason": "Voice system not available"}
        
        return {
            "enabled": True,
            "status": self.voice_processor.get_status(),
            "recent_commands": self.voice_processor.get_command_history(5)
        }