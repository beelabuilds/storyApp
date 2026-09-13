import random
"""Backend story generation orchestrator.

Coordinates prompt description processing, calls the Qwen worker process via IPC,
and extracts clean title and content for the frontend.
"""

import os
import sys
from typing import Dict, Any, Optional

# Ensure project root is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai.story_cleaner import extract_title_and_content
from ai.qwen_integration import (
    generate_story_with_qwen,
    is_qwen_available,
)

def resolve_fictional_character(hero: Optional[str], description: str) -> str:
    """Choose a friendly fictional character dynamically for each story."""

    cleaned_hero = (hero or "").strip()

    generic_names = {
        "", "none", "my child", "our child", "the child", "child",
        "a friendly explorer", "friendly explorer", "explorer",
        "an explorer", "someone", "a hero", "hero", "main character",
        "a character", "character", "kid", "little one", "boy", "girl"
    }

    # If the parent explicitly gives a specific character, keep it.
    if (
        cleaned_hero
        and cleaned_hero.lower() not in generic_names
        and not cleaned_hero.startswith("[")
    ):
        return cleaned_hero

    desc_lower = (description or "").lower()

    # If the parent explicitly asks for a type of animal/character,
    # choose a suitable named version dynamically.
    if "dragon" in desc_lower:
        return random.choice([
            "Luna the Little Star-Dragon",
            "Ember the Gentle Dragon",
            "Nova the Tiny Moon-Dragon",
        ])

    if "puppy" in desc_lower or "dog" in desc_lower:
        return random.choice([
            "Biscuit the Playful Puppy",
            "Milo the Gentle Puppy",
            "Toby the Curious Little Dog",
        ])

    if "cat" in desc_lower or "kitten" in desc_lower:
        return random.choice([
            "Milo the Whiskered Kitten",
            "Coco the Curious Kitten",
            "Lily the Gentle Little Cat",
        ])

    if "bunny" in desc_lower or "rabbit" in desc_lower:
        return random.choice([
            "Bella the Little Bunny",
            "Rosie the Gentle Rabbit",
            "Poppy the Curious Bunny",
        ])

    if "bear" in desc_lower:
        return random.choice([
            "Teddy the Little Bear",
            "Benny the Gentle Bear",
            "Maple the Cozy Little Bear",
        ])

    if "owl" in desc_lower:
        return random.choice([
            "Oliver the Wise Little Owl",
            "Ollie the Gentle Owl",
            "Pippa the Moonlit Owl",
        ])

    if "mouse" in desc_lower:
        return random.choice([
            "Pip the Curious Mouse",
            "Mimi the Brave Little Mouse",
            "Nibbles the Gentle Mouse",
        ])

    # Bedtime, darkness, fears, sleeping alone
    if any(
        word in desc_lower
        for word in [
            "dark", "noise", "sound", "night", "shadow",
            "bed", "scared", "fear", "sleep", "alone"
        ]
    ):
        return random.choice([
            "Maple the Little Bear",
            "Lumi the Gentle Bunny",
            "Ollie the Sleepy Owl",
            "Pip the Tiny Mouse",
            "Milo the Moonlight Kitten",
            "Toby the Brave Little Puppy",
        ])

    # Courage / trying something new
    if any(
        word in desc_lower
        for word in [
            "brave", "courage", "try", "new",
            "nervous", "first day", "doctor"
        ]
    ):
        return random.choice([
            "Pip the Brave Little Mouse",
            "Finn the Curious Fox",
            "Luna the Little Rabbit",
            "Theo the Gentle Turtle",
        ])

    # Friendship / kindness / school
    if any(
        word in desc_lower
        for word in [
            "friend", "share", "kind", "play",
            "school", "preschool", "turn", "gentle"
        ]
    ):
        return random.choice([
            "Finley the Friendly Fox",
            "Rosie the Helpful Rabbit",
            "Milo the Kind Little Bear",
            "Tilly the Cheerful Turtle",
        ])

    # Fantasy / adventure
    if any(
        word in desc_lower
        for word in [
            "magic", "fly", "space", "star",
            "adventure", "forest"
        ]
    ):
        return random.choice([
            "Luna the Little Star-Dragon",
            "Nova the Moon Fox",
            "Poppy the Forest Fairy",
            "Theo the Tiny Explorer",
        ])

    # General stories
    return random.choice([
        "Oliver the Gentle Little Owl",
        "Lumi the Curious Bunny",
        "Theo the Friendly Turtle",
        "Milo the Little Fox",
        "Pippa the Playful Puppy",
        "Coco the Curious Kitten",
    ])


async def generate_story(
    description: str,
    age: Optional[str] = None,
    hero: Optional[str] = None,
    feedback_prompt: Optional[str] = None,
    max_tokens: int = 650,
) -> Dict[str, Any]:
    """Generate a children's story from the parent's natural description.

    Dispatches to the local Qwen worker process via IPC.
    """
    if not description or not description.strip():
        raise ValueError("Story description cannot be empty.")

    if not is_qwen_available():
        raise RuntimeError(
            "Local Qwen worker process is not running. "
            "Please ensure the application was started properly."
        )

    # Resolve real fictional character (never placeholder or 'my child')
    resolved_hero = resolve_fictional_character(hero, description)

    result = await generate_story_with_qwen(
        description=description,
        age=age,
        hero=resolved_hero,
        feedback_prompt=feedback_prompt,
        max_tokens=max_tokens,
    )
    raw_story = result.get("story", "")

    # Clean default title anchored around the real character
    desc_lower = description.lower()
    if any(w in desc_lower for w in ["dark", "sound", "noise", "night", "fear", "scared", "bedroom", "bed"]):
        default_title = f"{resolved_hero} and the Whispering Night"
    elif any(w in desc_lower for w in ["kind", "friend", "share"]):
        default_title = f"{resolved_hero}'s Kind Little Secret"
    elif any(w in desc_lower for w in ["brave", "courage", "confidence"]):
        default_title = f"{resolved_hero}'s Brave Little Step"
    else:
        default_title = f"{resolved_hero}'s Cozy Adventure"

    title, content = extract_title_and_content(
        raw_story,
        default_title=default_title,
        character_name=resolved_hero,
    )

    return {
        "title": title,
        "content": content,
        "story": content,
        "character": resolved_hero,
        "hero": resolved_hero,
        "raw": result.get("raw", raw_story),
        "engine": result.get("engine", "Qwen Local GGUF"),
        "is_fallback": result.get("is_fallback", False),
    }