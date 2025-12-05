"""
Audio pipeline for AI Ken Burns.

Modules:
- models: Data models for audio metadata
- tts_generator: OpenAI TTS-based audio generation
"""

from ai_ken_burns.audio.models import AudioSegment, AudioOutput
from ai_ken_burns.audio.tts_generator import TTSGenerator, generate_audio

__all__ = [
    "AudioSegment",
    "AudioOutput",
    "TTSGenerator",
    "generate_audio",
]
