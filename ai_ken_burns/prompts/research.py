"""
Research prompts for AI Ken Burns.

Prompts for finding historical connections to current news.
"""

from ai_ken_burns.prompts.templates import PromptTemplate

# System prompt for historical connection analysis
HISTORICAL_CONNECTION_SYSTEM = PromptTemplate(
    """You are a historian specializing in labor history, class struggle, and social movements.
Your task is to find compelling historical parallels that illuminate the class dynamics of current events.

When analyzing a news story:
1. Identify the core class dynamics at play (workers vs capital, community vs corporations, etc.)
2. Find a specific historical event that parallels these dynamics
3. Focus on events from labor history, social movements, or class struggle
4. Explain why this historical parallel is illuminating and relevant

Preferred historical periods and movements:
- Industrial Revolution labor struggles (1800s)
- Progressive Era reforms (1890s-1920s)
- Great Depression and New Deal (1930s)
- Civil Rights Movement (1950s-1960s)
- Labor movements worldwide
- Anti-colonial and independence movements
- Housing and tenant rights movements
- Environmental justice movements

Always provide specific, verifiable historical events with dates and locations.""",
    name="historical_connection_system"
)

# User prompt for historical connection analysis
HISTORICAL_CONNECTION_USER = PromptTemplate(
    """Analyze this current news story and find a compelling historical parallel from labor history or class struggle:

NEWS STORY:
Title: ${title}

Summary: ${summary}

Source: ${source}
Identified Themes: ${themes}
Key Topics: ${keywords}

Find a specific historical event that:
1. Has similar class dynamics or power structures
2. Shows how ordinary people organized or responded
3. Provides lessons or context for understanding today's situation
4. Has compelling visual history (for documentary footage/images)

Respond with a JSON object containing the historical event details, thesis statement,
narrative angle, and confidence score (0-1).

Focus on events that are:
- Specific and verifiable (not vague movements)
- Have visual documentation available
- Show worker/community agency and resistance
- Provide hope or lessons for today""",
    name="historical_connection_user"
)

# JSON schema for historical connection response
HISTORICAL_CONNECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "historical_event": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the historical event"},
                "year": {"type": "integer", "description": "Year the event occurred"},
                "year_range": {"type": "string", "description": "Year range if spans multiple years"},
                "location": {"type": "string", "description": "Where the event took place"},
                "summary": {"type": "string", "description": "Brief summary of the event (2-3 sentences)"},
                "significance": {"type": "string", "description": "Why this event matters for class consciousness"},
                "connection_rationale": {"type": "string", "description": "How this connects to the current news story"},
                "parallel_themes": {"type": "array", "items": {"type": "string"}, "description": "Themes shared with current story"},
                "key_figures": {"type": "array", "items": {"type": "string"}, "description": "Important people involved"},
                "key_facts": {"type": "array", "items": {"type": "string"}, "description": "Important facts to mention"},
                "suggested_imagery": {"type": "array", "items": {"type": "string"}, "description": "Historical images to search for"}
            },
            "required": ["name", "summary", "connection_rationale"]
        },
        "thesis": {"type": "string", "description": "Central thesis connecting news to history"},
        "narrative_angle": {"type": "string", "description": "Suggested narrative approach"},
        "confidence_score": {"type": "number", "description": "Confidence in the connection (0-1)"}
    },
    "required": ["historical_event", "thesis", "narrative_angle", "confidence_score"]
}
