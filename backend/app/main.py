import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from .config import settings, PERFORMANCE_THRESHOLDS
from .voice_agent import voice_agent
from .simplified_voice_agent import simplified_voice_agent
from .complete_pipecat_agent import complete_pipecat_agent
from .services.gemini_live_service import gemini_live_service
from .services.audio_stream_processor import audio_stream_processor

voice_agent = complete_pipecat_agent

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ultra-Low Latency Voice Agent",
    description="Real-time AI voice agent with <500ms latency using Pipecat and Gemini Live",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metrics: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.connection_metrics[client_id] = {
                "connected_at": datetime.utcnow(),
                "messages_sent": 0,
                "messages_received": 0,
                "total_latency_ms": 0,
                "avg_latency_ms": 0,
            }
            logger.info(f"Client {client_id} connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect client {client_id}: {e}")
            return False
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_metrics:
            del self.connection_metrics[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]) -> bool:
        if client_id not in self.active_connections:
            return False
        
        try:
            start_time = asyncio.get_event_loop().time()
            websocket = self.active_connections[client_id]
            await websocket.send_text(json.dumps(message))
            
            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            metrics = self.connection_metrics[client_id]
            metrics["messages_sent"] += 1
            metrics["total_latency_ms"] += latency_ms
            metrics["avg_latency_ms"] = metrics["total_latency_ms"] / metrics["messages_sent"]
            
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            self.disconnect(client_id)
            return False
    
    def get_connection_count(self) -> int:
        return len(self.active_connections)
    
    def get_metrics(self) -> Dict[str, Any]:
        return {
            "active_connections": len(self.active_connections),
            "connection_details": self.connection_metrics,
        }

manager = ConnectionManager()

class VoiceSessionRequest(BaseModel):
    room_url: str
    token: str
    config: Optional[Dict[str, Any]] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    version: str
    performance_metrics: Dict[str, Any]

@app.get("/health", response_model=HealthCheck)
async def health_check():
    metrics = voice_agent.get_metrics()
    connection_metrics = manager.get_metrics()
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        performance_metrics={
            "voice_agent": metrics,
            "connections": connection_metrics,
            "thresholds": PERFORMANCE_THRESHOLDS,
        }
    )

@app.post("/api/voice/session")
async def create_voice_session(request: VoiceSessionRequest):
    try:
        start_time = asyncio.get_event_loop().time()
        
        success = await voice_agent.initialize(request.room_url, request.token)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to initialize voice agent")
        
        init_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        
        if init_time_ms > PERFORMANCE_THRESHOLDS["connection_setup_ms"]:
            logger.warning(f"Session initialization exceeded threshold: {init_time_ms:.2f}ms")
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "session_id": f"session_{int(datetime.utcnow().timestamp())}",
                "initialization_time_ms": round(init_time_ms, 2),
                "message": "Voice session created successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/voice/{client_id}")
async def voice_websocket_endpoint(websocket: WebSocket, client_id: str):
    connection_success = await manager.connect(websocket, client_id)
    if not connection_success:
        return
    
    try:
        logger.info(f"Starting voice session for client {client_id}")
        
        agent_initialized = await voice_agent.initialize()
        if not agent_initialized:
            await manager.send_message(client_id, {
                "type": "error",
                "message": "Failed to initialize voice agent"
            })
            return
        
        await manager.send_message(client_id, {
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Voice agent ready. You can start speaking!"
        })
        
        while True:
            try:
                data = await websocket.receive_text()
                message_start_time = asyncio.get_event_loop().time()
                
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": "Invalid JSON message format"
                    })
                    continue
                
                manager.connection_metrics[client_id]["messages_received"] += 1
                
                await process_websocket_message(client_id, message, message_start_time)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                })
                
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        manager.disconnect(client_id)
        try:
            await voice_agent.stop_conversation()
        except Exception as e:
            logger.error(f"Error stopping voice conversation: {e}")

