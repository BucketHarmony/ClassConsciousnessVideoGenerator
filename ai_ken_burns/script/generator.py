"""
Script generator for AI Ken Burns.

Uses LLM to generate narration scripts with embedded visual markers
that guide the Ken Burns video generation.
"""

from __future__ import annotations

import re
from typing import Optional

from ai_ken_burns.clients.openai_client import get_openai_client, APIResponse
from ai_ken_burns.config import get_config
from ai_ken_burns.research.models import ResearchOutput
from ai_ken_burns.script.models import (
    AnnotatedScript,
    ScriptSegment,
    VisualMarker,
    VisualType,
    MotionSuggestion,
)
from ai_ken_burns.utils.logging_utils import get_script_logger, log_timing
from ai_ken_burns.prompts.script import (
    SCRIPT_GENERATION_SYSTEM,
    SCRIPT_GENERATION_USER,
    SCRIPT_RESPONSE_SCHEMA,
    SEARCH_TERMS_ENHANCEMENT,
)

logger = get_script_logger()


class ScriptGenerator:
    """
    Generates annotated narration scripts from research output.

    Uses GPT-4 to create documentary-style scripts with embedded
    visual markers for Ken Burns video generation.
    """

    def __init__(self) -> None:
        """Initialize the script generator."""
        self.config = get_config()
        self.client = get_openai_client()

    def _build_prompt(
        self,
        research: ResearchOutput,
        style: str,
        target_duration: int,
    ) -> str:
        """Build the prompt for script generation using prompts module."""
        # Calculate target word count (roughly 150 words per minute)
        target_words = int((target_duration / 60) * 150)
        marker_count = max(3, target_duration // 10)  # One marker per ~10 seconds

        return SCRIPT_GENERATION_USER.format(
            research_context=research.to_prompt_context(),
            target_duration=target_duration,
            target_words=target_words,
            marker_count_min=marker_count,
            marker_count_max=marker_count + 3,
            style=style,
            response_schema=SCRIPT_RESPONSE_SCHEMA,
        )

    def generate(
        self,
        research: ResearchOutput,
        style: str = "documentary style, thoughtful and engaging",
        target_duration: int = 90,
        temperature: float = 0.8,
    ) -> Optional[AnnotatedScript]:
        """
        Generate an annotated script from research output.

        Args:
            research: ResearchOutput from the research pipeline
            style: Style prompt for the narrative
            target_duration: Target duration in seconds
            temperature: LLM temperature for creativity

        Returns:
            AnnotatedScript with visual markers, or None if failed
        """
        logger.info(f"Generating script for: {research.news_story.title[:50]}...")
        logger.info(f"Target duration: {target_duration}s, Style: {style}")

        prompt = self._build_prompt(research, style, target_duration)

        messages = [
            {"role": "system", "content": str(SCRIPT_GENERATION_SYSTEM)},
            {"role": "user", "content": prompt},
        ]

        with log_timing("llm_script_generation", logger):
            response = self.client.chat_completion_json(
                messages=messages,
                model=self.config.llm.generation_model,
                temperature=temperature,
            )

        if not response.success:
            logger.error(f"LLM request failed: {response.error}")
            return None

        try:
            return self._parse_response(research, response, style)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None

    def _parse_response(
        self,
        research: ResearchOutput,
        response: APIResponse,
        style: str,
    ) -> AnnotatedScript:
        """Parse the LLM response into AnnotatedScript."""
        data = response.data

        segments = []
        for seg_data in data.get("segments", []):
            # Parse visual markers
            markers = []
            for marker_data in seg_data.get("visual_markers", []):
                marker = VisualMarker(
                    id=marker_data.get("id", f"v{len(markers) + 1}"),
                    description=marker_data.get("description", ""),
                    search_terms=marker_data.get("search_terms", []),
                    visual_type=self._parse_visual_type(marker_data.get("visual_type")),
                    mood=marker_data.get("mood", "neutral"),
                    motion=self._parse_motion(marker_data.get("motion")),
                    era=marker_data.get("era"),
                    location=marker_data.get("location"),
                )
                markers.append(marker)

            segment = ScriptSegment(
                id=seg_data.get("id", len(segments) + 1),
                text=seg_data.get("text", ""),
                visual_markers=markers,
                mood=seg_data.get("mood", "neutral"),
                pacing=seg_data.get("pacing", "normal"),
            )
            segments.append(segment)

        script = AnnotatedScript(
            title=data.get("title", "Class Consciousness Video"),
            news_title=research.news_story.title,
            historical_event=research.historical_event.name,
            thesis=research.thesis,
            style=style,
            tone=data.get("tone", "thoughtful"),
            segments=segments,
            llm_model=self.config.llm.generation_model,
        )

        logger.info(
            f"Generated script: {script.segment_count} segments, "
            f"{script.marker_count} visual markers, "
            f"~{script.estimate_duration():.0f}s estimated"
        )

        return script

    def _parse_visual_type(self, value: Optional[str]) -> VisualType:
        """Parse visual type string to enum."""
        if not value:
            return VisualType.HISTORICAL_PHOTO

        try:
            return VisualType(value.lower())
        except ValueError:
            return VisualType.HISTORICAL_PHOTO

    def _parse_motion(self, value: Optional[str]) -> MotionSuggestion:
        """Parse motion string to enum."""
        if not value:
            return MotionSuggestion.SLOW_ZOOM_IN

        try:
            return MotionSuggestion(value.lower())
        except ValueError:
            return MotionSuggestion.SLOW_ZOOM_IN

    def enhance_markers(self, script: AnnotatedScript) -> AnnotatedScript:
        """
        Enhance visual markers with additional search terms.

        Uses LLM to generate better search terms for image retrieval.
        """
        logger.info("Enhancing visual markers with search terms...")

        for segment in script.segments:
            for marker in segment.visual_markers:
                if len(marker.search_terms) < 3:
                    # Generate additional search terms
                    enhanced_terms = self._generate_search_terms(marker)
                    marker.search_terms = list(set(marker.search_terms + enhanced_terms))

        return script

    def _generate_search_terms(self, marker: VisualMarker) -> list[str]:
        """Generate additional search terms for a marker using prompts module."""
        prompt = SEARCH_TERMS_ENHANCEMENT.format(
            description=marker.description,
            visual_type=marker.visual_type.value,
            era=marker.era or 'not specified',
            location=marker.location or 'not specified',
        )

        response = self.client.chat_completion_json(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        if response.success and response.data:
            if isinstance(response.data, list):
                return response.data[:5]
            elif isinstance(response.data, dict) and "terms" in response.data:
                return response.data["terms"][:5]

        return []


def generate_script(
    research: ResearchOutput,
    style: str = "documentary style, thoughtful and engaging",
    target_duration: int = 90,
) -> Optional[AnnotatedScript]:
    """
    Convenience function to generate a script from research.

    Args:
        research: ResearchOutput from the research pipeline
        style: Style prompt for the narrative
        target_duration: Target duration in seconds

    Returns:
        AnnotatedScript with visual markers
    """
    generator = ScriptGenerator()
    return generator.generate(research, style, target_duration)
