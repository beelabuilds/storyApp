"""Qwen worker for StoryApp.

This file is the only place that controls story length.

Length modes:
- long:   450-550 words
- normal: 300-400 words
- short:  200-280 words

The worker:
1. reads parent feedback,
2. chooses a single length mode,
3. generates one story,
4. retries once if the story is too short/too long/incomplete,
5. chooses the better draft,
6. returns one complete story.

It does NOT append large continuations, because that caused very long,
messy stories with the small local model.
"""

import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional, Tuple


# ============================================================
# PROJECT PATH
# ============================================================

project_root = Path(__file__).resolve().parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


from ai.prompts import (
    get_system_prompt_for_age,
    build_user_message,
)

from ai.story_cleaner import strip_thinking_tags


logger = logging.getLogger("qwen_worker")

logging.basicConfig(
    level=logging.INFO,
    format="[QwenWorker %(asctime)s] %(message)s",
)


# ============================================================
# FIND LOCAL GGUF MODEL
# ============================================================

def find_local_gguf_model() -> Optional[str]:

    env_path = os.getenv(
        "QWEN_MODEL_PATH",
        "",
    ).strip()

    if env_path and Path(env_path).is_file():
        return str(
            Path(env_path).resolve()
        )

    search_dirs = [
        project_root / "models",
        project_root / "ai" / "models",
        project_root / "ai",
    ]

    for directory in search_dirs:

        if not directory.is_dir():
            continue

        for gguf in directory.glob(
            "*.gguf"
        ):
            return str(
                gguf.resolve()
            )

    hf_cache = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
    )

    if hf_cache.is_dir():

        for gguf in hf_cache.rglob(
            "*.gguf"
        ):

            if (
                "qwen" in gguf.name.lower()
                and not gguf.name.endswith(
                    ".incomplete"
                )
            ):

                return str(
                    gguf.resolve()
                )

    return None


# ============================================================
# FEEDBACK / LENGTH MODE
# ============================================================

def _normalize_feedback(
    text: Optional[str],
) -> str:

    return (
        (text or "")
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("–", " ")
        .replace("—", " ")
    )

def _length_mode(
    feedback_prompt: Optional[str],
) -> str:
    """
    Detect ONLY story-length feedback.

    Important:
    Phrases such as "shorter sentences" refer to reading
    difficulty, NOT story length, so they must not trigger
    SHORT mode.
    """

    text = _normalize_feedback(
        feedback_prompt
    )

    # ------------------------------------------
    # EXPLICIT LONG STORY FEEDBACK
    # ------------------------------------------

    long_signals = (
        "too short",
        "story was too short",
        "story is too short",
        "previous story was too short",
        "make the next story longer",
        "make the story longer",
        "parent requested a longer story",
        "longer with more useful story development",
        "length feedback too short",
    )

    if any(
        signal in text
        for signal in long_signals
    ):
        return "long"


    # ------------------------------------------
    # EXPLICIT SHORT STORY FEEDBACK
    # ------------------------------------------

    short_signals = (
        "too long",
        "story was too long",
        "story is too long",
        "previous story was too long",
        "make the next story shorter",
        "make the story shorter",
        "parent requested a shorter story",
        "length feedback too long",
    )

    if any(
        signal in text
        for signal in short_signals
    ):
        return "short"


    # ------------------------------------------
    # CHECK STANDALONE IMPROVEMENT TAGS
    # ------------------------------------------

    lines = [
        line.strip(" .,:;-").lower()
        for line in text.splitlines()
        if line.strip()
    ]

    if "longer" in lines:
        return "long"

    if "shorter" in lines:
        return "short"


    # "shorter sentences" is intentionally ignored.
    return "normal"

# ============================================================
# LENGTH CONFIG
# ============================================================

def _length_config(
    mode: str,
) -> Tuple[
    int,
    int,
    int,
    str,
]:

    if mode == "long":

        return (
            450,
            550,
            900,
            (
                "LENGTH MODE: LONG.\n"
                "Write a complete story of about 450 to 550 words.\n"
                "Use exactly 7 developed paragraphs.\n"
                "Each paragraph should move the story forward.\n"
                "Use useful scenes, gentle dialogue, actions, and feelings.\n"
                "Do not repeat ideas just to make the story longer.\n"
                "Reserve the final paragraph for a clear, satisfying ending."
            ),
        )

    if mode == "short":

        return (
            200,
            280,
            520,
            (
                "LENGTH MODE: SHORT.\n"
                "Write a complete story of about 200 to 280 words.\n"
                "Use 3 to 4 short paragraphs.\n"
                "Keep the story concise, but include a real ending."
            ),
        )

    return (
        300,
        400,
        700,
        (
            "LENGTH MODE: NORMAL.\n"
            "Write a complete story of about 300 to 400 words.\n"
            "Use 4 to 5 paragraphs.\n"
            "Give the story a clear beginning, middle, and ending."
        ),
    )


