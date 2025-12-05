"""
Script generation prompts for AI Ken Burns.

Prompts for generating documentary narration scripts with visual markers.
"""

from ai_ken_burns.prompts.templates import PromptTemplate

# System prompt for script generation
SCRIPT_GENERATION_SYSTEM = PromptTemplate(
    """You are a documentary scriptwriter specializing in connecting current events to historical class struggles.

Your task is to write compelling narration scripts that:
1. Open with a very brief, hard hitting summary of today's news story.  Make it hook the users with exaggerated drama and urgency.
2. Transition to the historical parallel quickly, explaining the context and significance.
3. Draw meaningful connections between past and present.
4. End with insight or call to reflection.
Be brief, radical, and desperate to explain class conciousness.
Use a tone that is engaging, thought-provoking, and accessible to a general audience.
Use the speaking style of Malcom X and Fred Hampton.

IMPORTANT: Embed visual markers in your script using [v1], [v2], etc. format.
Each marker indicates where a new image should appear in the video.

Guidelines for visual markers:
- Place markers at natural transition points
- Each marker should have 5-15 seconds of narration
- Use markers to highlight key moments, people, and events
- Suggest what type of image should appear

Your response must be valid JSON with the structure specified.""",
    name="script_generation_system"
)

# User prompt for script generation
SCRIPT_GENERATION_USER = PromptTemplate(
    """Write a documentary narration script connecting this news story to its historical parallel.

${research_context}

REQUIREMENTS:
- Target duration: approximately ${target_duration} seconds (${target_words} words)
- Include ${marker_count_min}-${marker_count_max} visual markers [v1], [v2], etc.
- Style: ${style}
- Structure: 3-5 segments (intro, news context, historical parallel, connection, conclusion)

VISUAL MARKER PLACEMENT:
- Place [v1] near the opening to show contemporary context
- Place markers at each major transition
- Include markers for key historical figures and events
- End with a reflective visual

The script should flow naturally when read aloud. Make it compelling and thought-provoking.

Respond with a JSON object following this schema:
${response_schema}""",
    name="script_generation_user"
)

# Response schema for script generation (as string for inclusion in prompts)
SCRIPT_RESPONSE_SCHEMA = """
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

# Prompt for enhancing visual marker search terms
SEARCH_TERMS_ENHANCEMENT = PromptTemplate(
    """Generate 5 specific image search terms for this visual:

Description: ${description}
Type: ${visual_type}
Era: ${era}
Location: ${location}

Return only a JSON array of search terms, e.g.: ["term1", "term2", "term3", "term4", "term5"]""",
    name="search_terms_enhancement"
)
