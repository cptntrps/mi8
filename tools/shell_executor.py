#!/usr/bin/env python3
"""
Real Shell Command Executor for AgenticSeek
"""

import subprocess
import os
import signal
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

class ShellExecutor:
    """Execute actual shell commands safely"""
    
    def __init__(self, safe_mode: bool = True):
        self.safe_mode = safe_mode
        self.timeout = 30  # 30 second timeout
        
        # Allowed commands in safe mode
        self.safe_commands = {
            'ls', 'dir', 'pwd', 'cd', 'cat', 'head', 'tail', 'grep', 'find',
            'echo', 'which', 'whoami', 'date', 'uptime', 'df', 'du', 'free',
            'ps', 'top', 'htop', 'git', 'python', 'python3', 'pip', 'pip3',
            'node', 'npm', 'yarn', 'curl', 'wget', 'ping', 'nslookup',
            'make', 'cmake', 'gcc', 'g++', 'rustc', 'cargo', 'go',
            'docker', 'kubectl', 'systemctl', 'journalctl'
        }
        
        # Dangerous commands to block
        self.dangerous_commands = {
            'rm', 'rmdir', 'dd', 'mkfs', 'fdisk', 'mount', 'umount',
            'su', 'sudo', 'passwd', 'useradd', 'userdel', 'chmod',
            'chown', 'iptables', 'ufw', 'systemctl', 'service',
            'shutdown', 'reboot', 'halt', 'init', 'kill', 'killall'
        }
    
    def execute_command(self, command: str, working_dir: Optional[str] = None) -> Dict[str, Any]:
        """Execute shell command and return results"""
        try:
            # Parse command
            cmd_parts = command.strip().split()
            if not cmd_parts:
                return {"error": "Empty command"}
            
            base_command = cmd_parts[0]
            
            # Safety checks
            if self.safe_mode:
                if base_command in self.dangerous_commands:
                    return {"error": f"Command '{base_command}' is not allowed in safe mode"}
                
                if base_command not in self.safe_commands:
                    return {"error": f"Command '{base_command}' is not in safe command list"}
            
            # Set working directory
            if working_dir:
                work_path = Path(working_dir).expanduser().resolve()
                if not work_path.exists() or not work_path.is_dir():
                    return {"error": f"Working directory {working_dir} does not exist"}
                cwd = str(work_path)
            else:
                cwd = os.getcwd()
            
            # Execute command
            start_time = time.time()
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "command": command,
                "working_directory": cwd,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": round(execution_time, 3)
            }
            
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {self.timeout} seconds"}
        except Exception as e:
            return {"error": f"Failed to execute command: {str(e)}"}
    
    def execute_python_script(self, script_content: str, args: List[str] = None) -> Dict[str, Any]:
        """Execute Python script content"""
        try:
            # Create temporary script file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            try:
                # Build command
                command = ['python3', script_path]
                if args:
                    command.extend(args)
                
                # Execute
                start_time = time.time()
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "script_length": len(script_content),
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": round(execution_time, 3)
                }
                
            finally:
                # Clean up temp file
                os.unlink(script_path)
                
        except subprocess.TimeoutExpired:
            return {"error": f"Python script timed out after {self.timeout} seconds"}
        except Exception as e:
            return {"error": f"Failed to execute Python script: {str(e)}"}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get actual system information"""
        try:
            info = {}
            
            # Basic system info
            commands = {
                "os": "uname -a",
                "uptime": "uptime",
                "cpu_info": "cat /proc/cpuinfo | grep 'model name' | head -1",
                "memory": "free -h",
                "disk_space": "df -h",
                "current_user": "whoami",
                "current_directory": "pwd",
                "python_version": "python3 --version",
                "git_version": "git --version 2>/dev/null || echo 'git not installed'"
            }
            
            for key, cmd in commands.items():
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info[key] = result.stdout.strip()
                else:
                    info[key] = f"Command failed: {result.stderr.strip()}"
            
            return {
                "success": True,
                "system_info": info
            }
            
        except Exception as e:
            return {"error": f"Failed to get system info: {str(e)}"}
    
    def check_process(self, process_name: str) -> Dict[str, Any]:
        """Check if a process is running"""
        try:
            result = subprocess.run(
                f"pgrep -f '{process_name}'",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                return {
                    "success": True,
                    "process_name": process_name,
                    "running": True,
                    "pids": [int(pid) for pid in pids if pid]
                }
            else:
                return {
                    "success": True,
                    "process_name": process_name,
                    "running": False,
                    "pids": []
                }
                
        except Exception as e:
            return {"error": f"Failed to check process: {str(e)}"}

# Tool registry
def get_shell_tools():
    """Get all shell execution tools"""
    shell = ShellExecutor()
    
    return {
        "execute_command": shell.execute_command,
        "execute_python_script": shell.execute_python_script,
        "get_system_info": shell.get_system_info,
        "check_process": shell.check_process
    }