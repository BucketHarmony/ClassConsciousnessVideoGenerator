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

logger = get_script_logger()

# System prompt for script generation
SYSTEM_PROMPT = """You are a documentary scriptwriter specializing in connecting current events to historical class struggles.

Your task is to write compelling narration scripts that:
1. Open with today's news story
2. Transition to the historical parallel
3. Draw meaningful connections between past and present
4. End with insight or call to reflection

IMPORTANT: Embed visual markers in your script using [v1], [v2], etc. format.
Each marker indicates where a new image should appear in the video.

Guidelines for visual markers:
- Place markers at natural transition points
- Each marker should have 5-15 seconds of narration
- Use markers to highlight key moments, people, and events
- Suggest what type of image should appear

Your response must be valid JSON with the structure specified."""

# Response schema for script generation
RESPONSE_SCHEMA = """
{
  "title": "string - compelling title for the video",
  "segments": [
    {
      "id": 1,
      "text": "string - narration text with [v1], [v2] markers embedded",
      "mood": "string - emotional tone (somber, hopeful, urgent, contemplative)",
      "pacing": "string - slow, normal, or fast",
      "visual_markers": [
        {
          "id": "v1",
          "description": "what the visual should show",
          "search_terms": ["term1", "term2", "term3"],
          "visual_type": "historical_photo|historical_artwork|news_image|portrait|scene|map",
          "mood": "somber|hopeful|urgent|contemplative|neutral",
          "motion": "slow_zoom_in|slow_zoom_out|pan_left|pan_right|static",
          "era": "optional era like '1930s' or 'Victorian'",
          "location": "optional location"
        }
      ]
    }
  ],
  "tone": "overall tone",
  "style": "documentary style used"
}
"""


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
        """Build the prompt for script generation."""
        # Calculate target word count (roughly 150 words per minute)
        target_words = int((target_duration / 60) * 150)
        marker_count = max(3, target_duration // 10)  # One marker per ~10 seconds

        return f"""Write a documentary narration script connecting this news story to its historical parallel.

{research.to_prompt_context()}

REQUIREMENTS:
- Target duration: approximately {target_duration} seconds ({target_words} words)
- Include {marker_count}-{marker_count + 3} visual markers [v1], [v2], etc.
- Style: {style}
- Structure: 3-5 segments (intro, news context, historical parallel, connection, conclusion)

VISUAL MARKER PLACEMENT:
- Place [v1] near the opening to show contemporary context
- Place markers at each major transition
- Include markers for key historical figures and events
- End with a reflective visual

The script should flow naturally when read aloud. Make it compelling and thought-provoking.

Respond with a JSON object following this schema:
{RESPONSE_SCHEMA}"""

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
            {"role": "system", "content": SYSTEM_PROMPT},
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
        """Generate additional search terms for a marker."""
        prompt = f"""Generate 5 specific image search terms for this visual:

Description: {marker.description}
Type: {marker.visual_type.value}
Era: {marker.era or 'not specified'}
Location: {marker.location or 'not specified'}

Return only a JSON array of search terms, e.g.: ["term1", "term2", "term3", "term4", "term5"]"""

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
