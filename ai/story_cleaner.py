"""Simple and safe story cleaner for StoryApp.

The cleaner should NOT control story length.
The Qwen worker controls length.

This file only:
- removes Qwen thinking tags
- extracts one title
- removes Title / Story labels
- removes placeholders
- removes exact duplicate paragraphs
- removes unfinished final fragments
- preserves the generated story as much as possible
"""

import re
from typing import Tuple, List, Optional


# ============================================================
# REMOVE QWEN THINKING
# ============================================================

def strip_thinking_tags(text: str) -> str:
    """Remove <think>...</think> blocks."""

    if not text:
        return ""

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove unfinished thinking block
    text = re.sub(
        r"<think>.*$",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return text.strip()


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_for_comparison(text: str) -> str:
    """Normalize text for simple exact comparison."""

    return re.sub(
        r"[^a-z0-9]",
        "",
        (text or "").lower(),
    )


# ============================================================
# CHARACTER PLACEHOLDERS
# ============================================================

def replace_character_placeholders(
    text: str,
    character_name: Optional[str],
) -> str:
    """Replace obvious placeholder character text."""

    if not text:
        return ""

    if (
        character_name
        and character_name.strip()
        and character_name.strip().lower()
        not in {
            "my child",
            "the child",
            "none",
            "explorer",
        }
    ):
        character = character_name.strip()

    else:
        character = "the little hero"

    # [Character], [Hero], [Name], etc.
    text = re.sub(
        r"\[(?:character|hero|name|child|protagonist)\]",
        character,
        text,
        flags=re.IGNORECASE,
    )

    # Other common placeholders
    text = re.sub(
        r"\[(?:your\s+)?(?:character|hero|name)[^\]]*\]",
        character,
        text,
        flags=re.IGNORECASE,
    )

    # "my child" should not leak into fictional story
    text = re.sub(
        r"\b(?:my|our)\s+child\b",
        character,
        text,
        flags=re.IGNORECASE,
    )

    return text


# ============================================================
# TITLE CLEANING
# ============================================================

def clean_title_candidate(
    text: str,
) -> Optional[str]:
    """Return a usable title or None."""

    if not text:
        return None

    cleaned = text.strip()

    # Remove markdown decoration
    cleaned = cleaned.strip(
        "*#_\"' "
    )

    # Remove Title:
    cleaned = re.sub(
        r"^title\s*:\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = cleaned.strip(
        "*#_\"' "
    )

    if not cleaned:
        return None

    lower = cleaned.lower()

    # Reject generic labels/placeholders
    invalid = {
        "title",
        "title:",
        "story",
        "story:",
        "your creative title",
        "creative title",
        "story title",
        "your title",
    }

    if lower in invalid:
        return None

    if any(
        placeholder in lower
        for placeholder in [
            "[character]",
            "[hero]",
            "[name]",
            "your creative title",
            "story title",
        ]
    ):
        return None

    # Title should remain reasonably short
    if len(cleaned) > 100:
        return None

    return cleaned


# ============================================================
# FIND TITLE
# ============================================================

def _find_title(
    lines: List[str],
    fallback_title: str,
) -> str:
    """Find title from the first few generated lines."""

    # First prefer explicit Title:
    for line in lines[:8]:

        stripped = line.strip()

        if not stripped:
            continue

        working = stripped

        working = re.sub(
            r"^#{1,6}\s*",
            "",
            working,
        )

        working = working.strip("* ")

        match = re.match(
            r"^title\s*:\s*(.+)$",
            working,
            flags=re.IGNORECASE,
        )

        if match:

            candidate = clean_title_candidate(
                match.group(1)
            )

            if candidate:
                return candidate

    # Then accept a short markdown heading
    for line in lines[:5]:

        stripped = line.strip()

        if not stripped:
            continue

        heading = re.match(
            r"^#{1,6}\s+(.+)$",
            stripped,
        )

        if heading:

            candidate = clean_title_candidate(
                heading.group(1)
            )

            if candidate:
                return candidate

        bold = re.match(
            r"^\*{2}(.+?)\*{2}$",
            stripped,
        )

        if bold:

            candidate = clean_title_candidate(
                bold.group(1)
            )

            if candidate:
                return candidate

    return fallback_title


# ============================================================
# REMOVE UNFINISHED FINAL FRAGMENT
# ============================================================

def _clean_final_paragraph(
    paragraph: str,
) -> str:
    """Remove only a genuinely unfinished final fragment."""

    paragraph = (
        paragraph
        or ""
    ).strip()

    if not paragraph:
        return ""

    # Already ends normally
    if re.search(
        r'[.!?]["”’\']?\s*$',
        paragraph,
    ):
        return paragraph

    # Find last complete sentence
    last_complete = max(
        paragraph.rfind("."),
        paragraph.rfind("?"),
        paragraph.rfind("!"),
    )

    if last_complete >= 20:

        return paragraph[
            :last_complete + 1
        ].strip()

    # Entire paragraph appears unfinished
    return ""


# ============================================================
# MAIN CLEANER
# ============================================================

def extract_title_and_content(
    raw_story: str,
    default_title: Optional[str] = None,
    character_name: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Extract title and story body while preserving as much
    generated content as possible.
    """

    fallback_title = (
        default_title
        or "A Gentle Bedtime Adventure"
    )

    raw = strip_thinking_tags(
        raw_story or ""
    )

    if not raw.strip():
        return fallback_title, ""

    raw = (
        raw
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    raw = replace_character_placeholders(
        raw,
        character_name,
    )

    # Remove obvious title placeholders
    raw = re.sub(
        r"\[(?:your\s+)?creative\s+title\]",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    raw = re.sub(
        r"\[story\s+title\]",
        "",
        raw,
        flags=re.IGNORECASE,
    )

    lines = raw.split("\n")

    title = _find_title(
        lines,
        fallback_title,
    )

    normalized_title = (
        normalize_for_comparison(
            title
        )
    )

    body_lines: List[str] = []


    # ========================================================
    # REMOVE TITLE / STORY LABELS
    # ========================================================

    for line in lines:

        stripped = line.strip()

        if not stripped:

            body_lines.append("")
            continue

        lower = stripped.lower()

        # Standalone labels
        if lower in {
            "title",
            "title:",
            "story",
            "story:",
            "**title**",
            "**title:**",
            "**story**",
            "**story:**",
            "# title",
            "# story",
        }:
            continue

        # Generic markdown label
        if re.fullmatch(
            r"[*#_\s]*(title|story)\s*:?\s*[*#_\s]*",
            stripped,
            flags=re.IGNORECASE,
        ):
            continue

        # Explicit Title: Something
        title_match = re.match(
            r"^\s*(?:#{1,6}\s*)?"
            r"(?:\*{1,3}\s*)?"
            r"title\s*:\s*(.+?)"
            r"(?:\*{1,3})?\s*$",
            stripped,
            flags=re.IGNORECASE,
        )

        if title_match:
            continue

        # Remove Story: prefix but keep text after it
        story_match = re.match(
            r"^\s*(?:\*{0,2})"
            r"story\s*:\s*"
            r"(.*)$",
            stripped,
            flags=re.IGNORECASE,
        )

        if story_match:

            remainder = (
                story_match
                .group(1)
                .strip()
            )

            if remainder:
                body_lines.append(
                    remainder
                )

            continue

        # Remove repeated title line
        normalized_line = (
            normalize_for_comparison(
                stripped
            )
        )

        if (
            normalized_title
            and normalized_line
            == normalized_title
        ):
            continue

        # Remove simple markdown heading that equals title
        heading_match = re.match(
            r"^#{1,6}\s+(.+)$",
            stripped,
        )

        if heading_match:

            candidate = (
                normalize_for_comparison(
                    heading_match.group(1)
                )
            )

            if (
                candidate
                == normalized_title
            ):
                continue

        # Remove notices
        if stripped.startswith(
            "[FALLBACK"
        ):
            continue

        if stripped.startswith(
            "Notice:"
        ):
            continue

        body_lines.append(
            line
        )


    # ========================================================
    # CREATE PARAGRAPHS
    # ========================================================

    body_text = "\n".join(
        body_lines
    ).strip()

    raw_paragraphs = re.split(
        r"\n\s*\n+",
        body_text,
    )

    cleaned_paragraphs: List[str] = []

    seen_exact = set()


    for paragraph in raw_paragraphs:

        paragraph = (
            paragraph
            .strip()
        )

        if not paragraph:
            continue

        paragraph = (
            replace_character_placeholders(
                paragraph,
                character_name,
            )
        )

        # Remove markdown emphasis only
        paragraph = (
            paragraph
            .replace("**", "")
            .replace("__", "")
        )

        paragraph = re.sub(
            r"\[(?:your\s+)?creative\s+title\]",
            "",
            paragraph,
            flags=re.IGNORECASE,
        )

        paragraph = re.sub(
            r"\[story\s+title\]",
            "",
            paragraph,
            flags=re.IGNORECASE,
        )

        paragraph = (
            paragraph.strip()
        )

        if not paragraph:
            continue


        # ----------------------------------------------------
        # ONLY EXACT DUPLICATE PARAGRAPHS
        # ----------------------------------------------------

        normalized = (
            normalize_for_comparison(
                paragraph
            )
        )

        if not normalized:
            continue

        if normalized in seen_exact:
            continue

        seen_exact.add(
            normalized
        )

        cleaned_paragraphs.append(
            paragraph
        )


    # ========================================================
    # FINAL INCOMPLETE FRAGMENT
    # ========================================================

    if cleaned_paragraphs:

        cleaned_last = (
            _clean_final_paragraph(
                cleaned_paragraphs[-1]
            )
        )

        if cleaned_last:

            cleaned_paragraphs[-1] = (
                cleaned_last
            )

        else:

            cleaned_paragraphs.pop()


    # ========================================================
    # FINAL BODY
    # ========================================================

    clean_content = "\n\n".join(
        cleaned_paragraphs
    ).strip()


    # Safe fallback:
    # if cleaning unexpectedly removed everything,
    # return the body instead of destroying the story.
    if not clean_content:

        clean_content = (
            body_text.strip()
        )


    return (
        title,
        clean_content,
    )