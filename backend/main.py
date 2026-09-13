import os
import re
import sys
import threading
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


# ============================================================
# PROJECT PATH
# ============================================================

project_root = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
    )
)

if project_root not in sys.path:
    sys.path.append(project_root)


from ai.qwen_ipc import qwen_manager
from backend.story_generator import generate_story


# ============================================================
# DATABASE
# ============================================================

try:
    from backend.database import (
        init_database,
        save_review,
        get_review,
        get_all_reviews,
    )

    DATABASE_AVAILABLE = True

except ImportError:

    try:
        from database import (
            init_database,
            save_review,
            get_review,
            get_all_reviews,
        )

        DATABASE_AVAILABLE = True

    except ImportError as e:

        print(
            f"Database import error: {e}"
        )

        DATABASE_AVAILABLE = False


# ============================================================
# PENDING REVIEW
#
# IMPORTANT:
# A saved review is used for the NEXT story only.
#
# Old reviews in SQLite do NOT automatically affect
# a fresh first story.
# ============================================================

pending_review_feedback: Optional[str] = None

pending_review_lock = threading.Lock()


def set_pending_review_feedback(
    feedback: Optional[str],
) -> None:

    global pending_review_feedback

    with pending_review_lock:

        if feedback and feedback.strip():

            pending_review_feedback = (
                feedback.strip()
            )

        else:

            pending_review_feedback = None


def take_pending_review_feedback() -> Optional[str]:

    """
    Get the latest review and remove it
    so it is used only once.
    """

    global pending_review_feedback

    with pending_review_lock:

        feedback = (
            pending_review_feedback
        )

        pending_review_feedback = None

    return feedback


def restore_pending_review_feedback(
    feedback: Optional[str],
) -> None:

    """
    If generation fails, restore the review
    so the parent does not lose it.
    """

    global pending_review_feedback

    if not feedback:
        return

    with pending_review_lock:

        if pending_review_feedback is None:

            pending_review_feedback = (
                feedback
            )


# ============================================================
# DISPLAY CLEANUP
# ============================================================

def clean_display_content(
    text: str,
) -> str:

    if not text:
        return ""

    cleaned_lines = []

    lines = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
    )

    for line in lines:

        stripped = line.strip()

        # Remove standalone labels
        if stripped.lower() in {
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

        if re.fullmatch(
            r"[*#_\s]*(title|story)\s*:?\s*[*#_\s]*",
            stripped,
            flags=re.IGNORECASE,
        ):
            continue

        cleaned_lines.append(
            line
        )

    cleaned = "\n".join(
        cleaned_lines
    )

    cleaned = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned,
    )

    return cleaned.strip()


# ============================================================
# APP LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    # Initialize SQLite
    if DATABASE_AVAILABLE:

        try:

            init_database()

            print(
                "SQLite database initialized successfully."
            )

        except Exception as e:

            print(
                f"Database initialization error: {e}"
            )


    # Start Qwen worker
    try:

        qwen_manager.start()

        print(
            "Qwen Worker process started via FastAPI lifespan."
        )

    except Exception as e:

        print(
            f"Failed to start Qwen worker: {e}"
        )


    yield


    # Stop Qwen worker
    try:

        qwen_manager.stop()

        print(
            "Qwen Worker process stopped cleanly."
        )

    except Exception as e:

        print(
            f"Error stopping Qwen worker: {e}"
        )


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="StoryApp Backend",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC + TEMPLATES
# ============================================================

current_dir = Path(
    __file__
).resolve().parent


templates_dir = (
    current_dir
    / "templates"
)

static_dir = (
    current_dir
    / "static"
)


templates_dir.mkdir(
    exist_ok=True
)

static_dir.mkdir(
    exist_ok=True
)


app.mount(
    "/static",
    StaticFiles(
        directory=str(
            static_dir
        )
    ),
    name="static",
)


