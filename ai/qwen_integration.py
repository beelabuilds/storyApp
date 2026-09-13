"""Internal IPC integration module connecting story generation to the Qwen worker process.

Replaces the previous HTTP/ngrok client with direct in-memory multiprocessing IPC.
"""

from typing import Dict, Any, Optional
from ai.qwen_ipc import qwen_manager


def is_qwen_available() -> bool:
    """Check whether the internal Qwen worker process is active."""
    return qwen_manager.is_alive()


async def generate_story_with_qwen(
    description: str,
    age: Optional[str] = None,
    hero: Optional[str] = None,
    feedback_prompt: Optional[str] = None,
    max_tokens: int = 650,
) -> Dict[str, Any]:
    """Generate a story by dispatching parameters to the local Qwen worker via IPC."""
    if not description or not description.strip():
        raise ValueError("Story description cannot be empty.")

    result = await qwen_manager.generate_story(
        description=description.strip(),
        age=age,
        hero=hero,
        feedback_prompt=feedback_prompt,
        max_tokens=max_tokens,
    )

    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error during story generation.")
        raise RuntimeError(error_msg)

    return {
        "story": result.get("story", ""),
        "raw": result.get("raw", ""),
        "engine": result.get("engine", "Qwen Local GGUF"),
        "is_fallback": result.get("is_fallback", False),
    }