#!/usr/bin/env python3
"""
Simple Voice Integration Test
"""

import sys
import os

# Add the project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from sources.voice import VoiceCommandProcessor, VOICE_AVAILABLE
    
    def test_voice_simple():
        print("\n" + "="*50)
        print("🎤 Simple Voice Test")
        print("="*50)
        
        if not VOICE_AVAILABLE:
            print("❌ Voice libraries not available")
            return
        
        print("✅ Voice libraries available")
        
        # Test voice command processor creation
        try:
            processor = VoiceCommandProcessor(wake_word="test")
            print("✅ Voice processor created")
            
            # Test command parsing
            test_commands = [
                "open main.py in cursor",
                "remember test note",
                "hello there"
            ]
            
            print("\n🧪 Testing command parsing:")
            for cmd in test_commands:
                command = processor.parse_command(cmd)
                print(f"  '{cmd}' → {command.command_type.value}:{command.action}")
            
            # Test TTS
            print("\n🔊 Testing text-to-speech:")
            processor.tts.speak("Voice integration test successful")
            processor.tts.wait_until_done(timeout=10)
            
            # Cleanup
            processor.shutdown()
            print("✅ Voice test completed successfully")
            
        except Exception as e:
            print(f"❌ Voice test failed: {e}")
            import traceback
            traceback.print_exc()

    if __name__ == "__main__":
        test_voice_simple()
        
except Exception as e:
    print(f"❌ Test error: {e}")
    import traceback
    traceback.print_exc()