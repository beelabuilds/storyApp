import os
import sys
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make project root importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from story_generator import generate_story


# ============================================================
# APP
# ============================================================

app = FastAPI(title="StoryApp Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Story App backend is running!"
    }


# ============================================================
# STORY GENERATION
# ============================================================

class StoryRequest(BaseModel):
    description: str


class GenerateStoryResponse(BaseModel):
    story: str
    title: Optional[str] = None
    content: Optional[str] = None
    engine: Optional[str] = None


@app.post("/generate-story", response_model=GenerateStoryResponse)
def create_story(request: StoryRequest):
    """
    Generate a story from the parent's natural-language description.

    Example:
    {
        "description": "My daughter was scared to sleep alone
        because she heard a strange sound outside her room."
    }
    """

    if not request.description.strip():
        raise HTTPException(
            status_code=400,
            detail="Story description cannot be empty."
        )

    try:
        result = generate_story(request.description)

        return {
            "story": result.get("story", ""),
            "title": result.get("title", ""),
            "content": result.get("content", ""),
            "engine": result.get("engine")
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    except Exception as e:
        print(f"Story generation error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to generate story."
        )


# ============================================================
# CHAT
# ============================================================
# Kept for frontend compatibility.

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    storyContext: Optional[Dict[str, Any]] = None
    currentStory: Optional[Dict[str, Any]] = None


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for story generation assistant.
    """

    if not request.messages:
        raise HTTPException(
            status_code=400,
            detail="No messages provided."
        )

    # Get the latest user message
    user_message = None

    for message in reversed(request.messages):
        if message.role.lower() == "user":
            user_message = message.content
            break

    if not user_message or not user_message.strip():
        raise HTTPException(
            status_code=400,
            detail="No user message provided."
        )

    try:
        # Build personalization from previous parent reviews.
        personalized_description = user_message

        try:
            from database import build_parent_feedback_prompt

            requested_age = None
            if request.storyContext:
                requested_age = request.storyContext.get("age")

            feedback_prompt = build_parent_feedback_prompt(
                age=requested_age
            )

            if feedback_prompt:
                personalized_description = f"""PARENT'S NEW STORY REQUEST:
{user_message}

SAVED PARENT PREFERENCES:
{feedback_prompt}

Create the story requested by the parent while naturally applying these preferences.
Do not mention the feedback, database, ratings, or personalization instructions in the story."""

                print("Parent feedback personalization applied.")

        except Exception as feedback_error:
            # Story generation should still work even if feedback cannot be read.
            print(f"Feedback personalization unavailable: {feedback_error}")

        result = generate_story(personalized_description)
        title = result.get("title", "A New Adventure")
        content = result.get("content") or result.get("story", "")
        raw_story = result.get("story", "")

        return {
            "assistantMessage": "Here is a story created for your child ✨",
            "message": content,
            "story": {
                "title": title,
                "content": content,
                "story": content,
                "raw": raw_story
            },
            "storyContext": request.storyContext or {},
            "suggestions": ["Bedtime story", "Another adventure", "Make it funnier"],
            "engine": result.get("engine")
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    except Exception as e:
        print(f"Chat error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to process chat request."
        )


# ============================================================
# REVIEWS / DATABASE
# ============================================================

try:
    from database import (
        init_database,
        save_review,
        get_review,
        get_all_reviews,
    )

    DATABASE_AVAILABLE = True

except ImportError as e:
    print(f"Database import error: {e}")
    DATABASE_AVAILABLE = False


# Initialize database
if DATABASE_AVAILABLE:
    try:
        init_database()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization error: {e}")


class ParentReviewRequest(BaseModel):
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
    improvement_tags: Optional[List[str]] = None
    improvementTags: Optional[List[str]] = None
    comment: Optional[str] = ""
    feedback: Optional[str] = None
    parent_name: Optional[str] = None


@app.post("/reviews")
def create_review(request: ParentReviewRequest):
    """
    Save a parent's review for a generated story.
    """

    if not DATABASE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable."
        )

    story_id = request.storyId or request.story_id
    if not story_id:
        raise HTTPException(
            status_code=400,
            detail="Story ID is required."
        )

    if request.rating < 1 or request.rating > 10:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 10."
        )

    story_title = request.storyTitle or request.story_title or ""
    parent_liked = request.parentLiked if request.parentLiked is not None else request.parent_liked
    child_satisfied = request.childSatisfied or request.child_satisfied
    length_feedback = request.lengthFeedback or request.length_feedback
    difficulty_feedback = request.difficultyFeedback or request.difficulty_feedback
    improvement_tags = request.improvementTags if request.improvementTags is not None else request.improvement_tags
    comment = request.comment or request.feedback or ""

    try:
        result = save_review(
            story_id=story_id,
            story_title=story_title,
            age=request.age,
            rating=request.rating,
            parent_liked=parent_liked,
            child_satisfied=child_satisfied,
            length_feedback=length_feedback,
            difficulty_feedback=difficulty_feedback,
            improvement_tags=improvement_tags,
            comment=comment,
        )

        return {
            "message": "Review saved successfully.",
            "review": result,
        }

    except Exception as e:
        print(f"Review save error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to save review."
        )



@app.get("/reviews/{story_id}")
def fetch_review(story_id: str):
    """
    Get the review for a specific story.
    """

    if not DATABASE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable."
        )

    try:
        review = get_review(story_id)

        if review is None:
            raise HTTPException(
                status_code=404,
                detail="Review not found."
            )

        return review

    except HTTPException:
        raise

    except Exception as e:
        print(f"Review fetch error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch review."
        )


@app.get("/reviews")
def fetch_all_reviews():
    """
    Get all story reviews.
    """

    if not DATABASE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable."
        )

    try:
        reviews = get_all_reviews()

        return {
            "reviews": reviews
        }

    except Exception as e:
        print(f"Reviews fetch error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Failed to fetch reviews."
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )