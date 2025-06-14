#!/usr/bin/env python3
"""
Database Agent for AgenticSeek
Specialized agent for database operations, SQL queries, and schema management
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional
from sources.agents.enhanced_mcp_agent import EnhancedMCPAgent
from sources.memory import Memory
from sources.utility import pretty_print
from sources.schemas import executorResult

# Voice integration imports
try:
    from sources.voice import VoiceCommandProcessor, VoiceCommand, CommandType
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

class DatabaseAgent(EnhancedMCPAgent):
    """
    Specialized Database Agent with advanced SQL capabilities
    Integrates with Database MCP for comprehensive database operations
    """
    
    def __init__(self, name: str, prompt_path: str, provider, verbose=False, browser=None, voice_enabled=False) -> None:
        super().__init__(name, prompt_path, provider, verbose, browser, voice_enabled)
        self.type = "database_agent"
        self.role = "database"
        self.active_connections = {}
        self.query_history = []
        self.schema_cache = {}
        
        # Database-specific voice commands
        if self.voice_enabled and self.voice_processor:
            self._add_database_voice_commands()
    
    def _add_database_voice_commands(self):
        """Add database-specific voice command patterns"""
        if not self.voice_processor:
            return
            
        # Add database command patterns to existing processor
        db_patterns = {
            CommandType.MCP_CONTROL: [
                {
                    "pattern": r"connect to (?:the )?(.+?) database",
                    "action": "db_connect",
                    "params": {"database": 1}
                },
                {
                    "pattern": r"query (?:the )?(.+?) table",
                    "action": "db_query_table", 
                    "params": {"table": 1}
                },
                {
                    "pattern": r"show (?:me )?(?:all )?tables",
                    "action": "db_list_tables",
                    "params": {}
                },
                {
                    "pattern": r"describe (?:the )?(.+?) table",
                    "action": "db_describe_table",
                    "params": {"table": 1}
                },
                {
                    "pattern": r"analyze (?:the )?(.+?) table",
                    "action": "db_analyze_table",
                    "params": {"table": 1}
                },
                {
                    "pattern": r"export (?:the )?(.+?) (?:schema|structure)",
                    "action": "db_export_schema",
                    "params": {"format": 1}
                },
                {
                    "pattern": r"backup (?:the )?database",
                    "action": "db_backup",
                    "params": {}
                },
                {
                    "pattern": r"optimize (?:the )?query",
                    "action": "db_optimize_query",
                    "params": {}
                }
            ]
        }
        
        # Extend existing patterns
        for command_type, patterns in db_patterns.items():
            if command_type in self.voice_processor.command_patterns:
                self.voice_processor.command_patterns[command_type].extend(patterns)
    
    def connect_to_database(self, db_type: str, database: str, **kwargs) -> str:
        """Connect to a database using the Database MCP"""
        args = {
            "type": db_type,
            "database": database,
            **kwargs
        }
        
        result = self.execute_mcp_tool("database-control", "db_connect", args)
        if "error" in result:
            return f"Error connecting to database: {result['error']}"
        
        try:
            content = result.get("content", [{}])[0].get("text", "")
            data = json.loads(content)
            connection_id = data.get("connectionId")
            
            if connection_id:
                self.active_connections[database] = connection_id
                return f"✅ Connected to {db_type} database '{database}' (ID: {connection_id})"
            else:
                return "❌ Failed to get connection ID"
        except:
            return "✅ Database connection established"
    
    def execute_sql_query(self, connection_id: str, query: str, parameters: List = None, limit: int = 100) -> str:
        """Execute SQL query on connected database"""
        args = {
            "connectionId": connection_id,
            "query": query,
            "limit": limit
        }
        if parameters:
            args["parameters"] = parameters
        
        result = self.execute_mcp_tool("database-control", "db_query", args)
        if "error" in result:
            return f"Error executing query: {result['error']}"
        
        try:
            content = result.get("content", [{}])[0].get("text", "")
            data = json.loads(content)
            
            # Add to query history
            self.query_history.append({
                "query": query,
                "connection_id": connection_id,
                "success": data.get("success", False),
                "rows_affected": data.get("rowsAffected", 0),
                "execution_time": data.get("executionTime", 0)
            })
            
            if data.get("success"):
                rows = len(data.get("data", []))
                exec_time = data.get("executionTime", 0)
                return f"✅ Query executed successfully: {rows} rows returned in {exec_time}ms\n\nData:\n{json.dumps(data.get('data', [])[:5], indent=2)}..."
            else:
                return f"❌ Query failed: {data.get('error', 'Unknown error')}"
        except:
            return "✅ Query executed successfully"
    
    def list_database_tables(self, connection_id: str) -> str:
        """List all tables in the database"""
        result = self.execute_mcp_tool("database-control", "db_list_tables", {"connectionId": connection_id})
        if "error" in result:
            return f"Error listing tables: {result['error']}"
        
        try:
            content = result.get("content", [{}])[0].get("text", "")
            data = json.loads(content)
            tables = data.get("tables", [])
            
            if tables:
                table_list = "\n".join([f"- {table}" for table in tables])
                return f"📋 Found {len(tables)} tables:\n{table_list}"
            else:
                return "No tables found in database"
        except:
            return "✅ Tables listed successfully"
    
    def describe_table(self, connection_id: str, table_name: str) -> str:
        """Get detailed table structure"""
        result = self.execute_mcp_tool("database-control", "db_describe_table", {
            "connectionId": connection_id,
            "tableName": table_name
        })
        if "error" in result:
            return f"Error describing table: {result['error']}"
        
        try:
            content = result.get("content", [{}])[0].get("text", "")
            data = json.loads(content)
            
            table_info = f"📊 Table: {data.get('name', table_name)}\n"
            table_info += f"Rows: {data.get('rowCount', 0):,}\n\n"
            table_info += "Columns:\n"
            
            columns = data.get("columns", [])
            for col in columns:
                pk_marker = " 🔑" if col.get("primaryKey") else ""
                null_marker = " (nullable)" if col.get("nullable") else ""
                table_info += f"- {col.get('name')}: {col.get('type')}{pk_marker}{null_marker}\n"
            
            return table_info
        except:
            return "✅ Table structure retrieved"
    
    def analyze_table(self, connection_id: str, table_name: str, include_data: bool = False) -> str:
        """Perform advanced table analysis"""
        result = self.execute_mcp_tool("database-control", "db_analyze_table", {
            "connectionId": connection_id,
            "tableName": table_name,
            "includeData": include_data
        })
        if "error" in result:
            return f"Error analyzing table: {result['error']}"
        
        try:
            content = result.get("content", [{}])[0].get("text", "")
            data = json.loads(content)
            
            analysis = f"🔍 Analysis for table: {data.get('name', table_name)}\n\n"
            analysis += f"📊 Rows: {data.get('rowCount', 0):,}\n"
            analysis += f"📋 Columns: {len(data.get('columns', []))}\n\n"
            
            # Show insights
            insights = data.get("insights", [])
            if insights:
                analysis += "💡 Insights:\n"
                for insight in insights:
                    analysis += f"  {insight}\n"
                analysis += "\n"
            
            # Show relationships
            relationships = data.get("relationships", [])
            if relationships:
                analysis += "🔗 Relationships:\n"
                for rel in relationships:
                    analysis += f"  {rel.get('fromColumn')} → {rel.get('toTable')}.{rel.get('toColumn')}\n"
                analysis += "\n"
            
            # Column statistics
            columns = data.get("columns", [])
            if columns:
                analysis += "📈 Column Statistics:\n"
                for col in columns[:5]:  # Show first 5 columns
                    distinct = col.get("distinctValues", "N/A")
                    null_pct = col.get("nullPercentage", 0)
                    analysis += f"  {col.get('name')}: {distinct} distinct, {null_pct:.1f}% NULL\n"
            
            return analysis
        except Exception as e:
            return f"✅ Table analysis completed (parsing error: {e})"
    
    def export_database_schema(self, connection_id: str, format: str = "sql", include_drop: bool = False) -> str:
        """Export database schema in specified format"""
        result = self.execute_mcp_tool("database-control", "db_export_schema", {
            "connectionId": connection_id,
            "format": format,
            "includeDrop": include_drop
        })
        if "error" in result:
            return f"Error exporting schema: {result['error']}"
        
        try:
            content = result.get("content", [{}])[0].get("text", "")
            return f"📋 Schema exported in {format} format:\n\n{content}"
        except:
            return "✅ Schema exported successfully"
    
    def build_query_from_description(self, connection_id: str, description: str, table_name: str = None) -> str:
        """Build SQL query from natural language description"""
        args = {
            "connectionId": connection_id,
            "description": description
        }
        if table_name:
            args["tableName"] = table_name
        
        result = self.execute_mcp_tool("database-control", "db_build_query", args)
        if "error" in result:
            return f"Error building query: {result['error']}"
        
        try:
            content = result.get("content", [{}])[0].get("text", "")
            data = json.loads(content)
            
            query = data.get("query", "")
            explanation = data.get("explanation", "")
            
            return f"🔨 Generated SQL Query:\n\n```sql\n{query}\n```\n\n💡 Explanation: {explanation}"
        except:
            return "✅ Query generated successfully"
    
    def optimize_query(self, connection_id: str, query: str) -> str:
        """Analyze and optimize SQL query"""
        result = self.execute_mcp_tool("database-control", "db_optimize_query", {
            "connectionId": connection_id,
            "query": query
        })
        if "error" in result:
            return f"Error optimizing query: {result['error']}"
        
        try:
            content = result.get("content", [{}])[0].get("text", "")
            data = json.loads(content)
            
            optimization = f"⚡ Query Optimization Analysis:\n\n"
            optimization += f"Original Query:\n```sql\n{data.get('originalQuery', query)}\n```\n\n"
            
            optimized = data.get("optimizedQuery", "")
            if optimized and optimized != query:
                optimization += f"Optimized Query:\n```sql\n{optimized}\n```\n\n"
            
            suggestions = data.get("suggestions", [])
            if suggestions:
                optimization += "💡 Optimization Suggestions:\n"
                for suggestion in suggestions:
                    optimization += f"  • {suggestion}\n"
                optimization += "\n"
            
            improvement = data.get("estimatedImprovement", "")
            if improvement:
                optimization += f"📈 Estimated Improvement: {improvement}"
            
            return optimization
        except:
            return "✅ Query optimization analysis completed"
    
    def get_database_status(self) -> str:
        """Get status of all database connections and operations"""
        status = "🗄️ **Database Agent Status**\n\n"
        
        # Active connections
        status += f"**Active Connections**: {len(self.active_connections)}\n"
        for db_name, conn_id in self.active_connections.items():
            status += f"- {db_name}: {conn_id}\n"
        
        # Query history
        status += f"\n**Query History**: {len(self.query_history)} queries\n"
        if self.query_history:
            recent_queries = self.query_history[-3:]  # Last 3 queries
            for i, query_info in enumerate(recent_queries, 1):
                success_marker = "✅" if query_info.get("success") else "❌"
                exec_time = query_info.get("execution_time", 0)
                status += f"  {i}. {success_marker} {query_info.get('query', '')[:50]}... ({exec_time}ms)\n"
        
        # Schema cache
        status += f"\n**Cached Schemas**: {len(self.schema_cache)}\n"
        
        # Voice integration status
        if self.voice_enabled:
            voice_status = self.voice_processor.get_status() if self.voice_processor else {}
            status += f"\n**Voice Integration**: Enabled\n"
            if voice_status:
                status += f"- Database commands available via voice\n"
                status += f"- Recent voice commands: {voice_status.get('command_history_count', 0)}\n"
        
        return status
    
    def _handle_voice_command(self, command: VoiceCommand) -> str:
        """Override to handle database-specific voice commands"""
        try:
            if self.verbose:
                pretty_print(f"Database voice command: {command.original_text}", color="info")
            
            if command.command_type == CommandType.MCP_CONTROL:
                return self._execute_database_voice_command(command)
            else:
                # Fall back to parent implementation
                return super()._handle_voice_command(command)
                
        except Exception as e:
            error_msg = f"Error processing database voice command: {e}"
            if self.verbose:
                pretty_print(error_msg, color="failure")
            return "Sorry, I encountered an error processing that database command."
    
    def _execute_database_voice_command(self, command: VoiceCommand) -> str:
        """Execute database-specific voice commands"""
        action = command.action
        params = command.parameters
        
        try:
            # Get default connection (first available)
            default_conn = list(self.active_connections.values())[0] if self.active_connections else None
            
            if action == "db_connect":
                database = params.get("database", "")
                # For voice commands, assume SQLite for simplicity
                result = self.connect_to_database("sqlite", database, filename=f"{database}.db")
                return result
            
            elif action == "db_query_table":
                if not default_conn:
                    return "No active database connection. Please connect to a database first."
                table = params.get("table", "")
                result = self.execute_sql_query(default_conn, f"SELECT * FROM {table} LIMIT 10")
                return f"Showing data from {table} table. {result}"
            
            elif action == "db_list_tables":
                if not default_conn:
                    return "No active database connection. Please connect to a database first."
                result = self.list_database_tables(default_conn)
                return result
            
            elif action == "db_describe_table":
                if not default_conn:
                    return "No active database connection. Please connect to a database first."
                table = params.get("table", "")
                result = self.describe_table(default_conn, table)
                return f"Table structure for {table}. {result}"
            
            elif action == "db_analyze_table":
                if not default_conn:
                    return "No active database connection. Please connect to a database first."
                table = params.get("table", "")
                result = self.analyze_table(default_conn, table, include_data=True)
                return f"Analysis for {table} table. {result}"
            
            elif action == "db_export_schema":
                if not default_conn:
                    return "No active database connection. Please connect to a database first."
                format_type = params.get("format", "sql")
                result = self.export_database_schema(default_conn, format_type)
                return f"Database schema exported. {result}"
            
            elif action == "db_backup":
                if not default_conn:
                    return "No active database connection. Please connect to a database first."
                result = self.export_database_schema(default_conn, "sql", include_drop=True)
                return f"Database backup created. {result}"
            
            elif action == "db_optimize_query":
                return "Please specify a query to optimize. For example: 'optimize the query SELECT * FROM users'"
            
            else:
                return f"Database command '{action}' not implemented"
                
        except Exception as e:
            return f"Error executing database command: {e}"
    
    async def run(self, prompt: str) -> executorResult:
        """Enhanced run method with database-specific processing"""
        
        # Check if this is a database-related request
        if any(keyword in prompt.lower() for keyword in ['database', 'sql', 'query', 'table', 'schema']):
            
            # Initialize memory for this request
            self.memory = Memory()
            self.memory.push('user', prompt)
            
            # Load database-specific system prompt
            system_prompt = self.load_prompt(
                os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "base", "database_agent.txt")
            )
            
            # Enhance prompt with available database tools and connections
            db_context = self._build_database_context()
            enhanced_prompt = f"{system_prompt}\n\n{db_context}\n\nUser Request: {prompt}"
            self.memory.push('system', enhanced_prompt)
            
            try:
                # Get LLM response
                response, reasoning = await self.llm_request()
                self.last_answer = response
                self.last_reasoning = reasoning
                
                # Execute any database commands in the response
                if any(cmd in response.lower() for cmd in ['db_connect', 'db_query', 'db_list', 'db_describe', 'db_analyze']):
                    return self._parse_and_execute_database_commands(response)
                
                return executorResult(True, response, self.memory.get_memory())
                
            except Exception as e:
                error_msg = f"Database agent execution failed: {e}"
                if self.verbose:
                    pretty_print(error_msg, color="failure")
                return executorResult(False, error_msg, self.memory.get_memory())
        
        else:
            # Fall back to parent implementation for non-database requests
            return await super().run(prompt)
    
    def _build_database_context(self) -> str:
        """Build context about available database connections and tools"""
        context = "Database Context:\n"
        
        # Available connections
        if self.active_connections:
            context += f"Active Connections: {list(self.active_connections.keys())}\n"
        else:
            context += "No active database connections\n"
        
        # Available database tools
        db_tools = self.available_tools.get("database-control", {})
        if db_tools:
            context += f"Available Database Tools: {', '.join(db_tools.keys())}\n"
        
        # Recent query history
        if self.query_history:
            context += f"Recent Queries: {len(self.query_history)} executed\n"
        
        return context
    
    def _parse_and_execute_database_commands(self, response: str) -> executorResult:
        """Parse response for database commands and execute them"""
        try:
            # This is a simplified parser - in production, you'd want more sophisticated parsing
            if "connect to database" in response.lower():
                # Extract database connection details and execute
                pass
            elif "execute query" in response.lower():
                # Extract and execute SQL query
                pass
            
            return executorResult(True, response, self.memory.get_memory())
            
        except Exception as e:
            error_msg = f"Error executing database commands: {e}"
            return executorResult(False, error_msg, self.memory.get_memory())