async def process_websocket_message(client_id: str, message: Dict[str, Any], start_time: float):
    message_type = message.get("type")
    
    try:
        if message_type == "start_conversation":
            if not voice_agent.is_initialized:
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "Voice agent not initialized. Please refresh and try again."
                })
                return
                
            await voice_agent.start_conversation()
            await manager.send_message(client_id, {
                "type": "conversation_started",
                "message": "Voice conversation started. I'm listening!"
            })
            
        elif message_type == "audio_data":
            audio_data = message.get("data")
            if audio_data:
                try:
                    result = await voice_agent.process_audio_input(audio_data)
                    
                    if result["success"]:
                        await manager.send_message(client_id, {
                            "type": "audio_response",
                            "data": {
                                "response": result["response"],
                                "response_time_ms": result["response_time_ms"],
                                "text_extracted": result.get("text_extracted"),
                            }
                        })
                    else:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "data": {
                                "message": f"Audio processing failed: {result.get('error', 'Unknown error')}",
                                "details": result
                            }
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing audio data: {e}")
                    await manager.send_message(client_id, {
                        "type": "error",
                        "data": {"message": f"Audio processing error: {str(e)}"}
                    })
                
        elif message_type == "interrupt":
            await voice_agent.handle_interruption()
            await manager.send_message(client_id, {
                "type": "interruption_handled",
                "message": "Interruption processed"
            })
            
        elif message_type == "function_call":
            function_name = message.get("function_name")
            arguments = message.get("arguments", {})
            
            if function_name:
                result = await voice_agent.handle_function_call(function_name, arguments)
                await manager.send_message(client_id, {
                    "type": "function_result",
                    "function_name": function_name,
                    "result": result
                })
            
        elif message_type == "ping":
            await manager.send_message(client_id, {
                "type": "pong",
                "timestamp": message.get("timestamp"),
                "server_timestamp": datetime.utcnow().isoformat()
            })
            
        else:
            await manager.send_message(client_id, {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            })
        
        response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        if response_time_ms > PERFORMANCE_THRESHOLDS["voice_to_voice_latency_ms"]:
            logger.warning(f"Message processing exceeded latency threshold: {response_time_ms:.2f}ms")
            
    except Exception as e:
        logger.error(f"Error processing message type {message_type}: {e}")
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Error processing {message_type}: {str(e)}"
        })

@app.get("/api/forms/templates")
async def get_form_templates():
    return JSONResponse(content={
        "templates": list(voice_agent.form_manager.form_templates.keys()),
        "total_templates": len(voice_agent.form_manager.form_templates)
    })

@app.get("/api/metrics")
async def get_performance_metrics():
    voice_metrics = voice_agent.get_metrics()
    connection_metrics = manager.get_metrics()
    
    return JSONResponse(content={
        "timestamp": datetime.utcnow().isoformat(),
        "voice_agent": voice_metrics,
        "connections": connection_metrics,
        "thresholds": PERFORMANCE_THRESHOLDS,
        "system_info": {
            "active_connections": manager.get_connection_count(),
            "uptime_hours": 0,
        }
    })

@app.post("/api/test/voice-agent")
async def test_voice_agent():
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Endpoint not available in production")
    
    try:
        form_result = await voice_agent.handle_function_call("open_form", {
            "form_type": "contact",
            "title": "Test Contact Form"
        })
        
        fill_result = await voice_agent.handle_function_call("fill_form_field", {
            "field_name": "name",
            "value": "John Doe"
        })
        
        validation_result = await voice_agent.handle_function_call("validate_form", {})
        
        return JSONResponse(content={
            "success": True,
            "test_results": {
                "form_creation": form_result,
                "field_filling": fill_result,
                "form_validation": validation_result
            }
        })
        
    except Exception as e:
        logger.error(f"Voice agent test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Ultra-Low Latency Voice Agent")
    logger.info(f"Target latency: <{PERFORMANCE_THRESHOLDS['voice_to_voice_latency_ms']}ms")
    logger.info(f"Max connections: {settings.max_connections}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Voice Agent")
    try:
        await voice_agent.stop_conversation()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        access_log=settings.debug,
        ws_ping_interval=20,
        ws_ping_timeout=10,
        timeout_keep_alive=30,
        limit_concurrency=settings.max_connections,
    )

@app.websocket("/ws/rtvi/{client_id}")
async def rtvi_websocket_endpoint(websocket: WebSocket, client_id: str):
    connection_success = await manager.connect(websocket, client_id)
    if not connection_success:
        return
    
    try:
        logger.info(f"Starting RTVI session for client {client_id}")
        
        agent_initialized = await voice_agent.start_session(websocket, client_id)
        if not agent_initialized:
            await manager.send_message(client_id, {
                "type": "rtvi-error",
                "data": {"message": "Failed to initialize RTVI voice agent"}
            })
            return
        
        await manager.send_message(client_id, {
            "type": "rtvi-setup-complete",
            "data": {
                "client_id": client_id,
                "protocol_version": "0.2",
                "services": ["voice_agent"],
                "timestamp": datetime.utcnow().isoformat(),
                "message": "RTVI voice agent ready. You can start speaking!"
            }
        })
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type", "")
                message_data = message.get("data", {})
                
                if message_type == "rtvi-setup":
                    await manager.send_message(client_id, {
                        "type": "rtvi-setup-complete",
                        "data": {"success": True, "message": "Configuration updated"}
                    })
                
                elif message_type == "rtvi-audio-in":
                    audio_data = message_data.get("audio", [])
                    if audio_data:
                        audio_bytes = bytes(audio_data) if isinstance(audio_data, list) else audio_data
                        result = await audio_stream_processor.process_audio_stream(audio_bytes)
                        
                        if not result.get("success", False):
                            await manager.send_message(client_id, {
                                "type": "rtvi-error",
                                "data": {"message": "Audio processing failed"}
                            })
                
                elif message_type == "rtvi-action":
                    service = message_data.get("service", "")
                    action = message_data.get("action", "")
                    arguments = message_data.get("arguments", {})
                    action_id = message_data.get("action_id", "")
                    
                    if service == "voice_agent":
                        result = None
                        if action == "open_form":
                            result = await voice_agent.form_manager.open_form(
                                arguments.get("form_type", "contact"),
                                arguments.get("title", "Voice Form")
                            )
                        elif action == "fill_field":
                            result = await voice_agent.form_manager.fill_field(
                                arguments.get("field_name"),
                                arguments.get("value")
                            )
                        elif action == "submit_form":
                            result = await voice_agent.form_manager.submit_form()
                        elif action == "get_metrics":
                            result = {"success": True, "metrics": voice_agent.get_metrics()}
                        else:
                            result = {"success": False, "error": f"Unknown action: {action}"}
                        
                        await manager.send_message(client_id, {
                            "type": "rtvi-action-result",
                            "data": {
                                "action_id": action_id,
                                "success": result.get("success", False),
                                "result": result,
                                "error": result.get("error")
                            }
                        })
                
                elif message_type == "rtvi-ping":
                    await manager.send_message(client_id, {
                        "type": "rtvi-pong",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    })
                
                else:
                    logger.warning(f"Unknown RTVI message type: {message_type}")
                    await manager.send_message(client_id, {
                        "type": "rtvi-error",
                        "data": {"message": f"Unknown message type: {message_type}"}
                    })
                
            except WebSocketDisconnect:
                logger.info(f"RTVI client {client_id} disconnected")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from RTVI client {client_id}: {e}")
                await manager.send_message(client_id, {
                    "type": "rtvi-error",
                    "data": {"message": "Invalid JSON format"}
                })
            except Exception as e:
                logger.error(f"Error processing RTVI message from {client_id}: {e}")
                await manager.send_message(client_id, {
                    "type": "rtvi-error",
                    "data": {"message": f"Processing error: {str(e)}"}
                })
    
    except Exception as e:
        logger.error(f"Fatal error in RTVI session for {client_id}: {e}")
    finally:
        try:
            await voice_agent.stop_session()
            await manager.disconnect(websocket, client_id)
            logger.info(f"RTVI session cleanup completed for {client_id}")
        except Exception as cleanup_error:
            logger.error(f"Error during RTVI cleanup for {client_id}: {cleanup_error}")
