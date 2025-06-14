#!/usr/bin/env python3
"""
Voice Integration Module for AgenticSeek
Provides speech-to-text, text-to-speech, and voice command processing
"""

try:
    from .speech_to_text import SpeechToText
    from .text_to_speech import TextToSpeech
    from .voice_commands import VoiceCommandProcessor, VoiceCommand, CommandType
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    SpeechToText = None
    TextToSpeech = None
    VoiceCommandProcessor = None
    VoiceCommand = None
    CommandType = None

__all__ = [
    'SpeechToText',
    'TextToSpeech', 
    'VoiceCommandProcessor',
    'VoiceCommand',
    'CommandType',
    'VOICE_AVAILABLE'
]

__version__ = "1.0.0"