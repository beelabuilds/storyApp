import os
import re
import sys
from typing import Tuple

# Make project root importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from ai.qwen_integration import (
    generate_story_with_qwen,
    is_qwen_available,
)



def extract_title_and_content(raw_story: str) -> Tuple[str, str]:
    """Parse out title and clean body from generated markdown story."""
    raw = (raw_story or "").strip()
    if not raw:
        return "A New Adventure", ""

    lines = raw.split("\n")
    first_non_empty_idx = -1
    for i, line in enumerate(lines):
        if line.strip():
            first_non_empty_idx = i
            break

    if first_non_empty_idx == -1:
        return "A New Adventure", raw

    first_line = lines[first_non_empty_idx].strip()

    # Match **Title: ...**, **Title**, or # Title
    match = re.match(r"^(\*{1,2}|#{1,6})?\s*(?:Title\s*:?\s*)?(.*?)\1?$", first_line, re.IGNORECASE)
    if match and len(first_line) < 140:
        extracted = match.group(2).strip().strip("*#_ ")
        if extracted and not extracted.endswith("."):
            remaining = "\n".join(lines[first_non_empty_idx + 1:]).strip()
            if remaining:
                return extracted, remaining

    return "A New Adventure", raw


def generate_story(description: str) -> dict:
    """
    Generate a children's story from the parent's natural description.

    The actual prompt and story reasoning are handled by
    Qwen3.5-9B in the Colab notebook.
    """

    if not description or not description.strip():
        raise ValueError("Story description cannot be empty.")

    if not is_qwen_available():
        raise RuntimeError(
            "Qwen AI service is currently unavailable. "
            "Make sure the Colab notebook and ngrok tunnel are running."
        )

    result = generate_story_with_qwen(description)
    raw_story = result.get("story", "")
    title, content = extract_title_and_content(raw_story)

    return {
        "title": title,
        "content": content,
        "story": raw_story,
        "engine": result.get("engine", "Qwen3.5-9B (Colab)")
    }