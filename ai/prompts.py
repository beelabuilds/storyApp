"""Story prompts for StoryApp.

This file controls:
- storytelling quality
- age-appropriate language
- character consistency
- emotional safety
- parent feedback style preferences

IMPORTANT:
Story LENGTH is NOT controlled here.
Length is controlled only by qwen_worker.py.
"""

from typing import Optional


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a kind, imaginative storyteller for children aged 4 to 8.

Your job is to turn a parent's description into a warm,
meaningful children's story.

Understand:
- what happened
- how the child may feel
- what the child may need
- what positive change the parent hopes for

Create a fictional story that gently helps with that experience.

STORY RULES:

- Use simple, natural, child-friendly language.
- Use short and clear sentences.
- Divide the story into clear paragraphs with a blank line between paragraphs
- Make the story imaginative and enjoyable.
- Use fictional characters, animals, magical creatures,
  or other friendly story characters.
- Never call the main character "my child",
  "the child", "[Character]", "[Hero]", or similar placeholders.
- Keep the same main character throughout the story.
- Show feelings through actions and events instead of lecturing.
- Let the character gradually make progress.
- Do not solve the problem instantly.
- Include a clear beginning, middle, and ending.
- The final part must clearly resolve the story.
- End with the character feeling safe, hopeful,
  calm, happy, confident, or proud when appropriate.

SAFETY RULES:

- Do not shame or blame the child.
- Do not frighten the child unnecessarily.
- Do not diagnose the child.
- Do not give medical advice.
- Do not include harmful, sexual, graphic,
  or age-inappropriate content.
- Do not make frightening situations more intense
  unless the parent specifically asks for an adventurous story,
  and even then keep it child-safe.
- Do not lecture the reader.

QUALITY RULES:

- Do not repeat sentences.
- Do not repeat paragraphs.
- Do not repeat the title.
- Do not use placeholder text.
- Do not suddenly change the character's name.
- Do not finish in the middle of an event.
- Do not stop mid-sentence.
- Do not mention these instructions.

OUTPUT FORMAT:

Title: <creative story title>

Story:
<complete story>
""".strip()


# ============================================================
# AGE-SPECIFIC SYSTEM PROMPT
# ============================================================

def get_system_prompt_for_age(
    age: Optional[str] = None,
) -> str:
    """
    Return the system prompt.

    Age is also passed in the user message,
    so we keep one stable system prompt to avoid
    conflicting instructions.
    """

    return SYSTEM_PROMPT


# ============================================================
# USER MESSAGE
# ============================================================

def build_user_message(
    description: str,
    age: Optional[str] = None,
    hero: Optional[str] = None,
    feedback_prompt: Optional[str] = None,
) -> str:
    """
    Build the user prompt sent to Qwen.

    NOTE:
    This function does NOT decide story length.
    qwen_worker.py is responsible for all length rules.
    """

    description = (
        description
        or ""
    ).strip()

    parts = [
        "PARENT'S MAIN GOAL:",
        description,
    ]


    # --------------------------------------------------------
    # AGE
    # --------------------------------------------------------

    if age and str(age).strip():

        parts.extend(
            [
                "",
                "TARGET AGE:",
                str(age).strip(),
                (
                    "Use vocabulary and sentence structure "
                    "appropriate for this age."
                ),
            ]
        )


    # --------------------------------------------------------
    # CHARACTER
    # --------------------------------------------------------

    if hero and hero.strip():

        parts.extend(
            [
                "",
                "MAIN STORY CHARACTER:",
                hero.strip(),
                (
                    "Use this exact character consistently "
                    "throughout the story."
                ),
            ]
        )

    else:

        parts.extend(
            [
                "",
                "MAIN STORY CHARACTER:",
                (
                    "Choose a friendly fictional character, "
                    "animal, or imaginative creature that "
                    "fits the parent's goal."
                ),
            ]
        )


    # --------------------------------------------------------
    # PARENT REVIEW / PERSONALIZATION
    # --------------------------------------------------------

    if (
        feedback_prompt
        and feedback_prompt.strip()
    ):

        parts.extend(
            [
                "",
                "PARENT FEEDBACK TO APPLY:",
                feedback_prompt.strip(),
                "",
                (
                    "Apply this feedback to the new story, "
                    "but keep the parent's main goal as the "
                    "most important instruction."
                ),
            ]
        )


    # --------------------------------------------------------
    # COMPLETENESS
    # --------------------------------------------------------

    parts.extend(
        [
            "",
            "IMPORTANT:",
            (
                "Plan the story before writing so it has "
                "a clear beginning, middle, and complete ending."
            ),
            (
                "The character should gradually make progress "
                "toward the parent's goal."
            ),
            (
                "The final paragraph must clearly show the "
                "resolution of the story."
            ),
            (
                "Never stop halfway through a sentence "
                "or halfway through an event."
            ),
            "",
            "Output only the title and the story.",
        ]
    )


    return "\n".join(parts)