# ============================================================
# STORY CHECKS
# ============================================================

def _word_count(
    text: str,
) -> int:

    visible = strip_thinking_tags(
        text or ""
    )

    return len(
        re.findall(
            r"\b[\w'-]+\b",
            visible,
        )
    )


def _ends_cleanly(
    text: str,
) -> bool:

    visible = strip_thinking_tags(
        text or ""
    ).strip()

    if not visible:
        return False

    return bool(
        re.search(
            r'[.!?]["”’\']?\s*$',
            visible,
        )
    )


def _is_complete(
    text: str,
    finish_reason: Optional[str],
) -> bool:

    if (
        finish_reason
        or ""
    ).lower() == "length":

        return False

    return _ends_cleanly(
        text
    )


def _trim_incomplete_tail(
    text: str,
) -> str:

    visible = strip_thinking_tags(
        text or ""
    ).strip()

    if not visible:
        return ""

    if _ends_cleanly(
        visible
    ):
        return visible

    last_complete = max(
        visible.rfind("."),
        visible.rfind("?"),
        visible.rfind("!"),
    )

    if last_complete >= 0:

        return visible[
            :last_complete + 1
        ].strip()

    return visible


# ============================================================
# MODEL CALL
# ============================================================

def _call_model(
    llm,
    messages,
    max_tokens: int,
):

    kwargs = {

        "messages":
            messages,

        "max_tokens":
            max_tokens,

        "temperature":
            0.35,

        "top_p":
            0.80,

        "top_k":
            20,

        "repeat_penalty":
            1.08,

        "presence_penalty":
            0.0,
    }

    try:

        return llm.create_chat_completion(

            **kwargs,

            chat_template_kwargs={
                "enable_thinking":
                    False,
            },
        )

    except TypeError:

        return llm.create_chat_completion(
            **kwargs
        )


def _read_response(
    response,
) -> Tuple[
    str,
    str,
    Optional[str],
]:

    choice = response[
        "choices"
    ][0]

    raw_text = (

        choice
        .get(
            "message",
            {},
        )
        .get(
            "content"
        )

        or ""
    )

    visible_text = (
        strip_thinking_tags(
            raw_text
        ).strip()
    )

    finish_reason = (
        choice.get(
            "finish_reason"
        )
    )

    return (
        raw_text,
        visible_text,
        finish_reason,
    )


# ============================================================
# PROMPT BUILDING
# ============================================================

def _build_effective_feedback(
    feedback_prompt: Optional[str],
    length_instruction: str,
) -> str:

    parts = []

    if (
        feedback_prompt
        and feedback_prompt.strip()
    ):

        parts.append(
            "PARENT REVIEW TO APPLY:\n"
            + feedback_prompt.strip()
        )

    parts.append(
        length_instruction
    )

    parts.append(
        "COMPLETENESS RULE:\n"
        "Plan the story before writing.\n"
        "The story must have a real beginning, middle, and resolution.\n"
        "Do not stop in the middle of an event.\n"
        "Do not stop in the middle of a sentence.\n"
        "The last paragraph must clearly finish the story."
    )

    return "\n\n".join(
        parts
    )


def _build_messages(
    description: str,
    age: Optional[str],
    hero: Optional[str],
    system_prompt: str,
    feedback_prompt: str,
):

    user_message = (
        build_user_message(

            description=
                description,

            age=
                age,

            hero=
                hero,

            feedback_prompt=
                feedback_prompt,
        )
    )

    return [

        {
            "role":
                "system",

            "content":
                system_prompt,
        },

        {
            "role":
                "user",

            "content":
                user_message,
        },
    ]


# ============================================================
# CANDIDATE SELECTION
# ============================================================

def _candidate_score(
    text: str,
    finish_reason: Optional[str],
    min_words: int,
    max_words: int,
) -> Tuple[
    int,
    int,
]:

    words = _word_count(
        text
    )

    complete = _is_complete(
        text,
        finish_reason,
    )

    if (
        min_words
        <= words
        <= max_words
    ):
        distance = 0

    elif words < min_words:
        distance = (
            min_words
            - words
        )

    else:
        distance = (
            words
            - max_words
        )

    if (
        complete
        and distance == 0
    ):
        tier = 4

    elif complete:
        tier = 3

    elif distance == 0:
        tier = 2

    else:
        tier = 1

    return (
        tier,
        -distance,
    )


