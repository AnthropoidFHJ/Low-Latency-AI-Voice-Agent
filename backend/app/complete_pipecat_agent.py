import asyncio
import logging
from typing import Dict, Any, Optional
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
    BotInterruptionFrame,
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
from pipecat.transports.network.websocket_server import (
    WebsocketServerTransport,
    WebsocketServerParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from .config import settings, PERFORMANCE_THRESHOLDS
from .tools.form_manager import FormManager, FormTool
from .services.gemini_live_service import gemini_live_service
from .services.audio_stream_processor import audio_stream_processor
logger = logging.getLogger(__name__)
class CompletePipecatVoiceAgent:
    def __init__(self):
        self.form_manager = FormManager()
        self.form_tool = FormTool(self.form_manager)
        self.pipeline = None
        self.runner = None
        self.task = None
        self.transport = None
        self.is_initialized = False
        self.current_websocket = None
        self.current_client_id = None
        self.gemini_live = gemini_live_service
        self.audio_processor = audio_stream_processor
        self.metrics = {
            "total_requests": 0,
            "avg_latency_ms": 0,
            "active_connections": 0,
            "last_response_time": None,
            "voice_to_voice_latency": [],
            "rtvi_actions_handled": 0,
        }
        self._setup_callbacks()
    def _setup_callbacks(self):
        self.audio_processor.set_callbacks(
            on_voice_start=self._on_voice_start,
            on_voice_end=self._on_voice_end,
            on_audio_chunk=self._on_audio_chunk
        )
        self.gemini_live.set_callbacks(
            on_audio_response=self._on_gemini_audio_response,
            on_text_response=self._on_gemini_text_response,
            on_function_call=self._on_gemini_function_call
        )
    async def create_rtvi_pipeline(self, websocket) -> Pipeline:
        try:
            transport_params = WebsocketServerParams(
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(
                    sample_rate=16000,
                    threshold=0.5
                ),
                vad_audio_passthrough=True,
                serializer=ProtobufFrameSerializer()
            )
            self.transport = WebsocketServerTransport(
                websocket=websocket,
                params=transport_params
            )
            rtvi_processor = RTVIProcessor(
                services=[
                    RTVIService(
                        name="voice_agent",
                        options=[
                            RTVIServiceOption(
                                name="model",
                                type="string",
                                handler=self._handle_model_option
                            ),
                            RTVIServiceOption(
                                name="voice_settings",
                                type="object",
                                handler=self._handle_voice_settings_option
                            ),
                            RTVIServiceOption(
                                name="latency_mode",
                                type="string",
                                handler=self._handle_latency_mode_option
                            )
                        ]
                    )
                ],
                actions=[
                    RTVIAction(
                        name="open_form",
                        description="Open a voice-controlled form",
                        arguments=[
                            RTVIActionArgument(name="form_type", type="string", required=True),
                            RTVIActionArgument(name="title", type="string", required=False)
                        ],
                        handler=self._handle_open_form_action
                    ),
                    RTVIAction(
                        name="fill_field",
                        description="Fill a form field with voice input",
                        arguments=[
                            RTVIActionArgument(name="field_name", type="string", required=True),
                            RTVIActionArgument(name="value", type="string", required=True)
                        ],
                        handler=self._handle_fill_field_action
                    ),
                    RTVIAction(
                        name="submit_form",
                        description="Submit the current form",
                        arguments=[],
                        handler=self._handle_submit_form_action
                    ),
                    RTVIAction(
                        name="get_metrics",
                        description="Get performance metrics",
                        arguments=[],
                        handler=self._handle_get_metrics_action
                    )
                ]
            )
            vad_analyzer = SileroVADAnalyzer(
                sample_rate=16000,
                threshold=0.5,
                min_silence_duration=0.3,
                min_speech_duration=0.1
            )
            pipeline = Pipeline([
                self.transport,
                vad_analyzer,
                rtvi_processor,
                self.transport
            ])
            return pipeline
        except Exception as e:
            logger.error(f"Failed to create RTVI pipeline: {e}")
            raise
    async def initialize(self, room_url: str = None, token: str = None) -> bool:
        try:
            if not self.is_initialized:
                logger.info("Initializing CompletePipecatVoiceAgent")
                self.is_initialized = True
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize CompletePipecatVoiceAgent: {e}")
            return False
    async def start_conversation(self):
        try:
            logger.info("Starting voice conversation")
            return True
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            raise
    async def stop_conversation(self):
        try:
            logger.info("Stopping voice conversation")
            if self.task:
                self.task.queue_frame(EndFrame())
                await self.task.stop()
                self.task = None
            if self.runner:
                await self.runner.stop()
                self.runner = None
            if self.pipeline:
                self.pipeline = None
            self.is_initialized = False
            logger.info("Voice conversation stopped")
        except Exception as e:
            logger.error(f"Error stopping conversation: {e}")
    async def process_audio_input(self, audio_data: str) -> Dict[str, Any]:
        try:
            import base64
            if isinstance(audio_data, str):
                try:
                    audio_bytes = base64.b64decode(audio_data)
                except Exception:
                    audio_bytes = audio_data.encode('utf-8')
            else:
                audio_bytes = audio_data
            result = await self.audio_processor.process_audio_chunk(audio_bytes)
            return {
                "success": True,
                "response": "Audio processed",
                "response_time_ms": 50,
                "text_extracted": result.get("text", ""),
                "voice_activity": result.get("voice_activity", False)
            }
        except Exception as e:
            logger.error(f"Error processing audio input: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    async def handle_interruption(self):
        try:
            logger.info("Handling conversation interruption")
            if self.task:
                self.task.queue_frame(BotInterruptionFrame())
        except Exception as e:
            logger.error(f"Error handling interruption: {e}")
    async def handle_function_call(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self.form_tool.execute(function_name, arguments)
        except Exception as e:
            logger.error(f"Error handling function call {function_name}: {e}")
            return {"error": str(e)}
    async def start_session(self, websocket, client_id: str) -> bool:
        try:
            logger.info(f"Starting RTVI voice session for client {client_id}")
            if not await self.gemini_live.initialize():
                logger.error("Failed to initialize Gemini Live API")
                return False
            self.pipeline = await self.create_rtvi_pipeline(websocket)
            self.task = PipelineTask(self.pipeline)
            self.runner = PipelineRunner()
            asyncio.create_task(self._run_pipeline())
            asyncio.create_task(self._listen_to_gemini())
            self.metrics["active_connections"] += 1
            logger.info(f"RTVI session started for {client_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start RTVI session: {e}")
            return False
    async def _run_pipeline(self):
        try:
            await self.runner.run(self.task)
        except Exception as e:
            logger.error(f"Error running pipeline: {e}")
        finally:
            await self.stop_session()
    async def _listen_to_gemini(self):
        try:
            async for response in self.gemini_live.start_listening():
                pass
        except Exception as e:
            logger.error(f"Error listening to Gemini Live: {e}")
    async def stop_session(self):
        try:
            if self.task:
                await self.task.queue_frame(EndFrame())
            if self.gemini_live:
                await self.gemini_live.close()
            self.metrics["active_connections"] = max(0, self.metrics["active_connections"] - 1)
            logger.info("RTVI session stopped")
        except Exception as e:
            logger.error(f"Error stopping session: {e}")
    async def _handle_open_form_action(self, processor, action_name: str, arguments: Dict[str, Any]):
        try:
            start_time = asyncio.get_event_loop().time()
            form_type = arguments.get("form_type", "contact")
            title = arguments.get("title", f"Voice {form_type.title()} Form")
            result = await self.form_manager.open_form(form_type, title)
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self.metrics["rtvi_actions_handled"] += 1
            return {
                "success": result.get("success", False),
                "form_id": result.get("form_id"),
                "message": result.get("message", "Form opened successfully"),
                "response_time_ms": response_time
            }
        except Exception as e:
            logger.error(f"Error handling open form action: {e}")
            return {"success": False, "error": str(e)}
    async def _handle_fill_field_action(self, processor, action_name: str, arguments: Dict[str, Any]):
        try:
            start_time = asyncio.get_event_loop().time()
            field_name = arguments.get("field_name")
            value = arguments.get("value")
            if not field_name or not value:
                return {"success": False, "error": "Missing field_name or value"}
            result = await self.form_manager.fill_field(field_name, value)
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self.metrics["rtvi_actions_handled"] += 1
            return {
                "success": result.get("success", False),
                "field_name": field_name,
                "value": value,
                "message": result.get("message", "Field filled successfully"),
                "response_time_ms": response_time
            }
        except Exception as e:
            logger.error(f"Error handling fill field action: {e}")
            return {"success": False, "error": str(e)}
    async def _handle_submit_form_action(self, processor, action_name: str, arguments: Dict[str, Any]):
        try:
            start_time = asyncio.get_event_loop().time()
            result = await self.form_manager.submit_form()
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self.metrics["rtvi_actions_handled"] += 1
            return {
                "success": result.get("success", False),
                "form_data": result.get("form_data"),
                "message": result.get("message", "Form submitted successfully"),
                "response_time_ms": response_time
            }
        except Exception as e:
            logger.error(f"Error handling submit form action: {e}")
            return {"success": False, "error": str(e)}
    async def _handle_get_metrics_action(self, processor, action_name: str, arguments: Dict[str, Any]):
        try:
            return {"success": True, "metrics": self.get_metrics()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    async def _handle_model_option(self, processor, option_name: str, config):
        logger.info(f"Model option updated: {config}")
    async def _handle_voice_settings_option(self, processor, option_name: str, config):
        logger.info(f"Voice settings updated: {config}")
    async def _handle_latency_mode_option(self, processor, option_name: str, config):
        logger.info(f"Latency mode updated: {config}")
    async def _on_voice_start(self, event: Dict[str, Any]):
        logger.debug("Voice activity started")
        if self.task:
            await self.task.queue_frame(TextFrame("Voice activity started"))
    async def _on_voice_end(self, event: Dict[str, Any]):
        logger.debug("Voice activity ended")
        if self.task:
            await self.task.queue_frame(TextFrame("Voice activity ended"))
    async def _on_audio_chunk(self, event: Dict[str, Any]):
        try:
            audio_data = event.get("audio_data")
            if audio_data and event.get("is_speech", False):
                await self.gemini_live.send_audio_chunk(audio_data)
                if self.task:
                    audio_frame = AudioRawFrame(
                        audio=audio_data,
                        sample_rate=16000,
                        num_channels=1
                    )
                    await self.task.queue_frame(audio_frame)
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
    async def _on_gemini_audio_response(self, response: Dict[str, Any]):
        try:
            audio_data = response.get("audio_data")
            if audio_data and self.task:
                audio_frame = TTSAudioRawFrame(
                    audio=audio_data,
                    sample_rate=16000,
                    num_channels=1
                )
                await self.task.queue_frame(audio_frame)
                response_time = response.get("response_time_ms", 0)
                self.metrics["voice_to_voice_latency"].append(response_time)
                self.metrics["last_response_time"] = response_time
                logger.debug(f"Audio response processed with {response_time}ms latency")
        except Exception as e:
            logger.error(f"Error handling Gemini audio response: {e}")
    async def _on_gemini_text_response(self, response: Dict[str, Any]):
        try:
            text = response.get("text")
            if text and self.task:
                text_frame = TextFrame(text)
                await self.task.queue_frame(text_frame)
        except Exception as e:
            logger.error(f"Error handling Gemini text response: {e}")
    async def _on_gemini_function_call(self, response: Dict[str, Any]) -> Dict[str, Any]:
        try:
            function_name = response.get("function_name")
            arguments = response.get("arguments", {})
            logger.info(f"Handling Gemini function call: {function_name}")
            if function_name == "open_form":
                return await self.form_manager.open_form(
                    arguments.get("form_type", "contact"),
                    arguments.get("title", "Voice Form")
                )
            elif function_name == "fill_field":
                return await self.form_manager.fill_field(
                    arguments.get("field_name"),
                    arguments.get("value")
                )
            elif function_name == "submit_form":
                return await self.form_manager.submit_form()
            else:
                return {"success": False, "error": f"Unknown function: {function_name}"}
        except Exception as e:
            logger.error(f"Error handling Gemini function call: {e}")
            return {"success": False, "error": str(e)}
    def get_metrics(self) -> Dict[str, Any]:
        voice_latencies = self.metrics["voice_to_voice_latency"]
        avg_voice_latency = sum(voice_latencies) / len(voice_latencies) if voice_latencies else 0
        return {
            **self.metrics,
            "avg_voice_to_voice_latency_ms": avg_voice_latency,
            "performance_target_met": avg_voice_latency < PERFORMANCE_THRESHOLDS["voice_to_voice_latency_ms"],
            "gemini_live_metrics": self.gemini_live.get_metrics(),
            "audio_processor_metrics": self.audio_processor.get_metrics(),
            "form_manager_stats": self.form_manager.stats,
        }
complete_pipecat_agent = CompletePipecatVoiceAgent()