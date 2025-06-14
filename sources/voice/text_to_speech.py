#!/usr/bin/env python3
"""
Text-to-Speech (TTS) System for AgenticSeek
Provides voice response capabilities
"""

import pyttsx3
import threading
import queue
import time
from typing import Optional, Callable, Dict, Any, List
import logging
import tempfile
import os

class TextToSpeech:
    """
    Text-to-Speech system with multiple voice options and queue management
    """
    
    def __init__(self,
                 voice_id: Optional[str] = None,
                 rate: int = 200,
                 volume: float = 0.9,
                 async_speech: bool = True):
        """
        Initialize Text-to-Speech system
        
        Args:
            voice_id: Specific voice to use (None for default)
            rate: Speech rate (words per minute)
            volume: Speech volume (0.0 to 1.0)
            async_speech: Whether to speak asynchronously
        """
        self.async_speech = async_speech
        self.speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        
        # Initialize TTS engine
        try:
            self.engine = pyttsx3.init()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize TTS engine: {e}")
        
        # Configure voice settings
        self.set_rate(rate)
        self.set_volume(volume)
        
        if voice_id:
            self.set_voice(voice_id)
        
        # Callbacks
        self.on_speech_start: Optional[Callable[[str], None]] = None
        self.on_speech_end: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        self.logger = logging.getLogger(__name__)
        
        # Start async processing if enabled
        if self.async_speech:
            self._start_speech_processor()
    
    def get_available_voices(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available voices"""
        voices = {}
        try:
            for voice in self.engine.getProperty('voices'):
                voices[voice.id] = {
                    'name': voice.name,
                    'language': getattr(voice, 'languages', ['unknown']),
                    'gender': getattr(voice, 'gender', 'unknown'),
                    'age': getattr(voice, 'age', 'unknown')
                }
        except Exception as e:
            self.logger.error(f"Error getting voices: {e}")
        return voices
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the TTS voice
        
        Args:
            voice_id: Voice ID to use
            
        Returns:
            True if voice was set successfully
        """
        try:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if voice.id == voice_id:
                    self.engine.setProperty('voice', voice_id)
                    print(f"✅ Voice set to: {voice.name}")
                    return True
            
            print(f"❌ Voice not found: {voice_id}")
            return False
            
        except Exception as e:
            print(f"❌ Error setting voice: {e}")
            if self.on_error:
                self.on_error(e)
            return False
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        try:
            self.engine.setProperty('rate', rate)
            print(f"✅ Speech rate set to: {rate} WPM")
        except Exception as e:
            print(f"❌ Error setting rate: {e}")
    
    def set_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0)"""
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp to valid range
            self.engine.setProperty('volume', volume)
            print(f"✅ Speech volume set to: {volume:.1f}")
        except Exception as e:
            print(f"❌ Error setting volume: {e}")
    
    def speak(self, text: str, interrupt: bool = False) -> bool:
        """
        Speak the given text
        
        Args:
            text: Text to speak
            interrupt: Whether to interrupt current speech
            
        Returns:
            True if speech was initiated successfully
        """
        if not text or not text.strip():
            return False
        
        text = text.strip()
        
        if interrupt:
            self.stop()
        
        if self.async_speech:
            return self._queue_speech(text)
        else:
            return self._speak_sync(text)
    
    def _speak_sync(self, text: str) -> bool:
        """Speak text synchronously"""
        try:
            if self.on_speech_start:
                self.on_speech_start(text)
            
            self.speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
            self.speaking = False
            
            if self.on_speech_end:
                self.on_speech_end(text)
            
            return True
            
        except Exception as e:
            self.speaking = False
            self.logger.error(f"Sync speech error: {e}")
            if self.on_error:
                self.on_error(e)
            return False
    
    def _queue_speech(self, text: str) -> bool:
        """Queue text for asynchronous speech"""
        try:
            self.speech_queue.put(text, block=False)
            return True
        except queue.Full:
            self.logger.warning("Speech queue is full")
            return False
        except Exception as e:
            self.logger.error(f"Error queuing speech: {e}")
            return False
    
    def _start_speech_processor(self):
        """Start the asynchronous speech processing thread"""
        if self.speech_thread and self.speech_thread.is_alive():
            return
        
        self.speech_thread = threading.Thread(target=self._speech_processor_loop)
        self.speech_thread.daemon = True
        self.speech_thread.start()
    
    def _speech_processor_loop(self):
        """Process speech queue in background thread"""
        while True:
            try:
                # Get text from queue (blocking)
                text = self.speech_queue.get(timeout=1)
                
                if text is None:  # Shutdown signal
                    break
                
                # Speak the text
                if self.on_speech_start:
                    self.on_speech_start(text)
                
                self.speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
                self.speaking = False
                
                if self.on_speech_end:
                    self.on_speech_end(text)
                
                # Mark task as done
                self.speech_queue.task_done()
                
            except queue.Empty:
                # No speech to process, continue
                continue
            except Exception as e:
                self.speaking = False
                self.logger.error(f"Speech processor error: {e}")
                if self.on_error:
                    self.on_error(e)
    
    def stop(self):
        """Stop current speech and clear queue"""
        try:
            # Stop current speech
            self.engine.stop()
            self.speaking = False
            
            # Clear queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except queue.Empty:
                    break
            
            print("🔇 Speech stopped and queue cleared")
            
        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self.speaking
    
    def wait_until_done(self, timeout: Optional[float] = None):
        """Wait until all queued speech is complete"""
        if self.async_speech:
            try:
                if timeout:
                    # Wait with timeout
                    start_time = time.time()
                    while not self.speech_queue.empty() or self.speaking:
                        if time.time() - start_time > timeout:
                            break
                        time.sleep(0.1)
                else:
                    # Wait indefinitely
                    self.speech_queue.join()
                    while self.speaking:
                        time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error waiting for speech completion: {e}")
    
    def get_queue_size(self) -> int:
        """Get number of items in speech queue"""
        return self.speech_queue.qsize()
    
    def speak_file(self, file_path: str) -> bool:
        """
        Speak text from a file
        
        Args:
            file_path: Path to text file
            
        Returns:
            True if file was read and speech initiated
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return self.speak(text)
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return False
    
    def save_to_file(self, text: str, file_path: str) -> bool:
        """
        Save speech to audio file (if supported by engine)
        
        Args:
            text: Text to convert to speech
            file_path: Output file path
            
        Returns:
            True if file was saved successfully
        """
        try:
            # Note: pyttsx3 doesn't directly support saving to file
            # This is a placeholder for potential future implementation
            # or integration with other TTS engines
            self.logger.warning("Save to file not implemented with pyttsx3")
            return False
        except Exception as e:
            self.logger.error(f"Error saving to file: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current TTS system status"""
        current_voice = self.engine.getProperty('voice')
        voices = self.get_available_voices()
        current_voice_info = voices.get(current_voice, {})
        
        return {
            "speaking": self.speaking,
            "async_mode": self.async_speech,
            "queue_size": self.get_queue_size(),
            "rate": self.engine.getProperty('rate'),
            "volume": self.engine.getProperty('volume'),
            "current_voice": {
                "id": current_voice,
                "name": current_voice_info.get('name', 'Unknown'),
                "language": current_voice_info.get('language', 'Unknown')
            },
            "available_voices": len(voices)
        }
    
    def shutdown(self):
        """Shutdown the TTS system"""
        try:
            self.stop()
            
            # Signal speech processor to shutdown
            if self.async_speech and self.speech_thread:
                self.speech_queue.put(None)  # Shutdown signal
                self.speech_thread.join(timeout=2)
            
            print("🔇 TTS system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def demo_tts():
    """Demo function for Text-to-Speech system"""
    print("\n" + "="*50)
    print("🔊 Text-to-Speech Demo")
    print("="*50)
    
    # Initialize TTS
    tts = TextToSpeech(rate=180, volume=0.8)
    
    # Show available voices
    voices = tts.get_available_voices()
    print(f"\n🗣️ Available voices ({len(voices)}):")
    for voice_id, info in list(voices.items())[:5]:  # Show first 5
        print(f"  {info['name']} ({voice_id[:30]}...)")
    
    # Show current status
    status = tts.get_status()
    print(f"\n📊 TTS Status:")
    print(f"  Current voice: {status['current_voice']['name']}")
    print(f"  Rate: {status['rate']} WPM")
    print(f"  Volume: {status['volume']:.1f}")
    print(f"  Async mode: {status['async_mode']}")
    
    # Setup callbacks
    def on_start(text):
        print(f"🗣️ Speaking: '{text[:50]}...'")
    
    def on_end(text):
        print(f"✅ Finished speaking")
    
    tts.on_speech_start = on_start
    tts.on_speech_end = on_end
    
    # Demo speech
    demo_texts = [
        "Hello! This is the AgenticSeek text-to-speech system.",
        "I can speak multiple languages and adjust my voice settings.",
        "Voice integration is now active for enhanced AI agent interaction."
    ]
    
    print(f"\n🎯 Speaking {len(demo_texts)} demo messages:")
    
    for i, text in enumerate(demo_texts, 1):
        print(f"\n{i}. Queuing: '{text}'")
        tts.speak(text)
        
        # Wait a bit between messages
        time.sleep(1)
    
    # Wait for completion
    print("\n⏳ Waiting for speech completion...")
    tts.wait_until_done(timeout=30)
    
    # Test voice change (if multiple voices available)
    if len(voices) > 1:
        print(f"\n🔄 Testing voice change...")
        other_voice = list(voices.keys())[1]
        if tts.set_voice(other_voice):
            tts.speak("This is a different voice!")
            tts.wait_until_done(timeout=10)
    
    # Shutdown
    tts.shutdown()
    
    print("\n✅ Text-to-Speech demo complete!")


if __name__ == "__main__":
    demo_tts()