templates = Jinja2Templates(
    directory=str(
        templates_dir
    )
)


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
def serve_home(
    request: Request,
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


# ============================================================
# STORY MODELS
# ============================================================

class StoryRequest(
    BaseModel
):

    description: str

    age: Optional[str] = None

    hero: Optional[str] = None

    max_tokens: Optional[int] = 800


class GenerateStoryResponse(
    BaseModel
):

    story: str

    title: Optional[str] = None

    content: Optional[str] = None

    character: Optional[str] = None

    engine: Optional[str] = None

    is_fallback: Optional[bool] = False


# ============================================================
# GENERATE STORY
# ============================================================

@app.post(
    "/generate-story",
    response_model=GenerateStoryResponse,
)
async def create_story(
    request: StoryRequest,
):

    if not request.description.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "Story description cannot be empty."
            ),
        )


    # ------------------------------------------
    # GET REVIEW FOR NEXT STORY ONLY
    # ------------------------------------------

    feedback_prompt = (
        take_pending_review_feedback()
    )


    if feedback_prompt:

        print(
            "\n"
            "Using NEW review for this next story only:"
        )

        print(
            feedback_prompt
        )

        print()

    else:

        print(
            "\n"
            "No pending review. "
            "Generating a NORMAL first/new story."
            "\n"
        )


    try:

        result = await generate_story(

            description=
                request.description.strip(),

            age=
                request.age,

            hero=
                request.hero,

            feedback_prompt=
                feedback_prompt,

            max_tokens=
                request.max_tokens
                or 800,
        )


        clean_content = (
            clean_display_content(

                result.get(
                    "content"
                )

                or result.get(
                    "story",
                    "",
                )
            )
        )


        return {

            "story":
                clean_content,

            "title":
                result.get(
                    "title",
                    "A Gentle Adventure",
                ),

            "content":
                clean_content,

            "character":
                result.get(
                    "character"
                ),

            "engine":
                result.get(
                    "engine"
                ),

            "is_fallback":
                result.get(
                    "is_fallback",
                    False,
                ),
        }


    except ValueError as e:

        restore_pending_review_feedback(
            feedback_prompt
        )

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


    except RuntimeError as e:

        restore_pending_review_feedback(
            feedback_prompt
        )

        raise HTTPException(
            status_code=503,
            detail=str(e),
        )


    except Exception as e:

        restore_pending_review_feedback(
            feedback_prompt
        )

        print(
            f"Story generation error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate story: "
                f"{str(e)}"
            ),
        )


# ============================================================
# CHAT MODELS
# ============================================================

class ChatMessage(
    BaseModel
):

    role: str

    content: str


