#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to AgenticSeek WebSocket!")
            
            # Send a ping
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 Received: {data['type']} - {data.get('message', data.get('timestamp', ''))}")
                
                if data['type'] == 'pong':
                    print("✅ WebSocket connection working!")
                    break
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())