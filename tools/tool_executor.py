#!/usr/bin/env python3
"""
Tool Execution Framework for Functional AgenticSeek
"""

import json
import re
from typing import Dict, List, Any, Optional, Callable
import traceback

# Import all tool modules
from .file_operations import get_file_tools
from .shell_executor import get_shell_tools
from .cursor_control import get_cursor_tools
from .database_operations import get_database_tools
from .git_operations import get_git_tools

class ToolExecutor:
    """Execute actual tools based on AI requests"""
    
    def __init__(self):
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        # File operations
        self.tools.update(get_file_tools())
        
        # Shell commands
        self.tools.update(get_shell_tools())
        
        # Cursor IDE control
        self.tools.update(get_cursor_tools())
        
        # Database operations
        self.tools.update(get_database_tools())
        
        # Git operations
        self.tools.update(get_git_tools())
    
    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools with descriptions"""
        tool_descriptions = {
            # File operations
            "read_file": "Read contents of a file",
            "write_file": "Write content to a file", 
            "list_directory": "List contents of a directory",
            "search_files": "Search for files matching a pattern",
            "create_directory": "Create a new directory",
            "move_file": "Move or rename a file",
            "copy_file": "Copy a file or directory",
            "delete_file": "Delete a file or directory",
            
            # Shell commands
            "execute_command": "Execute a shell command",
            "execute_python_script": "Execute Python script code",
            "get_system_info": "Get system information",
            "check_process": "Check if a process is running",
            
            # Cursor IDE
            "open_file": "Open file in Cursor IDE",
            "open_directory": "Open directory in Cursor IDE",
            "create_and_open_file": "Create new file and open in Cursor",
            "is_cursor_running": "Check if Cursor IDE is running",
            "get_cursor_info": "Get Cursor IDE information",
            
            # Database operations
            "connect_sqlite": "Connect to SQLite database",
            "execute_query": "Execute SQL query",
            "get_tables": "Get list of database tables",
            "get_table_schema": "Get schema of a table",
            "create_sample_table": "Create sample table with data",
            "close_connection": "Close database connection",
            "list_connections": "List active database connections",
            
            # Git operations
            "git_status": "Get git repository status",
            "git_add": "Add files to git staging",
            "git_commit": "Commit staged changes",
            "git_push": "Push commits to remote repository",
            "git_branch": "Git branch operations (list, create, switch)",
            "git_log": "Get git commit history"
        }
        
        return tool_descriptions
    
    def parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Parse tool calls from AI response text"""
        tool_calls = []
        
        # Look for tool call patterns like:
        # TOOL_CALL: tool_name(arg1="value1", arg2="value2")
        # [TOOL: tool_name, args: {...}]
        
        patterns = [
            # Pattern 1: TOOL_CALL: function_name(args)
            r'TOOL_CALL:\s*(\w+)\s*\((.*?)\)',
            # Pattern 2: [TOOL: name, args: {...}]
            r'\[TOOL:\s*(\w+)(?:,\s*args:\s*({.*?}))?\]',
            # Pattern 3: Use tool: name with args
            r'use\s+tool:\s*(\w+)(?:\s+with\s+args\s*({.*?}))?',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                tool_name = match.group(1)
                args_str = match.group(2) if len(match.groups()) > 1 else ""
                
                # Parse arguments
                args = {}
                if args_str:
                    try:
                        if args_str.startswith('{'):
                            # JSON format
                            args = json.loads(args_str)
                        else:
                            # Function call format: arg1="value1", arg2=value2
                            arg_matches = re.findall(r'(\w+)=(["\']?)(.*?)\2(?:,|$)', args_str)
                            for arg_name, quote, arg_value in arg_matches:
                                # Try to parse as appropriate type
                                if arg_value.lower() in ['true', 'false']:
                                    args[arg_name] = arg_value.lower() == 'true'
                                elif arg_value.isdigit():
                                    args[arg_name] = int(arg_value)
                                else:
                                    args[arg_name] = arg_value
                    except:
                        # If parsing fails, treat as string
                        args = {"input": args_str}
                
                if tool_name in self.tools:
                    tool_calls.append({
                        "tool": tool_name,
                        "args": args,
                        "raw_match": match.group(0)
                    })
        
        return tool_calls
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool with arguments"""
        try:
            if tool_name not in self.tools:
                return {"error": f"Tool '{tool_name}' not found"}
            
            tool_function = self.tools[tool_name]
            
            # Execute the tool
            result = tool_function(**args)
            
            return {
                "tool": tool_name,
                "args": args,
                "result": result,
                "success": result.get("success", True) if isinstance(result, dict) else True
            }
            
        except Exception as e:
            return {
                "tool": tool_name,
                "args": args,
                "error": f"Tool execution failed: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def process_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Process AI response and execute any tool calls"""
        try:
            # Parse tool calls from response
            tool_calls = self.parse_tool_calls(ai_response)
            
            if not tool_calls:
                return {
                    "success": True,
                    "message": ai_response,
                    "tool_calls": [],
                    "has_tool_calls": False
                }
            
            # Execute tool calls
            executed_tools = []
            for call in tool_calls:
                result = self.execute_tool(call["tool"], call["args"])
                executed_tools.append(result)
            
            return {
                "success": True,
                "message": ai_response,
                "tool_calls": executed_tools,
                "has_tool_calls": True,
                "tool_count": len(executed_tools)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process AI response: {str(e)}",
                "message": ai_response,
                "traceback": traceback.format_exc()
            }
    
    def get_tool_usage_instructions(self) -> str:
        """Get instructions for AI on how to use tools"""
        return """
TOOL USAGE INSTRUCTIONS:

To use tools, include tool calls in your response using this format:
TOOL_CALL: tool_name(arg1="value1", arg2="value2")

Available tools:
""" + "\n".join([f"- {name}: {desc}" for name, desc in self.get_available_tools().items()]) + """

Examples:
- To read a file: TOOL_CALL: read_file(file_path="/path/to/file.txt")
- To execute command: TOOL_CALL: execute_command(command="ls -la")
- To open in Cursor: TOOL_CALL: open_file(file_path="/path/to/file.py", line_number=42)
- To query database: TOOL_CALL: execute_query(connection_id="sqlite_/tmp/test.db", query="SELECT * FROM users")

IMPORTANT:
1. Always use actual file paths, not made-up ones
2. Tool calls will be executed automatically
3. You will receive the actual results
4. Be specific with your tool arguments
5. Use tools to provide real functionality, not just descriptions
"""

# Global tool executor instance
_tool_executor = None

def get_tool_executor() -> ToolExecutor:
    """Get global tool executor instance"""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor