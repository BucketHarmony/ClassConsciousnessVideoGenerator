"""
Script generation pipeline for AI Ken Burns.

Modules:
- models: Data models for scripts and visual markers
- generator: LLM-based script generation with visual annotations
"""

from ai_ken_burns.script.models import (
    VisualMarker,
    ScriptSegment,
    AnnotatedScript,
)
from ai_ken_burns.script.generator import ScriptGenerator, generate_script

__all__ = [
    "VisualMarker",
    "ScriptSegment",
    "AnnotatedScript",
    "ScriptGenerator",
    "generate_script",
]
