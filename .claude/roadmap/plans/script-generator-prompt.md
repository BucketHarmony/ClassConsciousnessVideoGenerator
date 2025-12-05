# Script Generator - GPT-4 Narrative Prompt Design

## Purpose
Transform news story + historical connection into a compelling 2-4 minute narrative script for video narration. The script should educate viewers on class dynamics while being engaging and actionable.

## Target Specifications
- **Length**: 400-600 words (approximately 2-4 minutes at 150 words/minute speaking rate)
- **Tone**: Urgent, educational, empowering (not preachy or cynical)
- **Structure**: 6 sections with clear narrative arc
- **Audience**: General public interested in politics/economics/labor issues
- **Format**: Plain text with section markers (no markdown formatting in final narration)

## Prompt Template

```
You are a documentary scriptwriter specializing in class consciousness education. Write a compelling 2-4 minute video narration script that connects a current news event to a historical parallel in class struggle.

RESEARCH MATERIAL:

Current News:
- Headline: {news_headline}
- Summary: {news_summary}
- Date: {news_date}
- Source: {news_source}

Historical Connection:
- Event: {historical_event_name}
- Year: {historical_year}
- Location: {historical_location}
- Description: {historical_description}
- Key Figures: {key_figures}
- Outcome: {historical_outcome}

Thematic Connection:
- Theme: {connection_theme}
- Parallels: {parallels_list}
- Contrast: {contrast}
- Lesson: {educational_lesson}

SCRIPT STRUCTURE (6 Sections):

1. HOOK (50-80 words)
   - Start with the current news event
   - Frame it in terms of class dynamics or power
   - Create urgency or curiosity
   - Example: "This week, Amazon workers in Alabama made headlines..."

2. NEWS CONTEXT (80-120 words)
   - Expand on the current situation
   - Explain who benefits and who loses
   - Identify the class dynamic at play
   - Make it concrete and relatable
   - Example: "For decades, Amazon has fought unionization..."

3. HISTORICAL EVENT (100-150 words)
   - Transport viewer to the historical moment
   - Paint vivid picture of what happened
   - Include specific names, dates, locations
   - Show the human stakes
   - Example: "In 1894, workers at the Pullman Company faced similar..."

4. CONNECTION (80-120 words)
   - Explicitly draw parallels between past and present
   - Highlight patterns in how power operates
   - Show that these dynamics are not accidents but systems
   - Example: "The tactics Pullman used mirror what we see today..."

5. MODERN RELEVANCE (60-100 words)
   - What does this history teach us about today?
   - Why does this pattern persist?
   - What's at stake now?
   - Example: "Understanding this history reveals that..."

6. CALL TO ACTION (30-50 words)
   - What can viewers do with this knowledge?
   - Concrete, accessible action (not overwhelming)
   - Empowering, not defeatist
   - Example: "When you see news about labor organizing, remember..."

WRITING GUIDELINES:

VOICE & TONE:
- Active voice, strong verbs
- Direct address ("you see", "we know", "they want")
- Confident and clear, not academic or jargon-heavy
- Emotionally resonant but not melodramatic
- Serious but not humorless

LANGUAGE:
- Short sentences mixed with medium sentences (avoid long, complex sentences for narration)
- Concrete nouns, specific details (not "workers" but "Amazon warehouse workers")
- Accessible vocabulary (explain jargon if needed: "union-busting - using legal and PR tactics to prevent unionization")
- Rhythm and pacing (varies sentence length for dynamic narration)

AVOID:
- Passive voice ("was done" → "they did")
- Vague statements ("some people think")
- Both-sides framing ("some say X, others say Y")
- Cynicism or hopelessness
- Jargon without explanation
- Over-simplification (acknowledge complexity while staying clear)

WORD COUNT: Target 400-600 words total. Aim for middle (500 words) for optimal pacing.

OUTPUT FORMAT:

[SECTION: HOOK]
{Hook text here}

[SECTION: NEWS_CONTEXT]
{News context text here}

[SECTION: HISTORICAL_EVENT]
{Historical event text here}

[SECTION: CONNECTION]
{Connection text here}

[SECTION: MODERN_RELEVANCE]
{Modern relevance text here}

[SECTION: CALL_TO_ACTION]
{Call to action text here}

[METADATA]
Word Count: {exact_count}
Estimated Duration: {minutes}:{seconds}
Tone: {urgent/educational/empowering}

---

Now write the script based on the research material provided above.
```

## Example Output Structure

```
[SECTION: HOOK]
This week, Amazon warehouse workers in Bessemer, Alabama voted on whether to form a union. The company spent millions fighting them. This isn't new. It's a script written over a century ago.

[SECTION: NEWS_CONTEXT]
Amazon is one of the world's most valuable companies, worth over a trillion dollars. Jeff Bezos, its founder, is one of the richest people in history. Yet warehouse workers describe brutal conditions: impossible quotas, injuries, surveillance, poverty wages. When workers tried to organize, Amazon hired union-busting consultants, held mandatory anti-union meetings, and flooded the workplace with anti-union propaganda. The message was clear: we own this place, and we decide how it runs.

[SECTION: HISTORICAL_EVENT]
In 1894, workers at the Pullman Company near Chicago faced the same fight. George Pullman owned everything: the factory, the housing, the stores. Workers lived in his town, bought from his shops, and had no voice. When Pullman cut wages but kept rents high during an economic depression, workers struck. Pullman hired strikebreakers and got federal troops to crush the strike violently. Eugene Debs, the labor leader, was jailed. The strike was broken.

[SECTION: CONNECTION]
The tactics Pullman used are Amazon's playbook today. Control the workplace. Flood workers with propaganda. Use legal and government pressure. Frame organizing as outside agitation. Pullman called strikers ungrateful. Amazon calls organizers troublemakers. Both companies had immense wealth and power. Both fought unionization as an existential threat to their control.

[SECTION: MODERN_RELEVANCE]
Understanding this history reveals that corporate resistance to worker power isn't a bug, it's the system working as designed. When workers organize, they shift the balance of power. That's why companies fight so hard. The Pullman Strike failed, but it sparked a movement that eventually won the eight-hour day, workplace safety laws, and the weekend. Today's fights are part of that same long struggle.

[SECTION: CALL_TO_ACTION]
When you see news about labor organizing, remember it's not just about one workplace. It's about whether workers have a voice in an economy that concentrates power at the top. History doesn't repeat, but it rhymes. And this time, we get to write a different ending.

[METADATA]
Word Count: 487
Estimated Duration: 3:15
Tone: urgent/educational/empowering
```

## Validation Checks

After generating script, validate:

1. **Word count**: 400 ≤ word_count ≤ 600
2. **Section count**: Exactly 6 sections
3. **Section markers**: All sections properly tagged
4. **No markdown**: No **, *, #, etc. in narration text
5. **Readability**: Flesch reading ease score ≥ 60 (8th grade level)
6. **Tone check**: No defeatist language, no both-sidesism
7. **Specificity**: Includes specific names, dates, places from research

## Quality Metrics

Rate generated scripts on:
- **Engagement** (1-10): Does it hook the viewer?
- **Clarity** (1-10): Is the narrative easy to follow?
- **Accuracy** (1-10): Does it faithfully represent the research?
- **Actionability** (1-10): Does it empower viewers?

Target: All metrics ≥ 7

## Testing

Generate scripts for these test cases:
1. Labor union vote
2. Antitrust regulation debate
3. Wealth inequality report
4. Tech worker organizing
5. Minimum wage legislation

Manually review each for quality before approving prompt.
