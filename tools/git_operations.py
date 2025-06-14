#!/usr/bin/env python3
"""
Real Git Operations Tool for AgenticSeek
"""

import subprocess
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class GitOperations:
    """Execute actual git operations"""
    
    def __init__(self, safe_mode: bool = True):
        self.safe_mode = safe_mode
        self.timeout = 30
    
    def git_status(self, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Get actual git status"""
        try:
            if repo_path:
                path = Path(repo_path).expanduser().resolve()
                if not path.exists():
                    return {"error": f"Repository path {repo_path} does not exist"}
                cwd = str(path)
            else:
                cwd = os.getcwd()
            
            # Check if it's a git repo
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                return {"error": "Not a git repository"}
            
            # Get status
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                # Parse status output
                lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                files = {
                    "modified": [],
                    "added": [],
                    "deleted": [],
                    "untracked": [],
                    "renamed": []
                }
                
                for line in lines:
                    if len(line) >= 3:
                        status = line[:2]
                        filename = line[3:]
                        
                        if status.startswith('M'):
                            files["modified"].append(filename)
                        elif status.startswith('A'):
                            files["added"].append(filename)
                        elif status.startswith('D'):
                            files["deleted"].append(filename)
                        elif status.startswith('??'):
                            files["untracked"].append(filename)
                        elif status.startswith('R'):
                            files["renamed"].append(filename)
                
                # Get current branch
                branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                            cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
                current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
                
                return {
                    "success": True,
                    "repository": cwd,
                    "current_branch": current_branch,
                    "files": files,
                    "has_changes": any(files.values()),
                    "total_changes": sum(len(file_list) for file_list in files.values())
                }
            else:
                return {"error": f"Git status failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Git command timed out"}
        except Exception as e:
            return {"error": f"Failed to get git status: {str(e)}"}
    
    def git_add(self, files: List[str], repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Add files to git staging"""
        try:
            cwd = str(Path(repo_path).expanduser().resolve()) if repo_path else os.getcwd()
            
            # Add files
            cmd = ['git', 'add'] + files
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "added_files": files,
                    "message": f"Added {len(files)} files to staging"
                }
            else:
                return {"error": f"Git add failed: {result.stderr}"}
                
        except Exception as e:
            return {"error": f"Failed to add files: {str(e)}"}
    
    def git_commit(self, message: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Commit staged changes"""
        try:
            cwd = str(Path(repo_path).expanduser().resolve()) if repo_path else os.getcwd()
            
            # Commit
            result = subprocess.run(['git', 'commit', '-m', message], 
                                  cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                           cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
                commit_hash = hash_result.stdout.strip()[:8] if hash_result.returncode == 0 else "unknown"
                
                return {
                    "success": True,
                    "commit_message": message,
                    "commit_hash": commit_hash,
                    "message": f"Committed changes: {commit_hash}"
                }
            else:
                return {"error": f"Git commit failed: {result.stderr}"}
                
        except Exception as e:
            return {"error": f"Failed to commit: {str(e)}"}
    
    def git_push(self, remote: str = "origin", branch: Optional[str] = None, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Push commits to remote"""
        try:
            cwd = str(Path(repo_path).expanduser().resolve()) if repo_path else os.getcwd()
            
            # Get current branch if not specified
            if not branch:
                branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                            cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
                branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "main"
            
            # Push
            result = subprocess.run(['git', 'push', remote, branch], 
                                  cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "remote": remote,
                    "branch": branch,
                    "message": f"Pushed {branch} to {remote}"
                }
            else:
                return {"error": f"Git push failed: {result.stderr}"}
                
        except Exception as e:
            return {"error": f"Failed to push: {str(e)}"}
    
    def git_branch(self, action: str, branch_name: Optional[str] = None, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Git branch operations"""
        try:
            cwd = str(Path(repo_path).expanduser().resolve()) if repo_path else os.getcwd()
            
            if action == "list":
                result = subprocess.run(['git', 'branch'], 
                                      cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
                if result.returncode == 0:
                    branches = []
                    current_branch = None
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            if line.startswith('*'):
                                current_branch = line[2:].strip()
                                branches.append({"name": current_branch, "current": True})
                            else:
                                branches.append({"name": line.strip(), "current": False})
                    
                    return {
                        "success": True,
                        "action": "list",
                        "branches": branches,
                        "current_branch": current_branch
                    }
                    
            elif action == "create" and branch_name:
                result = subprocess.run(['git', 'checkout', '-b', branch_name], 
                                      cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
                if result.returncode == 0:
                    return {
                        "success": True,
                        "action": "create",
                        "branch_name": branch_name,
                        "message": f"Created and switched to branch {branch_name}"
                    }
                else:
                    return {"error": f"Failed to create branch: {result.stderr}"}
                    
            elif action == "switch" and branch_name:
                result = subprocess.run(['git', 'checkout', branch_name], 
                                      cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
                if result.returncode == 0:
                    return {
                        "success": True,
                        "action": "switch",
                        "branch_name": branch_name,
                        "message": f"Switched to branch {branch_name}"
                    }
                else:
                    return {"error": f"Failed to switch branch: {result.stderr}"}
            else:
                return {"error": f"Invalid branch action: {action}"}
                
        except Exception as e:
            return {"error": f"Branch operation failed: {str(e)}"}
    
    def git_log(self, limit: int = 10, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Get git commit log"""
        try:
            cwd = str(Path(repo_path).expanduser().resolve()) if repo_path else os.getcwd()
            
            result = subprocess.run(['git', 'log', f'--max-count={limit}', 
                                   '--pretty=format:%H|%an|%ad|%s', '--date=short'], 
                                  cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|', 3)
                        if len(parts) == 4:
                            commits.append({
                                "hash": parts[0][:8],
                                "author": parts[1],
                                "date": parts[2],
                                "message": parts[3]
                            })
                
                return {
                    "success": True,
                    "commits": commits,
                    "commit_count": len(commits)
                }
            else:
                return {"error": f"Git log failed: {result.stderr}"}
                
        except Exception as e:
            return {"error": f"Failed to get git log: {str(e)}"}

# Tool registry
def get_git_tools():
    """Get all git operation tools"""
    git_ops = GitOperations()
    
    return {
        "git_status": git_ops.git_status,
        "git_add": git_ops.git_add,
        "git_commit": git_ops.git_commit,
        "git_push": git_ops.git_push,
        "git_branch": git_ops.git_branch,
        "git_log": git_ops.git_log
    }