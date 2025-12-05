"""
Prompts module for AI Ken Burns.

Centralizes all LLM prompts for easy customization and maintenance.
"""

from ai_ken_burns.prompts.templates import PromptTemplate, load_prompt
from ai_ken_burns.prompts.research import (
    HISTORICAL_CONNECTION_SYSTEM,
    HISTORICAL_CONNECTION_USER,
)
from ai_ken_burns.prompts.script import (
    SCRIPT_GENERATION_SYSTEM,
    SCRIPT_GENERATION_USER,
)
from ai_ken_burns.prompts.image import (
    IMAGE_PROMPT_SYSTEM,
    IMAGE_PROMPT_USER,
)

__all__ = [
    "PromptTemplate",
    "load_prompt",
    "HISTORICAL_CONNECTION_SYSTEM",
    "HISTORICAL_CONNECTION_USER",
    "SCRIPT_GENERATION_SYSTEM",
    "SCRIPT_GENERATION_USER",
    "IMAGE_PROMPT_SYSTEM",
    "IMAGE_PROMPT_USER",
]
