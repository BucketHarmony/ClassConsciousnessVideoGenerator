"""
Prompt template utilities for AI Ken Burns.

Provides a flexible system for managing and formatting LLM prompts.
"""

from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Optional


class PromptTemplate:
    """
    A template for LLM prompts with variable substitution.

    Supports both simple string formatting and Template-style substitution.

    Example:
        template = PromptTemplate(
            "Analyze the following news story: ${title}\\n\\n${summary}"
        )
        prompt = template.format(title="Workers Strike", summary="...")
    """

    def __init__(self, template: str, name: Optional[str] = None) -> None:
        """
        Initialize a prompt template.

        Args:
            template: The template string with ${variable} placeholders
            name: Optional name for the template (for logging/debugging)
        """
        self.template = template
        self.name = name
        self._template = Template(template)

    def format(self, **kwargs) -> str:
        """
        Format the template with the given variables.

        Args:
            **kwargs: Variables to substitute into the template

        Returns:
            Formatted prompt string
        """
        return self._template.safe_substitute(**kwargs)

    def __str__(self) -> str:
        return self.template

    def __repr__(self) -> str:
        name = f" name={self.name!r}" if self.name else ""
        return f"PromptTemplate({self.template[:50]!r}...{name})"


def load_prompt(path: Path) -> PromptTemplate:
    """
    Load a prompt template from a file.

    Args:
        path: Path to the prompt file

    Returns:
        PromptTemplate loaded from the file
    """
    content = path.read_text(encoding="utf-8")
    return PromptTemplate(content, name=path.stem)


def format_list(items: list[str], bullet: str = "-") -> str:
    """
    Format a list of items as bullet points.

    Args:
        items: List of strings to format
        bullet: Bullet character to use

    Returns:
        Formatted string with bullet points
    """
    return "\n".join(f"{bullet} {item}" for item in items)


def format_numbered(items: list[str]) -> str:
    """
    Format a list of items as numbered points.

    Args:
        items: List of strings to format

    Returns:
        Formatted string with numbered points
    """
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
