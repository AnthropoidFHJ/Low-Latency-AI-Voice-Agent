import asyncio
import websockets
import json
import sys
async def test_websocket_connection():
    uri = "ws://localhost:8000/ws/voice/test_client_12345"
    try:
        print("Connecting to voice agent WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            init_message = {
                "type": "initialize",
                "data": {"client_id": "test_client_12345"}
            }
            await websocket.send(json.dumps(init_message))
            print("Sent initialization message")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                print(f"Received: {response_data}")
                if response_data.get("type") == "connection_established":
                    print("Voice agent connection established!")
                    return True
                else:
                    print(f"Unexpected response: {response_data}")
                    return False
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                return False
    except ConnectionRefusedError:
        print("Connection refused - make sure the backend server is running")
        return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False
if __name__ == "__main__":
    success = asyncio.run(test_websocket_connection())
    sys.exit(0 if success else 1)