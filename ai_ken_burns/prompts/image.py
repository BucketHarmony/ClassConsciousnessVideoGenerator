"""
Image generation prompts for AI Ken Burns.

Prompts for generating DALL-E image prompts from visual markers.
"""

from ai_ken_burns.prompts.templates import PromptTemplate

# System prompt for DALL-E prompt generation
IMAGE_PROMPT_SYSTEM = PromptTemplate(
    """You are an expert at crafting DALL-E image generation prompts for documentary-style historical imagery.

Your prompts should:
1. Create evocative, historically accurate imagery
2. Use cinematic composition and lighting
3. Avoid text, logos, or modern elements unless specifically relevant
4. Specify artistic style (photograph, painting, illustration)
5. Include mood and atmosphere details
6. Be detailed but under 400 characters for best results
7. Include camera settings.
8. Describe composition, lighting, color palette, and any relevant historical details.

Output ONLY the prompt text, no explanations or quotes.""",
    name="image_prompt_system"
)

# User prompt for generating DALL-E prompts
IMAGE_PROMPT_USER = PromptTemplate(
    """Create a DALL-E prompt for this documentary visual:

Description: ${visual_description}
Historical Context: ${historical_context}
${style_hints_line}

Generate a single, detailed image prompt.""",
    name="image_prompt_user"
)

# Visual type style mappings for DALL-E prompts
VISUAL_TYPE_STYLES = {
    "historical_photo": "vintage photograph, sepia or black and white, archival quality",
    "archival_footage": "historical documentary still, film grain, period authentic",
    "illustration": "detailed illustration, documentary style, historically accurate",
    "map": "historical map, vintage cartography, period-appropriate style",
    "portrait": "formal portrait, period-appropriate clothing and setting",
    "scene_recreation": "cinematic recreation, dramatic lighting, documentary quality",
    "symbolic": "symbolic imagery, metaphorical, artistic documentary style",
    "modern_footage": "modern documentary photography, journalistic style",
    "news_image": "photojournalistic style, documentary realism, contemporary",
    "historical_artwork": "period artwork style, historically accurate, museum quality",
}

# Motion style hints for different Ken Burns effects
MOTION_STYLE_HINTS = {
    "slow_zoom_in": "centered composition, subject fills frame, dramatic focus",
    "slow_zoom_out": "establishing shot, wide context, environmental detail",
    "pan_left": "horizontal composition, left-to-right visual narrative",
    "pan_right": "horizontal composition, right-to-left visual narrative",
    "pan_up": "vertical composition, ground to sky, uplifting perspective",
    "pan_down": "vertical composition, sky to ground, grounding perspective",
    "static": "balanced composition, contemplative, timeless quality",
}


def get_style_hints(visual_type: str, motion: str, era: str = None, location: str = None, mood: str = None) -> str:
    """
    Build style hints string from visual marker attributes.

    Args:
        visual_type: Type of visual (historical_photo, etc.)
        motion: Motion suggestion (slow_zoom_in, etc.)
        era: Historical era
        location: Location context
        mood: Emotional mood

    Returns:
        Formatted style hints string
    """
    hints = []

    # Add visual type style
    type_style = VISUAL_TYPE_STYLES.get(visual_type, "documentary photography")
    hints.append(type_style)

    # Add era if provided
    if era:
        hints.append(f"{era} era")

    # Add location if provided
    if location:
        hints.append(f"set in {location}")

    # Add mood if provided
    if mood:
        hints.append(f"{mood} mood")

    # Add motion-appropriate composition hint
    motion_hint = MOTION_STYLE_HINTS.get(motion, "")
    if motion_hint:
        hints.append(motion_hint)

    return ", ".join(hints)
