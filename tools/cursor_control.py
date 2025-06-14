#!/usr/bin/env python3
"""
Real Cursor IDE Control for AgenticSeek
"""

import subprocess
import os
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

class CursorController:
    """Actually control Cursor IDE"""
    
    def __init__(self):
        self.cursor_command = self._find_cursor_command()
    
    def _find_cursor_command(self) -> Optional[str]:
        """Find the cursor command on the system"""
        possible_commands = ['cursor', 'code-cursor', '/usr/local/bin/cursor']
        
        for cmd in possible_commands:
            try:
                result = subprocess.run(['which', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    return cmd
            except:
                continue
        
        # Check for installed Cursor in common locations
        common_paths = [
            '/usr/local/bin/cursor',
            '/opt/cursor/cursor',
            '~/.local/bin/cursor',
            '/Applications/Cursor.app/Contents/Resources/app/bin/cursor'  # macOS
        ]
        
        for path in common_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists() and expanded_path.is_file():
                return str(expanded_path)
        
        return None
    
    def open_file(self, file_path: str, line_number: Optional[int] = None) -> Dict[str, Any]:
        """Actually open file in Cursor"""
        try:
            if not self.cursor_command:
                return {"error": "Cursor command not found. Is Cursor IDE installed?"}
            
            path = Path(file_path).expanduser().resolve()
            
            # Build command
            cmd = [self.cursor_command]
            
            if line_number:
                cmd.extend(['-g', f'{path}:{line_number}'])
            else:
                cmd.append(str(path))
            
            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "action": "opened_file",
                    "file_path": str(path),
                    "line_number": line_number,
                    "message": f"Opened {path} in Cursor IDE"
                }
            else:
                return {
                    "error": f"Failed to open file: {result.stderr}",
                    "exit_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {"error": "Cursor command timed out"}
        except Exception as e:
            return {"error": f"Failed to open file in Cursor: {str(e)}"}
    
    def open_directory(self, dir_path: str) -> Dict[str, Any]:
        """Actually open directory in Cursor"""
        try:
            if not self.cursor_command:
                return {"error": "Cursor command not found. Is Cursor IDE installed?"}
            
            path = Path(dir_path).expanduser().resolve()
            
            if not path.exists() or not path.is_dir():
                return {"error": f"Directory {dir_path} does not exist"}
            
            # Execute command
            result = subprocess.run([self.cursor_command, str(path)], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "action": "opened_directory", 
                    "directory_path": str(path),
                    "message": f"Opened {path} directory in Cursor IDE"
                }
            else:
                return {
                    "error": f"Failed to open directory: {result.stderr}",
                    "exit_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {"error": "Cursor command timed out"}
        except Exception as e:
            return {"error": f"Failed to open directory in Cursor: {str(e)}"}
    
    def create_and_open_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """Create file and open it in Cursor"""
        try:
            path = Path(file_path).expanduser().resolve()
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Open in Cursor
            open_result = self.open_file(str(path))
            
            if open_result.get("success"):
                return {
                    "success": True,
                    "action": "created_and_opened",
                    "file_path": str(path),
                    "content_length": len(content),
                    "message": f"Created and opened {path} in Cursor IDE"
                }
            else:
                return {
                    "success": True,
                    "action": "created_only",
                    "file_path": str(path),
                    "content_length": len(content),
                    "message": f"Created {path} but failed to open in Cursor",
                    "cursor_error": open_result.get("error")
                }
                
        except Exception as e:
            return {"error": f"Failed to create and open file: {str(e)}"}
    
    def is_cursor_running(self) -> Dict[str, Any]:
        """Check if Cursor is currently running"""
        try:
            # Check for cursor processes
            result = subprocess.run(['pgrep', '-f', 'cursor'], capture_output=True, text=True)
            
            running = result.returncode == 0
            pids = []
            
            if running and result.stdout.strip():
                pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
            
            return {
                "success": True,
                "cursor_running": running,
                "process_count": len(pids),
                "pids": pids
            }
            
        except Exception as e:
            return {"error": f"Failed to check Cursor status: {str(e)}"}
    
    def get_cursor_info(self) -> Dict[str, Any]:
        """Get Cursor IDE information"""
        try:
            info = {
                "cursor_command": self.cursor_command,
                "cursor_available": self.cursor_command is not None
            }
            
            if self.cursor_command:
                # Try to get version
                try:
                    result = subprocess.run([self.cursor_command, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        info["version"] = result.stdout.strip()
                except:
                    info["version"] = "Could not determine version"
            
            # Check if running
            status = self.is_cursor_running()
            if status.get("success"):
                info.update({
                    "running": status["cursor_running"],
                    "process_count": status["process_count"]
                })
            
            return {
                "success": True,
                "cursor_info": info
            }
            
        except Exception as e:
            return {"error": f"Failed to get Cursor info: {str(e)}"}

# Tool registry
def get_cursor_tools():
    """Get all Cursor IDE control tools"""
    cursor = CursorController()
    
    return {
        "open_file": cursor.open_file,
        "open_directory": cursor.open_directory,
        "create_and_open_file": cursor.create_and_open_file,
        "is_cursor_running": cursor.is_cursor_running,
        "get_cursor_info": cursor.get_cursor_info
    }