class ChatRequest(
    BaseModel
):

    messages: List[
        ChatMessage
    ]

    storyContext: Optional[
        Dict[str, Any]
    ] = None

    currentStory: Optional[
        Dict[str, Any]
    ] = None


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
):

    if not request.messages:

        raise HTTPException(
            status_code=400,
            detail="No messages provided.",
        )


    user_messages = [

        message.content.strip()

        for message
        in request.messages

        if (
            message.role.lower()
            == "user"

            and message.content.strip()
        )
    ]


    if not user_messages:

        raise HTTPException(
            status_code=400,
            detail="No user message provided.",
        )


    latest_user_message = (
        user_messages[-1]
    )

    latest_lower = (
        latest_user_message
        .lower()
        .strip()
    )


    # ========================================================
    # DETECT DIRECT REFINEMENT
    # ========================================================

    refinement_keywords = [

        "funnier",

        "longer",

        "shorter",

        "more adventure",

        "less scary",

        "more animals",

        "different ending",

        "bedtime ending",
    ]


    is_refinement = (

        len(user_messages) > 1

        and any(

            keyword in latest_lower

            for keyword
            in refinement_keywords
        )
    )


    current_feedback: List[str] = []


    if is_refinement:

        primary_goal = next(

            (
                message

                for message
                in user_messages[:-1]

                if len(
                    message.split()
                ) >= 4
            ),

            user_messages[0],
        )


        active_description = (
            primary_goal
        )


        if "longer" in latest_lower:

            current_feedback.append(
                "Parent requested a longer story."
            )


        if "shorter" in latest_lower:

            current_feedback.append(
                "Parent requested a shorter story."
            )


        if "funnier" in latest_lower:

            current_feedback.append(
                "Parent requested more gentle humor."
            )


        if "more adventure" in latest_lower:

            current_feedback.append(
                "Parent requested more safe adventure."
            )


        if "less scary" in latest_lower:

            current_feedback.append(
                "Parent requested a gentler and less scary story."
            )


        if "more animals" in latest_lower:

            current_feedback.append(
                "Parent requested more friendly animal characters."
            )


        if "different ending" in latest_lower:

            current_feedback.append(
                "Parent requested a different ending."
            )


        if "bedtime ending" in latest_lower:

            current_feedback.append(
                "Parent requested a peaceful bedtime ending."
            )


    else:

        active_description = (
            latest_user_message
        )


    requested_age = None

    hero = None


    if request.storyContext:

        requested_age = (
            request.storyContext.get(
                "age"
            )
        )

        hero = (
            request.storyContext.get(
                "hero"
            )
        )


    # ------------------------------------------
    # GET NEW REVIEW ONCE
    # ------------------------------------------

    pending_feedback = (
        take_pending_review_feedback()
    )


    feedback_parts: List[str] = []


    if current_feedback:

        feedback_parts.append(

            "CURRENT PARENT REQUEST:\n"

            + "\n".join(
                current_feedback
            )
        )


    if pending_feedback:

        feedback_parts.append(

            "NEWLY SAVED REVIEW "
            "FOR THIS NEXT STORY:\n"

            + pending_feedback
        )


    final_feedback_prompt = (

        "\n\n".join(
            feedback_parts
        )

        if feedback_parts

        else None
    )


    if final_feedback_prompt:

        print(
            "\n"
            "Feedback being sent to Qwen:"
        )

        print(
            final_feedback_prompt
        )

        print()

    else:

        print(
            "\n"
            "No pending review. "
            "Generating a NORMAL first/new story."
            "\n"
        )


    try:

        result = await generate_story(

            description=
                active_description,

            age=
                requested_age,

            hero=
                hero,

            feedback_prompt=
                final_feedback_prompt,

            max_tokens=
                800,
        )


        title = (
            result.get(
                "title",
                "A Gentle Adventure",
            )
        )


        content = (
            clean_display_content(

                result.get(
                    "content"
                )

                or result.get(
                    "story",
                    "",
                )
            )
        )


        resolved_character = (

            result.get(
                "character"
            )

            or hero

            or "Barnaby the Bear"
        )


        updated_context = dict(
            request.storyContext
            or {}
        )


        updated_context[
            "hero"
        ] = (
            resolved_character
        )


        return {

            "assistantMessage": (
                f"Here is a story about "
                f"{resolved_character} "
                f"created for your child"
            ),

            "message":
                content,

            "story": {

                "title":
                    title,

                "content":
                    content,

                "story":
                    content,

                "character":
                    resolved_character,

                "raw":
                    result.get(
                        "raw",
                        "",
                    ),
            },

            "storyContext":
                updated_context,

            "suggestions": [

                "Make it funnier",

                "Make it longer",

                "Make it shorter",

                "More adventure",
            ],

            "engine":
                result.get(
                    "engine"
                ),

            "is_fallback":
                result.get(
                    "is_fallback",
                    False,
                ),
        }


    except ValueError as e:

        restore_pending_review_feedback(
            pending_feedback
        )

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


    except RuntimeError as e:

        restore_pending_review_feedback(
            pending_feedback
        )

        raise HTTPException(
            status_code=503,
            detail=str(e),
        )


    except Exception as e:

        restore_pending_review_feedback(
            pending_feedback
        )

        print(
            f"Chat error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process chat request."
            ),
        )


# ============================================================
# REVIEW MODEL
# ============================================================

