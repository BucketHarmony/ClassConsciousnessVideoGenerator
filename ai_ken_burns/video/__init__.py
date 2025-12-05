"""
Video pipeline for AI Ken Burns.

Modules:
- models: Data models for video segments
- ken_burns: Ken Burns effect motion generation
- renderer: FFmpeg-based video rendering
"""

from ai_ken_burns.video.models import VideoSegment, RenderSpec
from ai_ken_burns.video.ken_burns import KenBurnsEngine, generate_motion
from ai_ken_burns.video.renderer import VideoRenderer, render_video

__all__ = [
    "VideoSegment",
    "RenderSpec",
    "KenBurnsEngine",
    "generate_motion",
    "VideoRenderer",
    "render_video",
]
