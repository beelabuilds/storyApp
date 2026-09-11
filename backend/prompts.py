AGE_GUIDELINES_TABLE = {
    4: {"length": "300–400 words", "time": "3–5 min", "desc": "Very simple, sensory, comforting language, gentle repetition, short sentences, and a warm resolution."},
    5: {"length": "350–500 words", "time": "4–6 min", "desc": "Simple, lively vocabulary, natural dialogue, relatable daily problem, and reassuring resolution."},
    6: {"length": "450–600 words", "time": "5–7 min", "desc": "Engaging vocabulary, small adventures, dialogue with friends, and active problem-solving."},
    7: {"length": "550–700 words", "time": "6–8 min", "desc": "Richer vocabulary, connected scenes, emotional growth, and thoughtful choices."},
    8: {"length": "650–850 words", "time": "7–10 min", "desc": "Detailed chapter-style storytelling, rich character depth, dialogue, and satisfying earned resolution."}
}

SYSTEM_PROMPT = """
You are an AI children's story writer.

Your task is to create meaningful, age-appropriate stories
based on a child's everyday experience.

The story should:
- Reflect the emotional situation in the provided event.
- Help the child explore the selected story goal through the story.
- Strictly adhere to the recommended word count and reading time for the child's exact age:
  * Age 4: 300–400 words (3–5 min read)
  * Age 5: 350–500 words (4–6 min read)
  * Age 6: 450–600 words (5–7 min read)
  * Age 7: 550–700 words (6–8 min read)
  * Age 8: 650–850 words (7–10 min read)
- KEEP PARAGRAPHS SHORT AND AIRY: Use short paragraphs (2–3 sentences each) with blank lines between them so children stay engaged and never feel overwhelmed or bored.
- Use age-appropriate vocabulary, sentence length, and narrative complexity.
- Have a clear beginning, middle, and ending.
- Show emotions through the character's experiences, dialogue, and actions.
- Provide a gentle, earned, and positive resolution.
- Be enjoyable and engaging when read aloud by a parent.
- Avoid frightening, violent, traumatic, or inappropriate content.
- Avoid directly giving psychological or medical advice.
- Avoid forcing an obvious moral or lesson.

Format:
**Title**

[Story content with short, readable paragraphs]
"""

def get_age_specs(age_input):
    age_str = str(age_input or "").strip().lower()
    for num in [4, 5, 6, 7, 8]:
        if str(num) in age_str and "4-5" not in age_str and "6-8" not in age_str and "4-8" not in age_str:
            return AGE_GUIDELINES_TABLE[num]

    if "4-5" in age_str or "4–5" in age_str:
        return {"length": "300–500 words", "time": "3–6 min", "desc": "Simple, sensory, comforting language with natural dialogue in short paragraphs."}
    elif "6-8" in age_str or "6–8" in age_str:
        return {"length": "500–800 words", "time": "5–9 min", "desc": "Richer vocabulary, dialogue between characters, character growth, broken into short readable paragraphs."}
    else:
        return {"length": "400–650 words", "time": "4–7 min", "desc": "Engaging, age-appropriate storytelling with dialogue and gentle resolution in short paragraphs."}


def build_story_prompt(event, age, goal, character, language="English", story_seed=None):
    specs = get_age_specs(age)
    
    return f"""Create a children's story using these details:

Child age: {age or '4-8'}
Target length: {specs['length']} (approx. reading time: {specs['time']})
Writing style guidance: {specs['desc']}
Daily event: {event or 'A new everyday adventure'}
Story goal: {goal or 'Confidence and courage'}
Main character: {character or 'A friendly hero'}
Language: {language or 'English'}
Story seed: {story_seed or 'unique-story'}

Formatting Rules:
- Keep paragraphs SHORT (2–3 sentences max per paragraph). Separate paragraphs with a blank line.
- Use natural dialogue on its own lines to make the story lively and fun to read aloud.
- Ensure the overall story meets the target length of {specs['length']}.

Format:
**Title**

[Story content with short paragraphs]
"""