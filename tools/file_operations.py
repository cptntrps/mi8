#!/usr/bin/env python3
"""
Real File Operations Tool for AgenticSeek
"""

import os
import shutil
import glob
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import mimetypes
from datetime import datetime

class FileOperationsTool:
    """Real file system operations"""
    
    def __init__(self, safe_mode: bool = True):
        self.safe_mode = safe_mode
        self.allowed_extensions = {
            '.txt', '.py', '.js', '.html', '.css', '.md', '.json', '.yml', '.yaml',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
            '.mp3', '.mp4', '.avi', '.mkv', '.pdf', '.doc', '.docx'
        }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Actually read file contents"""
        try:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                return {"error": f"File {file_path} does not exist"}
            
            if not path.is_file():
                return {"error": f"{file_path} is not a file"}
            
            # Check file size (limit to 10MB for safety)
            if path.stat().st_size > 10 * 1024 * 1024:
                return {"error": "File too large (>10MB)"}
            
            # Determine file type
            mime_type, _ = mimetypes.guess_type(str(path))
            
            # Read text files
            if mime_type and mime_type.startswith('text'):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return {
                    "success": True,
                    "content": content,
                    "file_path": str(path),
                    "size": path.stat().st_size,
                    "type": "text"
                }
            else:
                return {
                    "success": True,
                    "content": f"Binary file: {mime_type or 'unknown type'}",
                    "file_path": str(path),
                    "size": path.stat().st_size,
                    "type": "binary"
                }
                
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
    
    def write_file(self, file_path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
        """Actually write file contents"""
        try:
            path = Path(file_path).expanduser().resolve()
            
            # Safety check - only allow writing to user directories
            if self.safe_mode:
                home = Path.home()
                tmp = Path("/tmp")
                if not (str(path).startswith(str(home)) or str(path).startswith(str(tmp))):
                    return {"error": "Can only write to home directory or /tmp for safety"}
            
            # Create parent directories if needed
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": str(path),
                "size": len(content),
                "message": "File written successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to write file: {str(e)}"}
    
    def list_directory(self, dir_path: str, show_hidden: bool = False) -> Dict[str, Any]:
        """Actually list directory contents"""
        try:
            path = Path(dir_path).expanduser().resolve()
            
            if not path.exists():
                return {"error": f"Directory {dir_path} does not exist"}
            
            if not path.is_dir():
                return {"error": f"{dir_path} is not a directory"}
            
            items = []
            for item in path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "permissions": oct(stat.st_mode)[-3:]
                })
            
            return {
                "success": True,
                "directory": str(path),
                "items": sorted(items, key=lambda x: (x["type"], x["name"])),
                "count": len(items)
            }
            
        except Exception as e:
            return {"error": f"Failed to list directory: {str(e)}"}
    
    def search_files(self, pattern: str, directory: str = ".", recursive: bool = True) -> Dict[str, Any]:
        """Actually search for files"""
        try:
            path = Path(directory).expanduser().resolve()
            
            if not path.exists() or not path.is_dir():
                return {"error": f"Directory {directory} does not exist"}
            
            if recursive:
                search_pattern = str(path / "**" / pattern)
                matches = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = str(path / pattern)
                matches = glob.glob(search_pattern)
            
            results = []
            for match in matches[:100]:  # Limit results
                match_path = Path(match)
                if match_path.is_file():
                    stat = match_path.stat()
                    results.append({
                        "path": match,
                        "name": match_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": str(path),
                "matches": results,
                "count": len(results)
            }
            
        except Exception as e:
            return {"error": f"Failed to search files: {str(e)}"}
    
    def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """Actually create directory"""
        try:
            path = Path(dir_path).expanduser().resolve()
            
            # Safety check
            if self.safe_mode:
                home = Path.home()
                tmp = Path("/tmp")
                if not (str(path).startswith(str(home)) or str(path).startswith(str(tmp))):
                    return {"error": "Can only create directories in home or /tmp for safety"}
            
            path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "directory": str(path),
                "message": "Directory created successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to create directory: {str(e)}"}
    
    def move_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Actually move/rename files"""
        try:
            src_path = Path(src).expanduser().resolve()
            dst_path = Path(dst).expanduser().resolve()
            
            if not src_path.exists():
                return {"error": f"Source {src} does not exist"}
            
            # Safety check
            if self.safe_mode:
                home = Path.home()
                tmp = Path("/tmp")
                for path in [src_path, dst_path]:
                    if not (str(path).startswith(str(home)) or str(path).startswith(str(tmp))):
                        return {"error": "Can only move files within home or /tmp for safety"}
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            
            return {
                "success": True,
                "source": str(src_path),
                "destination": str(dst_path),
                "message": "File moved successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to move file: {str(e)}"}
    
    def copy_file(self, src: str, dst: str) -> Dict[str, Any]:
        """Actually copy files"""
        try:
            src_path = Path(src).expanduser().resolve()
            dst_path = Path(dst).expanduser().resolve()
            
            if not src_path.exists():
                return {"error": f"Source {src} does not exist"}
            
            # Safety check
            if self.safe_mode:
                home = Path.home()
                tmp = Path("/tmp")
                for path in [src_path, dst_path]:
                    if not (str(path).startswith(str(home)) or str(path).startswith(str(tmp))):
                        return {"error": "Can only copy files within home or /tmp for safety"}
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if src_path.is_file():
                shutil.copy2(str(src_path), str(dst_path))
            else:
                shutil.copytree(str(src_path), str(dst_path))
            
            return {
                "success": True,
                "source": str(src_path),
                "destination": str(dst_path),
                "message": "File copied successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to copy file: {str(e)}"}
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Actually delete files (with safety checks)"""
        try:
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                return {"error": f"File {file_path} does not exist"}
            
            # Extra safety check for deletion
            if self.safe_mode:
                home = Path.home()
                tmp = Path("/tmp")
                if not (str(path).startswith(str(home)) or str(path).startswith(str(tmp))):
                    return {"error": "Can only delete files in home or /tmp for safety"}
                
                # Don't delete important directories
                important_dirs = {str(home), str(home / "Documents"), str(home / "Desktop")}
                if str(path) in important_dirs:
                    return {"error": "Cannot delete important directories"}
            
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(str(path))
            
            return {
                "success": True,
                "deleted": str(path),
                "message": "File deleted successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to delete file: {str(e)}"}

# Tool registry
def get_file_tools():
    """Get all file operation tools"""
    file_ops = FileOperationsTool()
    
    return {
        "read_file": file_ops.read_file,
        "write_file": file_ops.write_file, 
        "list_directory": file_ops.list_directory,
        "search_files": file_ops.search_files,
        "create_directory": file_ops.create_directory,
        "move_file": file_ops.move_file,
        "copy_file": file_ops.copy_file,
        "delete_file": file_ops.delete_file
    }