# ============================================================
# WORKER
# ============================================================

def run_qwen_worker(
    request_queue,
    response_queue,
    stop_event,
    model_path: Optional[str] = None,
):

    logger.info(
        "Starting Qwen Worker Process "
        "(PID: %s)...",
        os.getpid(),
    )

    actual_model_path = (

        model_path

        or find_local_gguf_model()
    )

    llm = None

    engine_name = (
        "Qwen Local GGUF"
    )

    load_error_message = None


    # ========================================================
    # LOAD MODEL
    # ========================================================

    if (
        actual_model_path
        and Path(
            actual_model_path
        ).is_file()
    ):

        try:

            from llama_cpp import Llama

            cpu_threads = max(

                1,

                (
                    os.cpu_count()
                    or 2
                ) - 1,
            )

            logger.info(
                "Loading model: %s",
                actual_model_path,
            )

            started = time.time()

            llm = Llama(

                model_path=
                    actual_model_path,

                n_ctx=
                    4096,

                n_batch=
                    256,

                n_threads=
                    cpu_threads,

                verbose=
                    False,
            )

            model_name = Path(
                actual_model_path
            ).name

            engine_name = (
                f"Qwen Local GGUF "
                f"({model_name})"
            )

            logger.info(
                "Qwen loaded successfully "
                "in %.2f seconds.",
                time.time()
                - started,
            )

            logger.info(
                "Context window: 4096"
            )

        except Exception as exc:

            load_error_message = (
                "Failed to load GGUF model: "
                f"{exc}"
            )

            logger.exception(
                load_error_message
            )

    else:

        load_error_message = (
            "No local Qwen GGUF model found. "
            "Put a .gguf file in models/ "
            "or set QWEN_MODEL_PATH."
        )

        logger.error(
            load_error_message
        )


    # ========================================================
    # MAIN LOOP
    # ========================================================

    while not stop_event.is_set():

        try:

            try:

                task = request_queue.get(
                    timeout=0.3
                )

            except Exception:

                continue

            if task is None:
                break


            correlation_id = (
                task.get(
                    "correlation_id"
                )
            )


            # =================================================
            # MODEL CHECK
            # =================================================

            if llm is None:

                response_queue.put(
                    {

                        "correlation_id":
                            correlation_id,

                        "success":
                            False,

                        "error":
                            (
                                load_error_message
                                or
                                "Qwen model is not loaded."
                            ),

                        "engine":
                            "Qwen Local GGUF (Error)",

                        "is_fallback":
                            False,
                    }
                )

                continue


            # =================================================
            # REQUEST DATA
            # =================================================

            description = (
                task.get(
                    "description",
                    "",
                )
            )

            age = task.get(
                "age"
            )

            hero = task.get(
                "hero"
            )

            parent_feedback = (
                task.get(
                    "feedback_prompt"
                )
            )


            # =================================================
            # LENGTH MODE
            # =================================================

            mode = _length_mode(
                parent_feedback
            )

            (
                min_words,
                max_words,
                max_tokens,
                length_instruction,
            ) = _length_config(
                mode
            )

            effective_feedback = (
                _build_effective_feedback(

                    parent_feedback,

                    length_instruction,
                )
            )

            logger.info(
                "Request %s | "
                "mode=%s | "
                "target=%d-%d words | "
                "max_tokens=%d",

                correlation_id,

                mode.upper(),

                min_words,

                max_words,

                max_tokens,
            )


            try:

                started = time.time()

                system_prompt = (
                    get_system_prompt_for_age(
                        age
                    )
                )


                # =================================================
                # ATTEMPT 1
                # =================================================

                messages_1 = (
                    _build_messages(

                        description=
                            description,

                        age=
                            age,

                        hero=
                            hero,

                        system_prompt=
                            system_prompt,

                        feedback_prompt=
                            effective_feedback,
                    )
                )

                response_1 = (
                    _call_model(

                        llm,

                        messages_1,

                        max_tokens,
                    )
                )

                (
                    raw_1,
                    story_1,
                    finish_1,
                ) = _read_response(
                    response_1
                )

                words_1 = _word_count(
                    story_1
                )

                complete_1 = (
                    _is_complete(
                        story_1,
                        finish_1,
                    )
                )

                logger.info(
                    "Attempt 1 | "
                    "words=%d | "
                    "complete=%s | "
                    "finish=%s",

                    words_1,

                    complete_1,

                    finish_1,
                )

                score_1 = (
                    _candidate_score(

                        story_1,

                        finish_1,

                        min_words,

                        max_words,
                    )
                )

                best_raw = raw_1
                best_story = story_1
                best_finish = finish_1
                best_score = score_1


                acceptable_1 = (

                    complete_1

                    and min_words
                    <= words_1
                    <= max_words
                )


                # =================================================
                # ATTEMPT 2 ONLY IF NEEDED
                # =================================================

                if not acceptable_1:

                    if words_1 < min_words:

                        correction = (
                            f"The previous draft was only "
                            f"{words_1} words, so it was too short. "
                            f"Rewrite the whole story from the beginning "
                            f"and make it {min_words} to "
                            f"{max_words} words."
                        )

                    elif words_1 > max_words:

                        correction = (
                            f"The previous draft was "
                            f"{words_1} words, so it was too long. "
                            f"Rewrite the whole story from the beginning "
                            f"and keep it between "
                            f"{min_words} and {max_words} words."
                        )

                    else:

                        correction = (
                            "The previous draft did not finish properly. "
                            "Rewrite the whole story from the beginning "
                            "and make sure the final paragraph clearly "
                            "resolves the story."
                        )


                    retry_feedback = (

                        effective_feedback

                        + "\n\n"

                        + "REWRITE CORRECTION:\n"

                        + correction

                        + "\n"

                        + (
                            "Do not continue the old draft. "
                            "Write one new complete story."
                        )
                    )


                    messages_2 = (
                        _build_messages(

                            description=
                                description,

                            age=
                                age,

                            hero=
                                hero,

                            system_prompt=
                                system_prompt,

                            feedback_prompt=
                                retry_feedback,
                        )
                    )


                    response_2 = (
                        _call_model(

                            llm,

                            messages_2,

                            max_tokens,
                        )
                    )


                    (
                        raw_2,
                        story_2,
                        finish_2,
                    ) = _read_response(
                        response_2
                    )


                    words_2 = (
                        _word_count(
                            story_2
                        )
                    )


                    complete_2 = (
                        _is_complete(

                            story_2,

                            finish_2,
                        )
                    )


                    logger.info(
                        "Attempt 2 | "
                        "words=%d | "
                        "complete=%s | "
                        "finish=%s",

                        words_2,

                        complete_2,

                        finish_2,
                    )


                    score_2 = (
                        _candidate_score(

                            story_2,

                            finish_2,

                            min_words,

                            max_words,
                        )
                    )


                    if score_2 > best_score:

                        best_raw = raw_2

                        best_story = story_2

                        best_finish = finish_2

                        best_score = score_2


                # =================================================
                # FINAL SAFETY CLEANUP
                # =================================================

                final_story = (
                    strip_thinking_tags(
                        best_story
                    ).strip()
                )


                final_complete = (
                    _is_complete(

                        final_story,

                        best_finish,
                    )
                )


                if not final_complete:

                    # Do NOT append another large continuation.
                    # Only remove an unfinished final fragment.
                    final_story = (
                        _trim_incomplete_tail(
                            final_story
                        )
                    )


                final_words = (
                    _word_count(
                        final_story
                    )
                )


                final_complete = (
                    _ends_cleanly(
                        final_story
                    )
                )


                logger.info(
                    "FINAL | "
                    "mode=%s | "
                    "words=%d | "
                    "complete=%s | "
                    "time=%.2fs",

                    mode.upper(),

                    final_words,

                    final_complete,

                    time.time()
                    - started,
                )


                response_queue.put(
                    {

                        "correlation_id":
                            correlation_id,

                        "success":
                            True,

                        "story":
                            final_story,

                        "raw":
                            final_story,

                        "engine":
                            engine_name,

                        "is_fallback":
                            False,
                    }
                )


            except Exception as exc:

                logger.exception(
                    "Generation failed "
                    "for %s",
                    correlation_id,
                )


                response_queue.put(
                    {

                        "correlation_id":
                            correlation_id,

                        "success":
                            False,

                        "error":
                            (
                                "Qwen model inference "
                                "failed: "
                                f"{exc}"
                            ),

                        "engine":
                            engine_name,

                        "is_fallback":
                            False,
                    }
                )


        except KeyboardInterrupt:

            break


        except Exception:

            logger.exception(
                "Unexpected worker loop error"
            )


    logger.info(
        "Qwen worker stopped cleanly."
    )