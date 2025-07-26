import asyncio
import logging
import json
import base64
import io
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from .config import settings, AUDIO_CONFIG, GEMINI_CONFIG
from .tools.form_manager import FormManager
logger = logging.getLogger(__name__)
class UltraLowLatencyVoiceAgent:
    def __init__(self):
        self.form_manager = FormManager()
        self.is_initialized = False
        self.last_request_time = 0
        self.min_request_interval = 2.0
        self.request_count = 0
        self.request_limit_per_minute = 15
        self.request_times = []
        self.metrics = {
            "total_requests": 0,
            "avg_latency_ms": 0,
            "active_connections": 0,
            "last_response_time": None,
            "rate_limited_requests": 0,
        }
        self._initialize_gemini()
    def _initialize_gemini(self):
        try:
            genai.configure(api_key=settings.google_api_key)
            self.generation_config = GenerationConfig(
                temperature=GEMINI_CONFIG["temperature"],
                top_p=GEMINI_CONFIG["top_p"],
                max_output_tokens=GEMINI_CONFIG["max_output_tokens"],
            )
            self.model = genai.GenerativeModel(
                model_name=GEMINI_CONFIG["model"],
                generation_config=self.generation_config,
            )
            logger.info("Gemini API initialized successfully (without tools)")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
            raise
    async def initialize(self, room_url: str = None, token: str = None) -> bool:
        try:
            self.is_initialized = True
            logger.info("Voice agent initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize voice agent: {e}")
            return False
    def _get_form_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "function_declarations": [
                    {
                        "name": "open_form",
                        "description": "Open a new form for the user to fill out",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "form_type": {
                                    "type": "string",
                                    "description": "Type of form to open (contact, registration, feedback, etc.)",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Title or name of the form",
                                }
                            },
                            "required": ["form_type"]
                        }
                    },
                    {
                        "name": "fill_form_field",
                        "description": "Fill a specific field in the currently open form",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "field_name": {
                                    "type": "string",
                                    "description": "Name of the form field to fill",
                                },
                                "value": {
                                    "type": "string",
                                    "description": "Value to enter in the field",
                                }
                            },
                            "required": ["field_name", "value"]
                        }
                    },
                    {
                        "name": "submit_form",
                        "description": "Submit the currently open form",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "confirm": {
                                    "type": "boolean",
                                    "description": "Confirm form submission",
                                    "default": True
                                }
                            }
                        }
                    },
                    {
                        "name": "validate_form",
                        "description": "Validate the current form and check for any missing or invalid fields",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        ]
    async def handle_function_call(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        try:
            if function_name == "open_form":
                result = await self.form_manager.open_form(
                    form_type=arguments.get("form_type"),
                    title=arguments.get("title", "")
                )
            elif function_name == "fill_form_field":
                result = await self.form_manager.fill_field(
                    field_name=arguments["field_name"],
                    value=arguments["value"]
                )
            elif function_name == "submit_form":
                result = await self.form_manager.submit_form(
                    confirm=arguments.get("confirm", True)
                )
            elif function_name == "validate_form":
                result = await self.form_manager.validate_form()
            else:
                result = {"error": f"Unknown function: {function_name}"}
            response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            self.metrics["last_response_time"] = response_time_ms
            if response_time_ms > settings.form_validation_timeout * 1000:
                logger.warning(f"Tool response time exceeded threshold: {response_time_ms:.2f}ms")
            return result
        except Exception as e:
            logger.error(f"Error handling function call {function_name}: {e}")
            return {"error": str(e)}
    async def process_text_input(self, text: str) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        try:
            if settings.test_mode:
                await asyncio.sleep(0.2)
                return {
                    "success": True,
                    "response": f"[TEST MODE] I heard: '{text[:50]}...' - Voice input is working perfectly! The microphone is capturing your audio and streaming it to the backend successfully.",
                    "response_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            chat = self.model.start_chat()
            response = await chat.send_message_async(text)
            if not response or not response.candidates:
                logger.warning("Empty response from Gemini API")
                return {
                    "success": True,
                    "response": "I'm having trouble processing that. Could you please try again?",
                    "response_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            text_response = "I'm ready to help you!"
            try:
                if (response.candidates and 
                    len(response.candidates) > 0 and 
                    response.candidates[0].content and 
                    response.candidates[0].content.parts):
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            function_call = part.function_call
                            function_name = function_call.name
                            function_args = dict(function_call.args)
                            result = await self.handle_function_call(function_name, function_args)
                            function_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": result}
                                )
                            )
                            final_response = await chat.send_message_async(function_response)
                            if final_response and final_response.text:
                                text_response = final_response.text
                        else:
                            if response.text:
                                text_response = response.text
                else:
                    if hasattr(response, 'text') and response.text:
                        text_response = response.text
            except Exception as parse_error:
                logger.error(f"Error parsing response: {parse_error}")
                text_response = "I processed your request, but had trouble formatting the response. How else can I help you?"
            response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            self.metrics["last_response_time"] = response_time_ms
            self.metrics["total_requests"] += 1
            return {
                "success": True,
                "response": text_response,
                "response_time_ms": response_time_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000,
            }
    async def start_conversation(self) -> None:
        if not self.is_initialized:
            raise RuntimeError("Agent not initialized")
        try:
            logger.info("Starting ultra-low latency voice conversation")
            self.metrics["active_connections"] += 1
        except Exception as e:
            logger.error(f"Error during conversation: {e}")
            raise
    async def stop_conversation(self) -> None:
        try:
            self.metrics["active_connections"] = max(0, self.metrics["active_connections"] - 1)
            logger.info("Voice conversation stopped")
        except Exception as e:
            logger.error(f"Error stopping conversation: {e}")
    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "form_manager_stats": self.form_manager.get_stats(),
            "timestamp": datetime.utcnow().isoformat(),
            "is_initialized": self.is_initialized,
        }
    async def handle_interruption(self) -> None:
        try:
            logger.debug("Interruption handled successfully")
        except Exception as e:
            logger.error(f"Error handling interruption: {e}")
    async def process_audio_input(self, audio_data: str) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        try:
            if not self._check_rate_limit():
                self.metrics["rate_limited_requests"] += 1
                return {
                    "success": False,
                    "error": "Rate limited - too many requests. Please speak slower or wait a moment.",
                    "rate_limited": True,
                    "response_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000,
                }
            self._record_request()
            audio_bytes = base64.b64decode(audio_data)
            logger.info(f"Received audio data: {len(audio_bytes)} bytes")
            await asyncio.sleep(0.1)
            simulated_text = "I heard your voice input. This is a simulated response while we work on speech-to-text integration."
            text_result = await self.process_text_input(simulated_text)
            response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            return {
                "success": True,
                "audio_processed": True,
                "text_extracted": simulated_text,
                "response": text_result.get("response", "Audio processed successfully"),
                "response_time_ms": response_time_ms,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error processing audio input: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000,
            }
    def _check_rate_limit(self) -> bool:
        current_time = time.time()
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        if current_time - self.last_request_time < self.min_request_interval:
            logger.warning(f"Rate limit: Too frequent requests. Wait {self.min_request_interval}s between requests")
            return False
        if len(self.request_times) >= self.request_limit_per_minute:
            logger.warning(f"Rate limit: Exceeded {self.request_limit_per_minute} requests per minute")
            return False
        return True
    def _record_request(self):
        current_time = time.time()
        self.last_request_time = current_time
        self.request_times.append(current_time)
voice_agent = UltraLowLatencyVoiceAgent()