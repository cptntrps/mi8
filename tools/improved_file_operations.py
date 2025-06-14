#!/usr/bin/env python3
"""
Improved File Operations Tool - Fixes AgenticSeek's file handling issues
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

def write_file_properly(file_path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
    """Write file with proper string handling - fixes escaped newline issues"""
    try:
        path = Path(file_path).expanduser().resolve()
        
        # Safety check
        home = Path.home()
        tmp = Path("/tmp")
        if not (str(path).startswith(str(home)) or str(path).startswith(str(tmp))):
            return {"error": "Can only write to home directory or /tmp for safety"}
        
        # Create parent directories if needed
        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Process content to handle escaped characters properly
        if isinstance(content, str):
            # Convert literal \n to actual newlines
            content = content.replace('\\n', '\n').replace('\\t', '\t')
            # Remove surrounding quotes if present
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
        
        # Write file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "file_path": str(path),
            "size": len(content),
            "lines": len(content.split('\n')),
            "message": "File written successfully with proper formatting"
        }
        
    except Exception as e:
        return {"error": f"Failed to write file: {str(e)}"}

def validate_file_content(file_path: str) -> Dict[str, Any]:
    """Validate that file was written correctly"""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": "File does not exist"}
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common issues
        issues = []
        if '\\n' in content:
            issues.append("Contains literal \\n instead of newlines")
        if content.startswith('"') and content.endswith('"'):
            issues.append("Content wrapped in quotes")
        if len(content.strip()) == 0:
            issues.append("File is empty")
        
        return {
            "success": True,
            "file_path": str(path),
            "size": path.stat().st_size,
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "issues": issues,
            "is_valid": len(issues) == 0
        }
        
    except Exception as e:
        return {"error": f"Failed to validate file: {str(e)}"}

# Fix the corrupted roadmap file
def fix_roadmap_file():
    """Fix the corrupted roadmap file AgenticSeek created"""
    corrupted_file = "/tmp/agenticseek_roadmap.md"
    
    if Path(corrupted_file).exists():
        # Read the corrupted content
        with open(corrupted_file, 'r') as f:
            corrupted_content = f.read()
        
        print(f"Corrupted content: {corrupted_content}")
        
        # Fix it
        result = write_file_properly(corrupted_file, corrupted_content)
        print(f"Fix result: {result}")
        
        # Validate
        validation = validate_file_content(corrupted_file)
        print(f"Validation: {validation}")

if __name__ == "__main__":
    fix_roadmap_file()