import os
import requests
from typing import Optional, List, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure QWEN_API_URL from environment, .env file, or Colab ngrok URL
QWEN_API_URL = os.getenv("QWEN_API_URL", "").rstrip("/")


def is_qwen_available() -> bool:
    """Check if remote Qwen Colab server is reachable."""
    if not QWEN_API_URL:
        return False
    try:
        r = requests.get(f"{QWEN_API_URL}/", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


import re

def parse_markdown_story(raw_text: str) -> tuple:
    """
    Parses title and story content from Qwen's output:
    Supports:
    - **Title**\n\nStory...
    - Title: Title\n\nStory...
    - # Title\n\nStory...
    """
    clean_text = raw_text.strip()
    
    # Check for **Title** at start
    m_bold = re.match(r"^\*\*(.+?)\*\*\s*\n+(.*)", clean_text, flags=re.DOTALL)
    if m_bold:
        return m_bold.group(1).strip(), m_bold.group(2).strip()

    # Check for Title: Title at start
    m_title = re.match(r"^Title:\s*(.+?)\s*\n+(.*)", clean_text, flags=re.DOTALL | re.IGNORECASE)
    if m_title:
        return m_title.group(1).strip(), m_title.group(2).strip()

    # Check for # Title at start
    m_hash = re.match(r"^#\s*(.+?)\s*\n+(.*)", clean_text, flags=re.DOTALL)
    if m_hash:
        return m_hash.group(1).strip(), m_hash.group(2).strip()

    # Fallback: first line if short (< 60 chars)
    lines = clean_text.splitlines()
    if len(lines) > 2 and len(lines[0].strip()) < 60 and not lines[0].strip().endswith('.'):
        return lines[0].strip().strip('*# '), "\n".join(lines[1:]).strip()

    return "A Special Story", clean_text


def generate_story_with_qwen(
    age: Optional[Any] = None,
    event: Optional[str] = None,
    goal: Optional[str] = None,
    character: Optional[str] = None,
    language: Optional[str] = "English"
) -> Dict[str, Any]:
    """
    Calls the Qwen3.5-9B Colab service (FastAPI or Chat endpoint).
    """
    if not QWEN_API_URL:
        raise ValueError("QWEN_API_URL environment variable is not configured.")
    
    # Parse age to integer if possible
    age_val = None
    if age is not None:
        try:
            age_val = int(str(age).split("-")[0].strip())
        except (ValueError, TypeError):
            age_val = None

    payload = {
        "age": age_val,
        "event": event,
        "goal": goal,
        "character": character,
        "language": language or "English"
    }
    
    try:
        response = requests.post(f"{QWEN_API_URL}/generate", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        story_content = data.get("story") or ""
        title = data.get("title")
        if not title:
            parsed_title, clean_story = parse_markdown_story(story_content)
            title = parsed_title
            story_content = clean_story
        return {
            "title": title or "A Special Story",
            "story": story_content,
            "engine": "Qwen3.5-9B (Colab)"
        }
    except Exception as e:
        # Fallback to chat completions endpoint if /generate is not present
        chat_prompt = (
            f"Create a bedtime story using these details:\n"
            f"Child age: {age or '4-8'}\n"
            f"Daily event: {event or 'A new experience'}\n"
            f"Story goal: {goal or 'Confidence and joy'}\n"
            f"Main character: {character or 'A friendly hero'}\n"
            f"Language: {language or 'English'}\n\n"
            f"The story should help the child explore the feeling of {event} and gradually develop {goal}."
        )
        chat_payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI children's story writer. Your task is to create meaningful, "
                        "age-appropriate stories based on a child's everyday experience. Provide a gentle and positive resolution."
                    )
                },
                {"role": "user", "content": chat_prompt}
            ]
        }
        response = requests.post(f"{QWEN_API_URL}/v1/chat/completions", json=chat_payload, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        title, story = parse_markdown_story(content)
        return {
            "title": title,
            "story": story,
            "engine": "Qwen3.5-9B (Colab)"
        }


def suggest_goals_with_qwen(
    age: Optional[Any] = None,
    event: Optional[str] = None,
    character: Optional[str] = None,
    language: Optional[str] = "English"
) -> List[str]:
    """
    Calls the Qwen3.5-9B Colab FastAPI /suggest-goals endpoint.
    """
    if not QWEN_API_URL:
        raise ValueError("QWEN_API_URL environment variable is not configured.")
    
    age_val = None
    if age is not None:
        try:
            age_val = int(str(age).split("-")[0].strip())
        except (ValueError, TypeError):
            age_val = None

    payload = {
        "age": age_val,
        "event": event,
        "character": character,
        "language": language or "English"
    }
    
    response = requests.post(f"{QWEN_API_URL}/suggest-goals", json=payload, timeout=30)
    response.raise_for_status()
    return response.json().get("suggestions", [])
