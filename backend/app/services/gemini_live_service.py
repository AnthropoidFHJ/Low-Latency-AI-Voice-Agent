import asyncio
import logging
import json
import base64
from typing import Dict, Any, Optional, AsyncGenerator, Callable
import websockets
import aiohttp
from datetime import datetime
from ..config import settings
logger = logging.getLogger(__name__)
class GeminiLiveService:
    def __init__(self):
        self.api_key = settings.google_api_key
        self.model = "gemini-1.5-flash"
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.session_id: Optional[str] = None
        self.is_connected = False
        self.audio_config = {
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1,
            "chunk_size": 1024,
        }
        self.metrics = {
            "audio_chunks_sent": 0,
            "audio_chunks_received": 0,
            "avg_response_time_ms": 0,
            "last_response_time": None,
            "connection_time": None,
        }
        self.on_audio_response: Optional[Callable] = None
        self.on_text_response: Optional[Callable] = None
        self.on_function_call: Optional[Callable] = None
    async def initialize(self) -> bool:
        try:
            start_time = asyncio.get_event_loop().time()
            uri = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={self.api_key}"
            self.websocket = await websockets.connect(
                uri,
                extra_headers={
                    "Content-Type": "application/json",
                },
                ping_interval=10,
                ping_timeout=5,
                close_timeout=5
            )
            setup_message = {
                "setup": {
                    "model": f"models/{self.model}",
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": "Aoede" 
                                }
                            }
                        }
                    }
                }
            }
            await self.websocket.send(json.dumps(setup_message))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            setup_response = json.loads(response)
            if "setupComplete" in setup_response:
                self.is_connected = True
                self.metrics["connection_time"] = (asyncio.get_event_loop().time() - start_time) * 1000
                logger.info(f"Gemini Live API connected successfully in {self.metrics['connection_time']:.2f}ms")
                return True
            else:
                logger.error(f"Failed to setup Gemini Live: {setup_response}")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Live API: {e}")
            return False
    async def send_audio_chunk(self, audio_data: bytes) -> None:
        if not self.is_connected or not self.websocket:
            logger.warning("Gemini Live not connected, cannot send audio")
            return
        try:
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            message = {
                "realtimeInput": {
                    "mediaChunks": [
                        {
                            "mimeType": "audio/pcm",
                            "data": audio_b64
                        }
                    ]
                }
            }
            await self.websocket.send(json.dumps(message))
            self.metrics["audio_chunks_sent"] += 1
        except Exception as e:
            logger.error(f"Error sending audio chunk: {e}")
            await self._handle_connection_error()
    async def start_listening(self) -> AsyncGenerator[Dict[str, Any], None]:
        if not self.is_connected or not self.websocket:
            logger.error("Cannot start listening: not connected to Gemini Live")
            return
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    response_time = asyncio.get_event_loop().time()
                    if "serverContent" in data:
                        content = data["serverContent"]
                        if "modelTurn" in content and "parts" in content["modelTurn"]:
                            for part in content["modelTurn"]["parts"]:
                                if "inlineData" in part:
                                    audio_data = base64.b64decode(part["inlineData"]["data"])
                                    response = {
                                        "type": "audio_response",
                                        "audio_data": audio_data,
                                        "mime_type": part["inlineData"].get("mimeType", "audio/pcm"),
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "response_time_ms": (response_time - self.metrics.get("last_request_time", response_time)) * 1000
                                    }
                                    self.metrics["audio_chunks_received"] += 1
                                    self.metrics["last_response_time"] = response["response_time_ms"]
                                    if self.on_audio_response:
                                        await self.on_audio_response(response)
                                    yield response
                                elif "text" in part:
                                    response = {
                                        "type": "text_response",
                                        "text": part["text"],
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                                    if self.on_text_response:
                                        await self.on_text_response(response)
                                    yield response
                                elif "functionCall" in part:
                                    function_call = part["functionCall"]
                                    response = {
                                        "type": "function_call",
                                        "function_name": function_call["name"],
                                        "arguments": function_call.get("args", {}),
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                                    if self.on_function_call:
                                        result = await self.on_function_call(response)
                                        await self._send_function_response(function_call["name"], result)
                                    yield response
                    elif "toolCallCancellation" in data:
                        yield {
                            "type": "tool_cancellation",
                            "message": "Tool call was cancelled",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing Gemini Live response: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing Gemini Live message: {e}")
                    continue
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Gemini Live connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error in Gemini Live listening loop: {e}")
            await self._handle_connection_error()
    async def _send_function_response(self, function_name: str, result: Dict[str, Any]) -> None:
        try:
            message = {
                "realtimeInput": {
                    "toolResponse": {
                        "functionResponses": [
                            {
                                "name": function_name,
                                "response": result
                            }
                        ]
                    }
                }
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending function response: {e}")
    async def send_text_input(self, text: str) -> None:
        if not self.is_connected or not self.websocket:
            logger.warning("Gemini Live not connected, cannot send text")
            return
        try:
            message = {
                "realtimeInput": {
                    "mediaChunks": [
                        {
                            "mimeType": "text/plain",
                            "data": base64.b64encode(text.encode()).decode()
                        }
                    ]
                }
            }
            await self.websocket.send(json.dumps(message))
            self.metrics["last_request_time"] = asyncio.get_event_loop().time()
        except Exception as e:
            logger.error(f"Error sending text input: {e}")
    async def close(self) -> None:
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"Error closing Gemini Live connection: {e}")
            finally:
                self.websocket = None
                self.is_connected = False
                logger.info("Gemini Live connection closed")
    async def _handle_connection_error(self) -> None:
        self.is_connected = False
        logger.warning("Handling Gemini Live connection error")
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None
        await asyncio.sleep(1.0)
        logger.info("Attempting to reconnect to Gemini Live...")
        await self.initialize()
    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "is_connected": self.is_connected,
            "audio_config": self.audio_config,
        }
    def set_callbacks(self, 
                     on_audio_response: Optional[Callable] = None,
                     on_text_response: Optional[Callable] = None, 
                     on_function_call: Optional[Callable] = None) -> None:
        self.on_audio_response = on_audio_response
        self.on_text_response = on_text_response
        self.on_function_call = on_function_call
gemini_live_service = GeminiLiveService()