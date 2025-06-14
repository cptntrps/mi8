#!/usr/bin/env python3
"""
Voice Command Processing System for AgenticSeek
Handles voice command recognition, processing, and routing
"""

import re
import json
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech

class CommandType(Enum):
    """Types of voice commands"""
    MCP_CONTROL = "mcp"
    AGENT_REQUEST = "agent" 
    SYSTEM_CONTROL = "system"
    CONVERSATION = "conversation"
    UNKNOWN = "unknown"

@dataclass
class VoiceCommand:
    """Represents a processed voice command"""
    original_text: str
    command_type: CommandType
    action: str
    parameters: Dict[str, Any]
    confidence: float
    timestamp: float

class VoiceCommandProcessor:
    """
    Main voice command processing system
    Integrates STT, command parsing, and TTS
    """
    
    def __init__(self,
                 stt_engine: str = "google",
                 tts_rate: int = 180,
                 tts_volume: float = 0.8,
                 command_timeout: float = 30.0,
                 wake_word: str = "agenticsseek"):
        """
        Initialize voice command processor
        
        Args:
            stt_engine: Speech recognition engine
            tts_rate: Text-to-speech rate
            tts_volume: Text-to-speech volume
            command_timeout: Timeout for command processing
            wake_word: Wake word to activate commands
        """
        
        # Initialize STT and TTS
        self.stt = SpeechToText(recognition_engine=stt_engine)
        self.tts = TextToSpeech(rate=tts_rate, volume=tts_volume)
        
        self.wake_word = wake_word.lower()
        self.command_timeout = command_timeout
        self.listening = False
        self.wake_word_mode = True
        
        # Command patterns
        self.command_patterns = self._initialize_command_patterns()
        
        # Callbacks
        self.on_command_detected: Optional[Callable[[VoiceCommand], str]] = None
        self.on_wake_word_detected: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # Setup STT callbacks
        self.stt.on_speech_detected = self._process_speech
        self.stt.on_error = self._handle_stt_error
        
        self.logger = logging.getLogger(__name__)
        
        # Command history
        self.command_history: List[VoiceCommand] = []
        self.max_history = 50
    
    def _initialize_command_patterns(self) -> Dict[CommandType, List[Dict]]:
        """Initialize command recognition patterns"""
        return {
            CommandType.MCP_CONTROL: [
                {
                    "pattern": r"open (?:file )?(.+?) in (?:cursor|editor)",
                    "action": "cursor_open_file",
                    "params": {"file_path": 1}
                },
                {
                    "pattern": r"remember (?:that )?(.+)",
                    "action": "memory_save",
                    "params": {"content": 1}
                },
                {
                    "pattern": r"watch (?:the )?(.+?) (?:directory|folder|files)",
                    "action": "file_watch",
                    "params": {"path": 1}
                },
                {
                    "pattern": r"create (?:a )?file (?:called )?(.+)",
                    "action": "cursor_create_file", 
                    "params": {"file_name": 1}
                },
                {
                    "pattern": r"search (?:for )?(.+?) in (?:files|project)",
                    "action": "cursor_search_files",
                    "params": {"query": 1}
                }
            ],
            CommandType.AGENT_REQUEST: [
                {
                    "pattern": r"(?:write|code|create) (?:a )?(.+?) (?:function|script|program)",
                    "action": "code_request",
                    "params": {"description": 1}
                },
                {
                    "pattern": r"(?:browse|visit|go to) (.+)",
                    "action": "web_browse",
                    "params": {"url": 1}
                },
                {
                    "pattern": r"(?:search|find|look up) (.+?) (?:on the web|online)",
                    "action": "web_search",
                    "params": {"query": 1}
                },
                {
                    "pattern": r"(?:translate|convert) (.+?) (?:to|into) (.+)",
                    "action": "translate",
                    "params": {"text": 1, "target_language": 2}
                }
            ],
            CommandType.SYSTEM_CONTROL: [
                {
                    "pattern": r"(?:start|begin) (?:listening|voice (?:mode|control))",
                    "action": "start_listening",
                    "params": {}
                },
                {
                    "pattern": r"(?:stop|end|quit) (?:listening|voice (?:mode|control))",
                    "action": "stop_listening", 
                    "params": {}
                },
                {
                    "pattern": r"(?:set|change) voice (?:to )?(.+)",
                    "action": "change_voice",
                    "params": {"voice_name": 1}
                },
                {
                    "pattern": r"(?:set|change) (?:speech )?(?:rate|speed) (?:to )?(.+)",
                    "action": "change_speech_rate",
                    "params": {"rate": 1}
                },
                {
                    "pattern": r"(?:mute|unmute|silence)",
                    "action": "toggle_mute",
                    "params": {}
                }
            ],
            CommandType.CONVERSATION: [
                {
                    "pattern": r"(?:hello|hi|hey)(?:\s+.+)?",
                    "action": "greeting",
                    "params": {}
                },
                {
                    "pattern": r"(?:thank you|thanks)(?:\s+.+)?",
                    "action": "thanks",
                    "params": {}
                },
                {
                    "pattern": r"(?:goodbye|bye|see you later)(?:\s+.+)?",
                    "action": "goodbye",
                    "params": {}
                },
                {
                    "pattern": r"(?:help|what can you do)",
                    "action": "help",
                    "params": {}
                }
            ]
        }
    
    def parse_command(self, text: str) -> VoiceCommand:
        """
        Parse speech text into a structured command
        
        Args:
            text: Recognized speech text
            
        Returns:
            Parsed VoiceCommand object
        """
        text = text.lower().strip()
        
        # Try to match against command patterns
        for command_type, patterns in self.command_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                match = re.search(pattern, text, re.IGNORECASE)
                
                if match:
                    # Extract parameters
                    params = {}
                    for param_name, group_index in pattern_info["params"].items():
                        if group_index <= len(match.groups()):
                            params[param_name] = match.group(group_index).strip()
                    
                    return VoiceCommand(
                        original_text=text,
                        command_type=command_type,
                        action=pattern_info["action"],
                        parameters=params,
                        confidence=0.8,  # Base confidence for pattern match
                        timestamp=time.time()
                    )
        
        # No pattern matched - treat as general conversation
        return VoiceCommand(
            original_text=text,
            command_type=CommandType.UNKNOWN,
            action="general_query",
            parameters={"query": text},
            confidence=0.3,
            timestamp=time.time()
        )
    
    def _process_speech(self, text: str):
        """Process recognized speech text"""
        try:
            text = text.strip()
            if not text:
                return
            
            self.logger.info(f"Processing speech: '{text}'")
            
            # Check for wake word if in wake word mode
            if self.wake_word_mode:
                if self.wake_word in text.lower():
                    self.tts.speak("Yes?")
                    if self.on_wake_word_detected:
                        self.on_wake_word_detected()
                    # Remove wake word and process remaining text
                    text = re.sub(self.wake_word, "", text, flags=re.IGNORECASE).strip()
                    if not text:
                        return
                else:
                    # No wake word detected, ignore
                    return
            
            # Parse the command
            command = self.parse_command(text)
            
            # Add to history
            self.command_history.append(command)
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
            
            # Process the command
            response = self._execute_command(command)
            
            # Speak the response
            if response:
                self.tts.speak(response)
                
        except Exception as e:
            self.logger.error(f"Error processing speech: {e}")
            if self.on_error:
                self.on_error(e)
            self.tts.speak("Sorry, I encountered an error processing that command.")
    
    def _execute_command(self, command: VoiceCommand) -> str:
        """
        Execute a parsed voice command
        
        Args:
            command: Parsed voice command
            
        Returns:
            Response text to speak back
        """
        try:
            # Handle system control commands internally
            if command.command_type == CommandType.SYSTEM_CONTROL:
                return self._handle_system_command(command)
            
            # Handle conversation commands internally
            if command.command_type == CommandType.CONVERSATION:
                return self._handle_conversation_command(command)
            
            # For other commands, use callback if available
            if self.on_command_detected:
                return self.on_command_detected(command)
            else:
                return f"Command recognized: {command.action}. No handler available."
                
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            return "Sorry, I couldn't execute that command."
    
    def _handle_system_command(self, command: VoiceCommand) -> str:
        """Handle system control commands"""
        action = command.action
        params = command.parameters
        
        if action == "start_listening":
            self.wake_word_mode = False
            return "Continuous listening activated. I'm listening for commands."
        
        elif action == "stop_listening":
            self.wake_word_mode = True
            return "Switching to wake word mode. Say 'AgenticSeek' to get my attention."
        
        elif action == "change_voice":
            voice_name = params.get("voice_name", "").lower()
            voices = self.tts.get_available_voices()
            
            # Find voice by name
            for voice_id, info in voices.items():
                if voice_name in info["name"].lower():
                    if self.tts.set_voice(voice_id):
                        return f"Voice changed to {info['name']}"
                    else:
                        return "Failed to change voice"
            
            return f"Voice '{voice_name}' not found"
        
        elif action == "change_speech_rate":
            try:
                rate_text = params.get("rate", "").lower()
                # Parse common rate descriptions
                if "slow" in rate_text or "slower" in rate_text:
                    rate = 150
                elif "fast" in rate_text or "faster" in rate_text:
                    rate = 250
                elif "normal" in rate_text:
                    rate = 200
                else:
                    # Try to extract number
                    rate_match = re.search(r"(\d+)", rate_text)
                    if rate_match:
                        rate = int(rate_match.group(1))
                    else:
                        return "I didn't understand the speech rate"
                
                self.tts.set_rate(rate)
                return f"Speech rate set to {rate} words per minute"
                
            except Exception as e:
                return "Failed to change speech rate"
        
        elif action == "toggle_mute":
            current_volume = self.tts.engine.getProperty('volume')
            if current_volume > 0:
                self.tts.set_volume(0.0)
                return "Muted"
            else:
                self.tts.set_volume(0.8)
                return "Unmuted"
        
        return "System command not implemented"
    
    def _handle_conversation_command(self, command: VoiceCommand) -> str:
        """Handle conversation commands"""
        action = command.action
        
        responses = {
            "greeting": "Hello! I'm ready to help you with AgenticSeek.",
            "thanks": "You're welcome! Happy to help.",
            "goodbye": "Goodbye! Have a great day.",
            "help": "I can help you control Cursor, manage memory, watch files, browse the web, write code, and more. Just speak naturally!"
        }
        
        return responses.get(action, "I understand you're trying to chat, but I'm not sure how to respond to that.")
    
    def _handle_stt_error(self, error: Exception):
        """Handle STT errors"""
        self.logger.error(f"STT Error: {error}")
        if self.on_error:
            self.on_error(error)
    
    def start_listening(self):
        """Start voice command listening"""
        if self.listening:
            return
        
        self.listening = True
        self.stt.start_continuous_listening()
        
        if self.wake_word_mode:
            self.tts.speak(f"Voice control ready. Say '{self.wake_word}' to get my attention.")
        else:
            self.tts.speak("Voice control ready. I'm listening for commands.")
    
    def stop_listening(self):
        """Stop voice command listening"""
        if not self.listening:
            return
        
        self.listening = False
        self.stt.stop_continuous_listening()
        self.tts.speak("Voice control stopped.")
    
    def toggle_wake_word_mode(self):
        """Toggle wake word mode on/off"""
        self.wake_word_mode = not self.wake_word_mode
        mode = "wake word" if self.wake_word_mode else "continuous"
        self.tts.speak(f"Switched to {mode} mode.")
    
    def get_status(self) -> Dict[str, Any]:
        """Get voice command system status"""
        return {
            "listening": self.listening,
            "wake_word_mode": self.wake_word_mode,
            "wake_word": self.wake_word,
            "stt_status": self.stt.get_status(),
            "tts_status": self.tts.get_status(),
            "command_history_count": len(self.command_history),
            "supported_commands": len(sum([patterns for patterns in self.command_patterns.values()], []))
        }
    
    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent command history"""
        recent_commands = self.command_history[-limit:]
        return [
            {
                "text": cmd.original_text,
                "type": cmd.command_type.value,
                "action": cmd.action,
                "params": cmd.parameters,
                "confidence": cmd.confidence,
                "timestamp": cmd.timestamp
            }
            for cmd in recent_commands
        ]
    
    def shutdown(self):
        """Shutdown voice command system"""
        self.stop_listening()
        self.tts.shutdown()
        self.logger.info("Voice command system shutdown complete")


def demo_voice_commands():
    """Demo function for voice command system"""
    print("\n" + "="*60)
    print("🎤🔊 Voice Command System Demo")
    print("="*60)
    
    # Initialize voice command processor
    processor = VoiceCommandProcessor(wake_word="agenticsseek")
    
    # Setup command handler
    def handle_command(command: VoiceCommand) -> str:
        print(f"\n🎯 Command detected:")
        print(f"  Type: {command.command_type.value}")
        print(f"  Action: {command.action}")
        print(f"  Parameters: {command.parameters}")
        print(f"  Confidence: {command.confidence:.2f}")
        
        # Return appropriate response based on command type
        if command.command_type == CommandType.MCP_CONTROL:
            if command.action == "cursor_open_file":
                file_path = command.parameters.get("file_path", "unknown")
                return f"Opening {file_path} in Cursor"
            elif command.action == "memory_save":
                content = command.parameters.get("content", "")
                return f"Remembering: {content[:50]}..."
            elif command.action == "file_watch":
                path = command.parameters.get("path", "unknown")
                return f"Watching {path} for changes"
        
        elif command.command_type == CommandType.AGENT_REQUEST:
            if command.action == "code_request":
                description = command.parameters.get("description", "")
                return f"I'll help you write {description}"
            elif command.action == "web_browse":
                url = command.parameters.get("url", "")
                return f"Browsing to {url}"
        
        return f"Command {command.action} received and processed"
    
    processor.on_command_detected = handle_command
    
    # Show status
    status = processor.get_status()
    print(f"\n📊 Voice Command Status:")
    print(f"  Wake word: '{status['wake_word']}'")
    print(f"  Supported commands: {status['supported_commands']}")
    print(f"  STT Engine: {status['stt_status']['engine']}")
    print(f"  TTS Voice: {status['tts_status']['current_voice']['name']}")
    
    # Test command parsing
    print(f"\n🧪 Testing command parsing:")
    test_commands = [
        "AgenticSeek open main.py in cursor",
        "remember I'm working on authentication",
        "watch the src directory",
        "write a Python function",
        "hello there"
    ]
    
    for test_text in test_commands:
        # Remove wake word for parsing test
        clean_text = test_text.replace("AgenticSeek ", "")
        command = processor.parse_command(clean_text)
        print(f"  '{test_text}' → {command.command_type.value}:{command.action}")
    
    # Interactive demo
    print(f"\n🎤 Voice Command Demo - Say commands or 'quit' to exit")
    print(f"Sample commands:")
    print(f"  - 'AgenticSeek open main.py in cursor'")
    print(f"  - 'AgenticSeek remember I'm working on auth'")
    print(f"  - 'AgenticSeek write a Python script'")
    print(f"  - 'AgenticSeek hello'")
    
    try:
        processor.start_listening()
        
        # Wait for user to stop
        input("\nPress Enter to stop demo...")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted")
    finally:
        processor.stop_listening()
        processor.shutdown()
    
    print("\n✅ Voice command demo complete!")


if __name__ == "__main__":
    demo_voice_commands()