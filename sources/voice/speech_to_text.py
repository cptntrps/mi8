#!/usr/bin/env python3
"""
Speech-to-Text (STT) System for AgenticSeek
Provides voice command recognition capabilities
"""

import speech_recognition as sr
import sounddevice as sd
import numpy as np
import threading
import queue
import time
from typing import Optional, Callable, Dict, Any
import logging

class SpeechToText:
    """
    Speech-to-Text system with multiple recognition engines
    """
    
    def __init__(self, 
                 recognition_engine: str = "google",
                 microphone_index: Optional[int] = None,
                 energy_threshold: int = 4000,
                 dynamic_threshold: bool = True,
                 timeout: float = 5.0,
                 phrase_timeout: float = 1.0):
        """
        Initialize Speech-to-Text system
        
        Args:
            recognition_engine: Engine to use ('google', 'whisper', 'sphinx')
            microphone_index: Specific microphone to use (None for default)
            energy_threshold: Minimum audio energy for voice detection
            dynamic_threshold: Auto-adjust energy threshold
            timeout: Maximum wait time for audio
            phrase_timeout: Pause time before processing speech
        """
        self.recognition_engine = recognition_engine
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout
        
        # Initialize recognizer
        self.recognizer = sr.Recognizer()
        
        # Configure energy threshold
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_threshold
        
        # Initialize microphone
        self.microphone = sr.Microphone(device_index=microphone_index)
        
        # Adjust for ambient noise
        with self.microphone as source:
            print("🎤 Calibrating microphone for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"✅ Energy threshold set to {self.recognizer.energy_threshold}")
        
        # Audio queue for continuous listening
        self.audio_queue = queue.Queue()
        self.listening = False
        self.listen_thread = None
        
        # Callbacks
        self.on_speech_detected: Optional[Callable[[str], None]] = None
        self.on_listening_start: Optional[Callable[[], None]] = None
        self.on_listening_stop: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        self.logger = logging.getLogger(__name__)
        
    def test_microphone(self) -> bool:
        """Test microphone functionality"""
        try:
            with self.microphone as source:
                print("🎤 Testing microphone - say something...")
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)
                text = self.recognize_audio(audio)
                if text:
                    print(f"✅ Microphone test successful: '{text}'")
                    return True
                else:
                    print("❌ No speech detected during test")
                    return False
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            return False
    
    def recognize_audio(self, audio_data) -> Optional[str]:
        """
        Recognize speech from audio data
        
        Args:
            audio_data: Audio data from speech_recognition
            
        Returns:
            Recognized text or None if recognition failed
        """
        try:
            if self.recognition_engine == "google":
                text = self.recognizer.recognize_google(audio_data)
            elif self.recognition_engine == "whisper":
                text = self.recognizer.recognize_whisper(audio_data)
            elif self.recognition_engine == "sphinx":
                text = self.recognizer.recognize_sphinx(audio_data)
            else:
                raise ValueError(f"Unsupported recognition engine: {self.recognition_engine}")
            
            return text.strip() if text else None
            
        except sr.UnknownValueError:
            self.logger.debug("Speech not understood")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Recognition service error: {e}")
            if self.on_error:
                self.on_error(e)
            return None
        except Exception as e:
            self.logger.error(f"Recognition error: {e}")
            if self.on_error:
                self.on_error(e)
            return None
    
    def listen_once(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Listen for a single speech command
        
        Args:
            timeout: Maximum wait time (uses instance default if None)
            
        Returns:
            Recognized text or None
        """
        try:
            timeout = timeout or self.timeout
            
            with self.microphone as source:
                print("🎤 Listening...")
                if self.on_listening_start:
                    self.on_listening_start()
                
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=self.phrase_timeout
                )
                
                if self.on_listening_stop:
                    self.on_listening_stop()
                
                print("🔄 Processing speech...")
                text = self.recognize_audio(audio)
                
                if text:
                    print(f"✅ Recognized: '{text}'")
                    if self.on_speech_detected:
                        self.on_speech_detected(text)
                
                return text
                
        except sr.WaitTimeoutError:
            print("⏰ Listening timeout - no speech detected")
            return None
        except Exception as e:
            print(f"❌ Listening error: {e}")
            if self.on_error:
                self.on_error(e)
            return None
    
    def start_continuous_listening(self):
        """Start continuous listening in background thread"""
        if self.listening:
            print("⚠️ Already listening")
            return
        
        self.listening = True
        self.listen_thread = threading.Thread(target=self._continuous_listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        print("🎤 Started continuous listening")
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        if not self.listening:
            return
        
        self.listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        print("🔇 Stopped continuous listening")
    
    def _continuous_listen_loop(self):
        """Continuous listening loop (runs in background thread)"""
        with self.microphone as source:
            while self.listening:
                try:
                    if self.on_listening_start:
                        self.on_listening_start()
                    
                    # Listen for audio
                    audio = self.recognizer.listen(
                        source, 
                        timeout=1,  # Short timeout for responsiveness
                        phrase_time_limit=self.phrase_timeout
                    )
                    
                    if self.on_listening_stop:
                        self.on_listening_stop()
                    
                    # Process in background to avoid blocking
                    threading.Thread(
                        target=self._process_audio_async,
                        args=(audio,),
                        daemon=True
                    ).start()
                    
                except sr.WaitTimeoutError:
                    # Normal timeout, continue listening
                    continue
                except Exception as e:
                    self.logger.error(f"Continuous listening error: {e}")
                    if self.on_error:
                        self.on_error(e)
                    time.sleep(0.5)  # Brief pause before retrying
    
    def _process_audio_async(self, audio_data):
        """Process audio data asynchronously"""
        text = self.recognize_audio(audio_data)
        if text and self.on_speech_detected:
            self.on_speech_detected(text)
    
    def get_available_microphones(self) -> Dict[int, str]:
        """Get list of available microphones"""
        microphones = {}
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            microphones[index] = name
        return microphones
    
    def set_microphone(self, index: int):
        """Change microphone device"""
        try:
            self.microphone = sr.Microphone(device_index=index)
            # Re-calibrate for new microphone
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"✅ Switched to microphone: {self.get_available_microphones().get(index, 'Unknown')}")
        except Exception as e:
            print(f"❌ Failed to switch microphone: {e}")
    
    def set_recognition_engine(self, engine: str):
        """Change recognition engine"""
        if engine in ["google", "whisper", "sphinx"]:
            self.recognition_engine = engine
            print(f"✅ Switched to {engine} recognition engine")
        else:
            print(f"❌ Unsupported engine: {engine}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current STT system status"""
        return {
            "listening": self.listening,
            "engine": self.recognition_engine,
            "energy_threshold": self.recognizer.energy_threshold,
            "dynamic_threshold": self.recognizer.dynamic_energy_threshold,
            "timeout": self.timeout,
            "phrase_timeout": self.phrase_timeout,
            "microphone_count": len(self.get_available_microphones())
        }


def demo_stt():
    """Demo function for Speech-to-Text system"""
    print("\n" + "="*50)
    print("🎤 Speech-to-Text Demo")
    print("="*50)
    
    # Initialize STT
    stt = SpeechToText()
    
    # Test microphone
    if not stt.test_microphone():
        print("❌ Microphone test failed - check audio setup")
        return
    
    # Show available microphones
    mics = stt.get_available_microphones()
    print(f"\n📱 Available microphones:")
    for idx, name in mics.items():
        print(f"  {idx}: {name}")
    
    # Setup callbacks
    def on_speech(text):
        print(f"🗣️ You said: '{text}'")
        if "stop" in text.lower() or "quit" in text.lower():
            stt.stop_continuous_listening()
    
    def on_start():
        print("🔴 Listening...")
    
    def on_stop():
        print("⏸️ Processing...")
    
    stt.on_speech_detected = on_speech
    stt.on_listening_start = on_start
    stt.on_listening_stop = on_stop
    
    # Demo single recognition
    print("\n🎯 Single recognition test - say something:")
    result = stt.listen_once(timeout=5)
    
    # Demo continuous listening
    print("\n🔄 Starting continuous listening - say 'stop' to end:")
    stt.start_continuous_listening()
    
    # Wait for stop command
    try:
        while stt.listening:
            time.sleep(0.1)
    except KeyboardInterrupt:
        stt.stop_continuous_listening()
    
    print("\n✅ Speech-to-Text demo complete!")


if __name__ == "__main__":
    demo_stt()