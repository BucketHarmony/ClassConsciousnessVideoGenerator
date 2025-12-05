"""
AI Image Generator for AI Ken Burns.

Uses OpenAI DALL-E to generate documentary-style images
when historical image searches don't return suitable results.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from ai_ken_burns.clients.openai_client import get_openai_client
from ai_ken_burns.config import get_config
from ai_ken_burns.script.models import VisualMarker
from ai_ken_burns.images.models import ImageResult
from ai_ken_burns.utils.logging_utils import get_images_logger, log_timing

logger = get_images_logger()


class AIImageGenerator:
    """
    Generates images using DALL-E for documentary visuals.

    Creates high-quality, documentary-style images based on
    visual marker descriptions and historical context.
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        model: str = "dall-e-3",
        size: str = "1792x1024",
        quality: str = "standard",
        style: str = "natural",
    ) -> None:
        """
        Initialize the AI image generator.

        Args:
            output_dir: Directory to save generated images
            model: DALL-E model to use
            size: Image size (1792x1024 for landscape, 1024x1792 for portrait)
            quality: Image quality (standard or hd)
            style: Image style (natural or vivid)
        """
        self.config = get_config()
        self.client = get_openai_client()
        self.output_dir = output_dir or Path(self.config.paths.images_dir)
        self.model = model
        self.size = size
        self.quality = quality
        self.style = style

    def generate_for_marker(
        self,
        marker: VisualMarker,
        historical_context: str,
        output_dir: Optional[Path] = None,
    ) -> Optional[ImageResult]:
        """
        Generate an AI image for a visual marker.

        Args:
            marker: VisualMarker with description and search terms
            historical_context: Historical context for the image
            output_dir: Optional output directory override

        Returns:
            ImageResult with the generated image, or None if failed
        """
        output_dir = output_dir or self.output_dir
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating AI image for marker [{marker.id}]")

        # Build context from marker
        visual_description = marker.description
        if marker.search_terms:
            visual_description += f". Key elements: {', '.join(marker.search_terms[:3])}"

        # Add era and location if available
        style_hints = []
        if marker.era:
            style_hints.append(f"{marker.era} era")
        if marker.location:
            style_hints.append(f"set in {marker.location}")
        if marker.mood:
            style_hints.append(f"{marker.mood} mood")

        # Map visual type to style hints
        visual_type_hints = {
            "historical_photo": "vintage photograph, sepia or black and white, archival quality",
            "archival_footage": "historical documentary still, film grain, period authentic",
            "illustration": "detailed illustration, documentary style, historically accurate",
            "map": "historical map, vintage cartography, period-appropriate style",
            "portrait": "formal portrait, period-appropriate clothing and setting",
            "scene_recreation": "cinematic recreation, dramatic lighting, documentary quality",
            "symbolic": "symbolic imagery, metaphorical, artistic documentary style",
            "modern_footage": "modern documentary photography, journalistic style",
        }

        type_hint = visual_type_hints.get(marker.visual_type.value, "documentary photography")
        style_hints.append(type_hint)

        style_str = ", ".join(style_hints) if style_hints else None

        # Generate optimized prompt using GPT-4
        with log_timing(f"generate_prompt_{marker.id}", logger):
            prompt_response = self.client.generate_image_prompt(
                visual_description=visual_description,
                historical_context=historical_context,
                style_hints=style_str,
            )

        if not prompt_response.success:
            logger.error(f"Failed to generate prompt for [{marker.id}]: {prompt_response.error}")
            return None

        dalle_prompt = prompt_response.content
        logger.debug(f"Generated DALL-E prompt: {dalle_prompt[:100]}...")

        # Generate the image
        image_id = f"{marker.id}_{uuid.uuid4().hex[:12]}"
        output_path = output_dir / f"{image_id}.png"

        with log_timing(f"dalle_generate_{marker.id}", logger):
            image_response = self.client.generate_image(
                prompt=dalle_prompt,
                output_path=str(output_path),
                model=self.model,
                size=self.size,
                quality=self.quality,
                style=self.style,
            )

        if not image_response.success:
            logger.error(f"Failed to generate image for [{marker.id}]: {image_response.error}")
            return None

        # Get image dimensions from size string
        width, height = map(int, self.size.split("x"))

        # Create ImageResult
        revised_prompt = None
        if image_response.data:
            revised_prompt = image_response.data.get("revised_prompt")

        result = ImageResult(
            id=image_id,
            marker_id=marker.id,
            source_url="",  # AI generated, no source URL
            source_name="DALL-E AI Generated",
            title=f"AI Generated: {marker.description[:50]}",
            description=revised_prompt or dalle_prompt,
            local_path=str(output_path),
            is_downloaded=True,
            width=width,
            height=height,
            relevance_score=1.0,  # AI generated is always "relevant"
            is_ai_generated=True,
        )

        logger.info(f"Generated AI image for [{marker.id}]: {output_path.name}")

        return result

    def generate_batch(
        self,
        markers: list[VisualMarker],
        historical_context: str,
        output_dir: Optional[Path] = None,
    ) -> list[ImageResult]:
        """
        Generate AI images for multiple markers.

        Args:
            markers: List of VisualMarkers to generate images for
            historical_context: Historical context for all images
            output_dir: Optional output directory override

        Returns:
            List of successfully generated ImageResults
        """
        results = []

        for marker in markers:
            result = self.generate_for_marker(
                marker=marker,
                historical_context=historical_context,
                output_dir=output_dir,
            )
            if result:
                results.append(result)

        logger.info(f"Generated {len(results)}/{len(markers)} AI images")

        return results


def generate_ai_image(
    marker: VisualMarker,
    historical_context: str,
    output_dir: Path,
) -> Optional[ImageResult]:
    """
    Convenience function to generate a single AI image.

    Args:
        marker: VisualMarker to generate image for
        historical_context: Historical context
        output_dir: Output directory

    Returns:
        ImageResult or None if failed
    """
    generator = AIImageGenerator(output_dir=output_dir)
    return generator.generate_for_marker(marker, historical_context, output_dir)
