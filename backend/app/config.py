import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    google_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    test_mode: bool = False
    
    max_connections: int = 100
    connection_timeout: int = 30
    audio_buffer_size: int = 1024
    sample_rate: int = 16000
    channels: int = 1
    
    rtvi_secret_key: Optional[str] = None
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    enable_auth: bool = False
    
    voice_activity_timeout: float = 0.5
    interruption_threshold: float = 0.3
    
    max_form_fields: int = 20
    form_validation_timeout: float = 1.0
    
    log_level: str = "INFO"
    enable_metrics: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

AUDIO_CONFIG = {
    "sample_rate": settings.sample_rate,
    "channels": settings.channels,
    "format": "int16",
    "chunk_size": settings.audio_buffer_size,
    "enable_vad": True,
    "vad_threshold": 0.5,
    "noise_reduction": True,
    "echo_cancellation": True,
}

GEMINI_CONFIG = {
    "model": settings.gemini_model,
    "temperature": 0.7,
    "max_output_tokens": 1000,
    "top_p": 0.9,
    "stream": True,
    "enable_audio": True,
    "voice_settings": {
        "voice_id": "en-US-Neural2-J",
        "speaking_rate": 1.0,
        "pitch": 0.0,
        "volume_gain_db": 0.0,
    }
}

PERFORMANCE_THRESHOLDS = {
    "voice_to_voice_latency_ms": 500,
    "connection_setup_ms": 2000,
    "tool_response_ms": 1000,
    "audio_quality_threshold": 0.8,
}
