#!/usr/bin/env python3
"""
Real Database Operations for AgenticSeek
"""

import sqlite3
import json
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import tempfile

class DatabaseManager:
    """Actually execute database operations"""
    
    def __init__(self):
        self.connections = {}  # Store active connections
        self.max_results = 1000  # Limit query results
    
    def connect_sqlite(self, db_path: str) -> Dict[str, Any]:
        """Actually connect to SQLite database"""
        try:
            path = Path(db_path).expanduser().resolve()
            
            # Create database if it doesn't exist
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                # Create empty database
                conn = sqlite3.connect(str(path))
                conn.close()
            
            # Connect to database
            conn = sqlite3.connect(str(path))
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Store connection
            conn_id = f"sqlite_{str(path)}"
            self.connections[conn_id] = conn
            
            return {
                "success": True,
                "connection_id": conn_id,
                "database_path": str(path),
                "database_type": "sqlite",
                "message": f"Connected to SQLite database: {path}"
            }
            
        except Exception as e:
            return {"error": f"Failed to connect to SQLite database: {str(e)}"}
    
    def execute_query(self, connection_id: str, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Actually execute SQL query"""
        try:
            if connection_id not in self.connections:
                return {"error": f"Connection {connection_id} not found"}
            
            conn = self.connections[connection_id]
            cursor = conn.cursor()
            
            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Handle different query types
            query_lower = query.strip().lower()
            
            if query_lower.startswith(('select', 'with')):
                # SELECT query - fetch results
                rows = cursor.fetchmany(self.max_results)
                columns = [description[0] for description in cursor.description] if cursor.description else []
                
                # Convert to list of dicts
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))
                
                return {
                    "success": True,
                    "query_type": "select",
                    "columns": columns,
                    "results": results,
                    "row_count": len(results),
                    "query": query
                }
                
            elif query_lower.startswith(('insert', 'update', 'delete')):
                # Modification query
                conn.commit()
                row_count = cursor.rowcount
                
                return {
                    "success": True,
                    "query_type": "modification",
                    "affected_rows": row_count,
                    "query": query
                }
                
            elif query_lower.startswith(('create', 'drop', 'alter')):
                # DDL query
                conn.commit()
                
                return {
                    "success": True,
                    "query_type": "ddl",
                    "message": "Schema operation completed",
                    "query": query
                }
                
            else:
                # Other queries
                conn.commit()
                return {
                    "success": True,
                    "query_type": "other",
                    "message": "Query executed successfully",
                    "query": query
                }
                
        except Exception as e:
            return {"error": f"Failed to execute query: {str(e)}"}
    
    def get_tables(self, connection_id: str) -> Dict[str, Any]:
        """Actually get list of tables"""
        try:
            if connection_id not in self.connections:
                return {"error": f"Connection {connection_id} not found"}
            
            # SQLite system query
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            result = self.execute_query(connection_id, query)
            
            if result.get("success"):
                tables = [row["name"] for row in result["results"]]
                return {
                    "success": True,
                    "tables": tables,
                    "table_count": len(tables)
                }
            else:
                return result
                
        except Exception as e:
            return {"error": f"Failed to get tables: {str(e)}"}
    
    def get_table_schema(self, connection_id: str, table_name: str) -> Dict[str, Any]:
        """Actually get table schema"""
        try:
            if connection_id not in self.connections:
                return {"error": f"Connection {connection_id} not found"}
            
            # Get column information
            query = f"PRAGMA table_info({table_name})"
            result = self.execute_query(connection_id, query)
            
            if result.get("success"):
                columns = []
                for row in result["results"]:
                    columns.append({
                        "name": row["name"],
                        "type": row["type"],
                        "not_null": bool(row["notnull"]),
                        "default_value": row["dflt_value"],
                        "primary_key": bool(row["pk"])
                    })
                
                # Get indexes
                index_query = f"PRAGMA index_list({table_name})"
                index_result = self.execute_query(connection_id, index_query)
                indexes = index_result.get("results", []) if index_result.get("success") else []
                
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": columns,
                    "column_count": len(columns),
                    "indexes": indexes
                }
            else:
                return result
                
        except Exception as e:
            return {"error": f"Failed to get table schema: {str(e)}"}
    
    def create_sample_table(self, connection_id: str, table_name: str = "sample_data") -> Dict[str, Any]:
        """Create a sample table with data for testing"""
        try:
            if connection_id not in self.connections:
                return {"error": f"Connection {connection_id} not found"}
            
            # Create table
            create_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            create_result = self.execute_query(connection_id, create_query)
            if not create_result.get("success"):
                return create_result
            
            # Insert sample data
            sample_data = [
                ("Alice Johnson", "alice@example.com", 28),
                ("Bob Smith", "bob@example.com", 34),
                ("Carol Davis", "carol@example.com", 22),
                ("David Wilson", "david@example.com", 41)
            ]
            
            insert_query = f"INSERT OR IGNORE INTO {table_name} (name, email, age) VALUES (?, ?, ?)"
            
            for data in sample_data:
                self.execute_query(connection_id, insert_query, list(data))
            
            return {
                "success": True,
                "table_name": table_name,
                "sample_records": len(sample_data),
                "message": f"Created sample table '{table_name}' with {len(sample_data)} records"
            }
            
        except Exception as e:
            return {"error": f"Failed to create sample table: {str(e)}"}
    
    def close_connection(self, connection_id: str) -> Dict[str, Any]:
        """Actually close database connection"""
        try:
            if connection_id not in self.connections:
                return {"error": f"Connection {connection_id} not found"}
            
            conn = self.connections[connection_id]
            conn.close()
            del self.connections[connection_id]
            
            return {
                "success": True,
                "connection_id": connection_id,
                "message": "Database connection closed"
            }
            
        except Exception as e:
            return {"error": f"Failed to close connection: {str(e)}"}
    
    def list_connections(self) -> Dict[str, Any]:
        """List all active database connections"""
        try:
            connections = []
            for conn_id in self.connections.keys():
                if conn_id.startswith("sqlite_"):
                    db_path = conn_id.replace("sqlite_", "")
                    connections.append({
                        "connection_id": conn_id,
                        "type": "sqlite",
                        "database": db_path
                    })
            
            return {
                "success": True,
                "connections": connections,
                "connection_count": len(connections)
            }
            
        except Exception as e:
            return {"error": f"Failed to list connections: {str(e)}"}

# Tool registry
def get_database_tools():
    """Get all database operation tools"""
    db_manager = DatabaseManager()
    
    return {
        "connect_sqlite": db_manager.connect_sqlite,
        "execute_query": db_manager.execute_query,
        "get_tables": db_manager.get_tables,
        "get_table_schema": db_manager.get_table_schema,
        "create_sample_table": db_manager.create_sample_table,
        "close_connection": db_manager.close_connection,
        "list_connections": db_manager.list_connections
    }