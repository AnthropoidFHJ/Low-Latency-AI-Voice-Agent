import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pipecat.frames.frames import (
    Frame,
    AudioRawFrame,
    TextFrame,
    TranscriptionFrame,
    TTSAudioRawFrame,
    LLMMessagesFrame,
    EndFrame,
    FunctionCallInProgressFrame,
    FunctionCallResultFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import (
    RTVIProcessor,
    RTVIService,
    RTVIServiceOption,
    RTVIAction,
    RTVIActionArgument,
)
from pipecat.services.google import GoogleLLMService, GoogleTTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.transports.network.websocket_server import (
    WebsocketServerTransport,
    WebsocketServerParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from .config import settings, AUDIO_CONFIG, PERFORMANCE_THRESHOLDS
from .tools.form_manager import FormManager
from .services.gemini_live_service import gemini_live_service
from .services.audio_stream_processor import audio_stream_processor
logger = logging.getLogger(__name__)
class PipecatVoiceAgent:
    def __init__(self):
        self.form_manager = FormManager()
        self.pipeline = None
        self.runner = None
        self.task = None
        self.llm_service = None
        self.tts_service = None
        self.stt_service = None
        self.vad = None
        self._services_initialized = False
        self.metrics = {
            "total_requests": 0,
            "avg_latency_ms": 0,
            "active_connections": 0,
            "last_response_time": None,
            "voice_to_voice_latency": [],
        }
        logger.info("PipecatVoiceAgent initialized (services will be loaded when needed)")
    async def _ensure_services_initialized(self):
        if not self._services_initialized:
            await self._initialize_services()
    async def _initialize_services(self):
        if self._services_initialized:
            return
        try:
            self.llm_service = GoogleLLMService(
                api_key=settings.google_api_key,
                model="gemini-1.5-flash",
                max_tokens=1000,
                temperature=0.7,
            )
            self.tts_service = GoogleTTSService(
                api_key=settings.google_api_key,
                voice_id="en-US-Neural2-J",
                sample_rate=16000,
                language_code="en-US",
            )
            try:
                deepgram_key = os.getenv("DEEPGRAM_API_KEY")
                if deepgram_key:
                    self.stt_service = DeepgramSTTService(
                        api_key=deepgram_key,
                        model="nova-2",
                        language="en",
                        interim_results=True,
                    )
                else:
                    logger.warning("No Deepgram API key found. STT will be simulated.")
                    self.stt_service = None
            except Exception as e:
                logger.warning(f"Failed to initialize Deepgram STT: {e}")
                self.stt_service = None
            self.vad = SileroVADAnalyzer(
                sample_rate=16000,
                threshold=0.5,
            )
            self._services_initialized = True
            logger.info("Pipecat services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pipecat services: {e}")
            raise
    async def create_pipeline(self, transport: WebsocketServerTransport) -> Pipeline:
        await self._ensure_services_initialized()
        context = OpenAILLMContext(
            messages=[
                {
                    "role": "system",
                    "content": 
                }
            ]
        )
        processors = []
        processors.append(self.vad)
        if self.stt_service:
            processors.append(self.stt_service)
        else:
            processors.append(self._create_simulated_stt())
        processors.append(self.llm_service)
        processors.append(self.tts_service)
        pipeline = Pipeline(
            processors=processors,
            transport=transport,
        )
        return pipeline
    def _create_simulated_stt(self):
        class SimulatedSTT:
            async def process_frame(self, frame: Frame) -> Optional[Frame]:
                if isinstance(frame, AudioRawFrame):
                    return TranscriptionFrame(
                        text="I heard your voice input. How can I help you today?",
                        user_id="user",
                        timestamp=frame.timestamp,
                    )
                return frame
        return SimulatedSTT()
    async def start_session(self, websocket_url: str, room_id: str = "default") -> bool:
        try:
            await self._ensure_services_initialized()
            transport = WebsocketServerTransport(
                host="0.0.0.0",
                port=8001,
                websocket_path=f"/pipecat/{room_id}",
            )
            self.pipeline = await self.create_pipeline(transport)
            self.task = PipelineTask(
                pipeline=self.pipeline,
                params={
                    "room_id": room_id,
                    "user_id": "user",
                }
            )
            self.runner = PipelineRunner()
            await self.runner.run(self.task)
            logger.info(f"Pipecat voice session started for room: {room_id}")
            self.metrics["active_connections"] += 1
            return True
        except Exception as e:
            logger.error(f"Failed to start Pipecat session: {e}")
            return False
    async def stop_session(self):
        try:
            if self.task:
                await self.task.stop()
                self.task = None
            if self.runner:
                await self.runner.stop()
                self.runner = None
            self.pipeline = None
            self.metrics["active_connections"] = max(0, self.metrics["active_connections"] - 1)
            logger.info("Pipecat voice session stopped")
        except Exception as e:
            logger.error(f"Error stopping Pipecat session: {e}")
    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "form_manager_stats": self.form_manager.get_stats(),
            "pipecat_status": {
                "pipeline_active": self.pipeline is not None,
                "runner_active": self.runner is not None,
                "task_active": self.task is not None,
            }
        }
    async def handle_form_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if function_name == "open_form":
                return await self.form_manager.open_form(
                    form_type=arguments.get("form_type"),
                    title=arguments.get("title", "")
                )
            elif function_name == "fill_form_field":
                return await self.form_manager.fill_field(
                    field_name=arguments["field_name"],
                    value=arguments["value"]
                )
            elif function_name == "validate_form":
                return await self.form_manager.validate_form()
            elif function_name == "submit_form":
                return await self.form_manager.submit_form(
                    confirm=arguments.get("confirm", True)
                )
            else:
                return {"error": f"Unknown function: {function_name}"}
        except Exception as e:
            logger.error(f"Error handling form function {function_name}: {e}")
            return {"error": str(e)}
pipecat_agent = PipecatVoiceAgent()