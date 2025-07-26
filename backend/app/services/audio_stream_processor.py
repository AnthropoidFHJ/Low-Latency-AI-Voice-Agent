import asyncio
import logging
import numpy as np
from typing import Dict, Any, Optional, Callable, AsyncGenerator
import audioop
from datetime import datetime
logger = logging.getLogger(__name__)
class SimplePythonVAD:
    def __init__(self, aggressiveness: int = 2):
        self.aggressiveness = aggressiveness
        self.energy_thresholds = [500, 1000, 2000, 4000]
        self.energy_threshold = self.energy_thresholds[min(aggressiveness, 3)]
    def is_speech(self, audio_data: bytes, sample_rate: int) -> bool:
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            if len(audio_array) == 0:
                return False
            rms_energy = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))
            return rms_energy > self.energy_threshold
        except Exception as e:
            logger.warning(f"VAD processing error: {e}")
            return False
class AudioStreamProcessor:
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.frame_duration = 20
        self.vad = SimplePythonVAD(aggressiveness=2)
        self.vad_frame_size = int(sample_rate * self.frame_duration / 1000)
        self.audio_buffer = bytearray()
        self.is_speaking = False
        self.silence_duration = 0
        self.silence_threshold = 0.5
        self.metrics = {
            "chunks_processed": 0,
            "voice_detected_chunks": 0,
            "silence_detected_chunks": 0,
            "avg_processing_time_ms": 0,
            "buffer_size": 0,
        }
        self.on_voice_start: Optional[Callable] = None
        self.on_voice_end: Optional[Callable] = None
        self.on_audio_chunk: Optional[Callable] = None
    def set_callbacks(self,
                     on_voice_start: Optional[Callable] = None,
                     on_voice_end: Optional[Callable] = None,
                     on_audio_chunk: Optional[Callable] = None) -> None:
        self.on_voice_start = on_voice_start
        self.on_voice_end = on_voice_end
        self.on_audio_chunk = on_audio_chunk
    async def process_audio_stream(self, audio_data: bytes) -> Dict[str, Any]:
        start_time = asyncio.get_event_loop().time()
        try:
            self.audio_buffer.extend(audio_data)
            self.metrics["buffer_size"] = len(self.audio_buffer)
            results = []
            while len(self.audio_buffer) >= self.vad_frame_size * 2:
                frame_bytes = bytes(self.audio_buffer[:self.vad_frame_size * 2])
                self.audio_buffer = self.audio_buffer[self.vad_frame_size * 2:]
                is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
                voice_activity_changed = await self._handle_voice_activity(is_speech)
                if self.is_speaking or voice_activity_changed:
                    chunk_result = await self._process_audio_chunk(frame_bytes, is_speech)
                    results.append(chunk_result)
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self.metrics["avg_processing_time_ms"] = (
                (self.metrics["avg_processing_time_ms"] * self.metrics["chunks_processed"] + processing_time) /
                (self.metrics["chunks_processed"] + 1)
            )
            self.metrics["chunks_processed"] += 1
            return {
                "success": True,
                "chunks_processed": len(results),
                "is_speaking": self.is_speaking,
                "processing_time_ms": processing_time,
                "buffer_size": len(self.audio_buffer),
                "results": results
            }
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": (asyncio.get_event_loop().time() - start_time) * 1000
            }
    async def _handle_voice_activity(self, is_speech: bool) -> bool:
        voice_activity_changed = False
        if is_speech:
            self.silence_duration = 0
            if not self.is_speaking:
                self.is_speaking = True
                voice_activity_changed = True
                self.metrics["voice_detected_chunks"] += 1
                if self.on_voice_start:
                    await self.on_voice_start({
                        "timestamp": datetime.utcnow().isoformat(),
                        "event": "voice_start"
                    })
                logger.debug("Voice activity started")
        else:
            self.silence_duration += self.frame_duration / 1000.0  
            self.metrics["silence_detected_chunks"] += 1
            if self.is_speaking and self.silence_duration >= self.silence_threshold:
                self.is_speaking = False
                voice_activity_changed = True
                self.silence_duration = 0
                if self.on_voice_end:
                    await self.on_voice_end({
                        "timestamp": datetime.utcnow().isoformat(),
                        "event": "voice_end"
                    })
                logger.debug("Voice activity ended")
        return voice_activity_changed
    async def _process_audio_chunk(self, audio_chunk: bytes, is_speech: bool) -> Dict[str, Any]:
        try:
            processed_chunk = self._preprocess_audio(audio_chunk)
            if self.on_audio_chunk:
                await self.on_audio_chunk({
                    "audio_data": processed_chunk,
                    "is_speech": is_speech,
                    "timestamp": datetime.utcnow().isoformat(),
                    "chunk_size": len(processed_chunk)
                })
            return {
                "success": True,
                "chunk_size": len(processed_chunk),
                "is_speech": is_speech,
                "processed": True
            }
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_speech": is_speech
            }
    async def process_audio_chunk(self, audio_data: bytes) -> Dict[str, Any]:
        try:
            if not isinstance(audio_data, bytes):
                raise ValueError(f"Expected bytes, got {type(audio_data)}")
            if len(audio_data) == 0:
                return {
                    "success": True,
                    "message": "Empty audio chunk, skipping",
                    "is_speaking": self.is_speaking,
                    "voice_activity": False
                }
            min_chunk_size = self.vad_frame_size * 2
            if len(audio_data) < min_chunk_size:
                padding_needed = min_chunk_size - len(audio_data)
                audio_data = audio_data + b'\x00' * padding_needed
                logger.debug(f"Padded audio chunk from {len(audio_data) - padding_needed} to {len(audio_data)} bytes")
            is_speech = self.vad.is_speech(audio_data[:min_chunk_size], self.sample_rate)
            await self._handle_voice_activity(is_speech)
            result = await self._process_audio_chunk(audio_data, is_speech)
            self.metrics["chunks_processed"] += 1
            return {
                **result,
                "is_speaking": self.is_speaking,
                "voice_activity": is_speech,
                "chunk_size_bytes": len(audio_data)
            }
        except Exception as e:
            logger.error(f"Error in process_audio_chunk: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_speaking": self.is_speaking,
                "voice_activity": False
            }
    def _preprocess_audio(self, audio_data: bytes) -> bytes:
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            if len(audio_array) > 1:
                filtered = np.diff(audio_array, prepend=audio_array[0])
                audio_array = np.clip(filtered * 0.8, -32768, 32767).astype(np.int16)
            if len(audio_array) > 0:
                max_val = np.max(np.abs(audio_array))
                if max_val > 0:
                    normalization_factor = min(2.0, 16384 / max_val)
                    audio_array = (audio_array * normalization_factor).astype(np.int16)
            return audio_array.tobytes()
        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            return audio_data
    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "is_speaking": self.is_speaking,
            "silence_duration": self.silence_duration,
            "sample_rate": self.sample_rate,
            "chunk_size": self.chunk_size,
            "vad_frame_size": self.vad_frame_size
        }
    def reset_state(self) -> None:
        self.audio_buffer.clear()
        self.is_speaking = False
        self.silence_duration = 0
        self.metrics["buffer_size"] = 0
        logger.debug("Audio stream processor state reset")
class AudioFormatConverter:
    @staticmethod
    def convert_sample_rate(audio_data: bytes, from_rate: int, to_rate: int) -> bytes:
        if from_rate == to_rate:
            return audio_data
        try:
            converted = audioop.ratecv(audio_data, 2, 1, from_rate, to_rate, None)[0]
            return converted
        except Exception as e:
            logger.error(f"Error converting sample rate: {e}")
            return audio_data
    @staticmethod
    def convert_to_float32(audio_data: bytes) -> np.ndarray:
        try:
            int16_array = np.frombuffer(audio_data, dtype=np.int16)
            float32_array = int16_array.astype(np.float32) / 32768.0
            return float32_array
        except Exception as e:
            logger.error(f"Error converting to float32: {e}")
            return np.array([], dtype=np.float32)
    @staticmethod
    def convert_from_float32(audio_array: np.ndarray) -> bytes:
        try:
            int16_array = (audio_array * 32767).astype(np.int16)
            return int16_array.tobytes()
        except Exception as e:
            logger.error(f"Error converting from float32: {e}")
            return b''
audio_stream_processor = AudioStreamProcessor()