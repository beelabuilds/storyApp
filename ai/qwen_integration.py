import os
import requests
from pathlib import Path
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    # Load from backend/.env or root .env
    backend_env = Path(__file__).resolve().parent.parent / "backend" / ".env"
    root_env = Path(__file__).resolve().parent.parent / ".env"
    if backend_env.exists():
        load_dotenv(backend_env)
    elif root_env.exists():
        load_dotenv(root_env)
    else:
        load_dotenv()
except ImportError:
    pass


def get_qwen_api_url() -> str:
    """Get the currently configured Qwen API base URL."""
    return os.getenv("QWEN_API_URL", "").strip().rstrip("/")


def is_qwen_available() -> bool:
    """Check whether the Colab Qwen API is reachable."""
    api_url = get_qwen_api_url()
    if not api_url:
        return False

    try:
        response = requests.get(
            f"{api_url}/health",
            timeout=5
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def generate_story_with_qwen(description: str) -> Dict[str, Any]:
    """
    Send the parent's natural-language description to the
    Qwen3.5-9B story generator running on Colab.
    """
    api_url = get_qwen_api_url()

    if not api_url:
        raise ValueError(
            "QWEN_API_URL environment variable is not configured."
        )

    if not description or not description.strip():
        raise ValueError("Story description cannot be empty.")

    response = requests.post(
        f"{api_url}/generate-story",
        json={
            "description": description.strip()
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return {
        "story": data.get("story", ""),
        "engine": "Qwen3.5-9B (Colab)"
    }