class ParentReviewRequest(
    BaseModel
):

    story_id: Optional[str] = None
    storyId: Optional[str] = None

    story_title: Optional[str] = None
    storyTitle: Optional[str] = None

    age: Optional[str] = None

    rating: int

    parent_liked: Optional[bool] = None
    parentLiked: Optional[bool] = None

    child_satisfied: Optional[str] = None
    childSatisfied: Optional[str] = None

    length_feedback: Optional[str] = None
    lengthFeedback: Optional[str] = None

    difficulty_feedback: Optional[str] = None
    difficultyFeedback: Optional[str] = None

    improvement_tags: Optional[
        List[str]
    ] = None

    improvementTags: Optional[
        List[str]
    ] = None

    comment: Optional[str] = ""

    feedback: Optional[str] = None

    parent_name: Optional[str] = None


# ============================================================
# REVIEW HELPERS
# ============================================================

def _normalize_review_value(
    value: Optional[str],
) -> str:

    return (
        (value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def build_feedback_from_current_review(
    *,
    rating: int,
    parent_liked: Optional[bool],
    child_satisfied: Optional[str],
    length_feedback: Optional[str],
    difficulty_feedback: Optional[str],
    improvement_tags: Optional[
        List[str]
    ],
    comment: Optional[str],
) -> Optional[str]:

    """
    Build feedback ONLY from the review
    that was just submitted.

    Old database reviews are NOT used.
    """

    parts: List[str] = []


    # ------------------------------------------
    # RATING
    # ------------------------------------------

    if rating <= 4:

        parts.append(
            "The previous story received a low rating. "
            "Make the next story more engaging and natural."
        )

    elif rating <= 6:

        parts.append(
            "Improve the flow and engagement "
            "of the next story."
        )


    # ------------------------------------------
    # PARENT LIKED?
    # ------------------------------------------

    if parent_liked is False:

        parts.append(
            "The parent did not like the previous story. "
            "Improve the storytelling while keeping "
            "the parent's main goal."
        )


    # ------------------------------------------
    # CHILD SATISFACTION
    # ------------------------------------------

    child_value = (
        _normalize_review_value(
            child_satisfied
        )
    )


    if child_value in {
        "no",
        "not_really",
        "a_little",
        "little",
    }:

        parts.append(
            "The child was not fully satisfied. "
            "Make the next story more engaging and enjoyable."
        )


    # ------------------------------------------
    # STORY LENGTH
    # ------------------------------------------

    length_value = (
        _normalize_review_value(
            length_feedback
        )
    )


    if length_value in {
        "too_short",
        "short",
    }:

        parts.append(
            "The previous story was too short. "
            "Make the next story longer."
        )


    elif length_value in {
        "too_long",
        "long",
    }:

        parts.append(
            "The previous story was too long. "
            "Make the next story shorter."
        )


    # ------------------------------------------
    # READING DIFFICULTY
    # ------------------------------------------

    difficulty_value = (
        _normalize_review_value(
            difficulty_feedback
        )
    )


    if difficulty_value in {
        "too_difficult",
        "difficult",
        "too_hard",
    }:

        parts.append(
            "The previous story was too difficult. "
            "Use simple, familiar words and shorter sentences."
        )


    elif difficulty_value in {
        "too_easy",
        "easy",
    }:

        parts.append(
            "The previous story was too easy. "
            "Use slightly richer vocabulary while "
            "keeping it child-friendly."
        )


    # ------------------------------------------
    # IMPROVEMENT TAGS
    # ------------------------------------------

    tag_map = {

        "funnier":
            "Add more gentle humor.",

        "more_adventure":
            "Add more safe adventure and discovery.",

        "more_animals":
            "Include more friendly animal characters.",

        "less_scary":
            "Make the story gentler and less scary.",

        "longer":
            "Make the next story longer.",

        "shorter":
            "Make the next story shorter.",
    }


    for tag in (
        improvement_tags
        or []
    ):

        key = (
            _normalize_review_value(
                tag
            )
        )

        instruction = (
            tag_map.get(
                key
            )
        )

        if instruction:

            parts.append(
                instruction
            )


    # ------------------------------------------
    # COMMENT
    # ------------------------------------------

    if (
        comment
        and comment.strip()
    ):

        parts.append(
            "Parent's additional comment: "
            + comment.strip()
        )


    result = "\n".join(
        parts
    ).strip()


    return (
        result
        or None
    )


# ============================================================
# SAVE REVIEW
# ============================================================

@app.post("/reviews")
def create_review(
    request: ParentReviewRequest,
):

    if not DATABASE_AVAILABLE:

        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )


    story_id = (

        request.storyId

        or request.story_id
    )


    if not story_id:

        raise HTTPException(
            status_code=400,
            detail="Story ID is required.",
        )


    if (
        request.rating < 1
        or request.rating > 10
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Rating must be between 1 and 10."
            ),
        )


    story_title = (

        request.storyTitle

        or request.story_title

        or ""
    )


    parent_liked = (

        request.parentLiked

        if request.parentLiked
        is not None

        else request.parent_liked
    )


    child_satisfied = (

        request.childSatisfied

        or request.child_satisfied
    )


    length_feedback = (

        request.lengthFeedback

        or request.length_feedback
    )


    difficulty_feedback = (

        request.difficultyFeedback

        or request.difficulty_feedback
    )


    improvement_tags = (

        request.improvementTags

        if request.improvementTags
        is not None

        else request.improvement_tags
    )


    comment = (

        request.comment

        or request.feedback

        or ""
    )


    try:

        # ------------------------------------------
        # SAVE REVIEW IN DATABASE
        # ------------------------------------------

        result = save_review(

            story_id=
                story_id,

            story_title=
                story_title,

            age=
                request.age,

            rating=
                request.rating,

            parent_liked=
                parent_liked,

            child_satisfied=
                child_satisfied,

            length_feedback=
                length_feedback,

            difficulty_feedback=
                difficulty_feedback,

            improvement_tags=
                improvement_tags,

            comment=
                comment,
        )


        # ------------------------------------------
        # CREATE FEEDBACK FROM THIS REVIEW ONLY
        # ------------------------------------------

        next_story_feedback = (
            build_feedback_from_current_review(

                rating=
                    request.rating,

                parent_liked=
                    parent_liked,

                child_satisfied=
                    child_satisfied,

                length_feedback=
                    length_feedback,

                difficulty_feedback=
                    difficulty_feedback,

                improvement_tags=
                    improvement_tags,

                comment=
                    comment,
            )
        )


        # ------------------------------------------
        # SAVE IT TEMPORARILY FOR NEXT STORY
        # ------------------------------------------

        set_pending_review_feedback(
            next_story_feedback
        )


        print(
            "\n"
            "Review saved. "
            "This feedback will be used ONCE "
            "for the next story:"
        )

        print(
            next_story_feedback
            or "(No special feedback)"
        )

        print()


        return {

            "message":
                "Review saved successfully.",

            "review":
                result,
        }


    except Exception as e:

        print(
            f"Review save error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save review."
            ),
        )


# ============================================================
# GET ONE REVIEW
# ============================================================

@app.get(
    "/reviews/{story_id}"
)
def fetch_review(
    story_id: str,
):

    if not DATABASE_AVAILABLE:

        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )


    try:

        review = get_review(
            story_id
        )


        if review is None:

            raise HTTPException(
                status_code=404,
                detail="Review not found.",
            )


        return review


    except HTTPException:

        raise


    except Exception as e:

        print(
            f"Review fetch error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch review."
            ),
        )


# ============================================================
# GET ALL REVIEWS
# ============================================================

@app.get("/reviews")
def fetch_all_reviews():

    if not DATABASE_AVAILABLE:

        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )


    try:

        return {

            "reviews":
                get_all_reviews()
        }


    except Exception as e:

        print(
            f"Reviews fetch error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to fetch reviews."
            ),
        )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "ok",

        "worker_alive":
            qwen_manager.is_alive(),

        "database_connected":
            DATABASE_AVAILABLE,

        "review_waiting_for_next_story":
            pending_review_feedback
            is not None,
    }


# ============================================================
# DIRECT RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )