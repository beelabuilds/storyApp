import os
import sys

# Ensure backend and project root directories are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if current_dir not in sys.path:
    sys.path.append(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from story_generator import generate_story

app = FastAPI(title="StoryApp Backend")

# Enable CORS for the frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for demo purposes
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
def root():
    return {"message": "Story App backend is running!"}


from typing import List, Optional, Dict, Any
from story_generator import generate_story, suggest_goals

class StoryRequest(BaseModel):
    age: str
    event: str
    goal: str
    character: str
    language: str


class SuggestGoalsRequest(BaseModel):
    age: Optional[Any] = None
    event: Optional[str] = None
    character: Optional[str] = None
    language: Optional[str] = "English"


class SuggestGoalsResponse(BaseModel):
    suggestions: List[str]


class GenerateStoryRequest(BaseModel):
    age: Optional[Any] = None
    event: Optional[str] = None
    goal: Optional[str] = None
    character: Optional[str] = None
    language: Optional[str] = "English"


class GenerateStoryResponse(BaseModel):
    title: Optional[str] = None
    story: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    storyContext: Optional[Dict[str, Any]] = None
    currentStory: Optional[Dict[str, Any]] = None


@app.post("/suggest-goals", response_model=SuggestGoalsResponse)
def suggest_goals_endpoint(req: SuggestGoalsRequest):
    suggestions = suggest_goals(
        age=req.age,
        event=req.event,
        character=req.character,
        language=req.language or "English",
    )
    return {"suggestions": suggestions}


@app.post("/generate", response_model=GenerateStoryResponse)
def generate_endpoint(req: GenerateStoryRequest):
    result = generate_story(
        age=str(req.age or "6-8"),
        event=req.event or "",
        goal=req.goal or "",
        character=req.character or "",
        language=req.language or "English",
    )
    return {"title": result.get("title"), "story": result.get("story", "")}


@app.post("/generate-story")
def create_story(request: StoryRequest):
    result = generate_story(
        event=request.event,
        age=request.age,
        goal=request.goal,
        character=request.character,
        language=request.language
    )
    return result


import uuid
import re

def get_dynamic_suggestions(age=None, event=None, character=None, language="English") -> list:
    return suggest_goals(age=age, event=event, character=character, language=language)


def extract_context_from_text(text: str, context: dict) -> dict:
    """
    Extracts age, character, and event information if mentioned naturally in the user's message.
    """
    t_lower = text.lower()
    
    # Check for age mentions
    if not context.get("age"):
        if any(w in t_lower for w in ["4-5", "4–5", "preschool", "kindergarten", "4 years", "5 years", "4 yo", "5 yo", "age 4", "age 5"]):
            context["age"] = "4-5"
        elif any(w in t_lower for w in ["6-8", "6–8", "school age", "6 years", "7 years", "8 years", "6 yo", "7 yo", "8 yo", "age 6", "age 7", "age 8"]):
            context["age"] = "6-8"
        elif any(w in t_lower for w in ["4-8", "4–8"]):
            context["age"] = "4-8"

    return context


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    context = dict(request.storyContext or {})
    user_messages = [m for m in request.messages if m.role == "user"]
    last_user_msg = user_messages[-1].content.strip() if user_messages else ""
    msg_lower = last_user_msg.lower()

    waiting_for = context.get("waitingFor", "")

    # Check if user wants a story for a new/different child
    is_new_child_request = any(k in msg_lower for k in [
        "new child", "another child", "different child", "story for another child", "for another child", "my other child"
    ])

    if is_new_child_request:
        context.clear()
        context["storySeed"] = uuid.uuid4().hex[:12]
        context["waitingFor"] = "age"
        return {
            "assistantMessage": "Let's create a wonderful story for another child! What age group are they in?",
            "suggestions": ["4–5 years", "6–8 years", "4–8 years"],
            "storyContext": context,
            "type": "chat"
        }

    # Check if user wants a brand new story or to restart in the same chat
    is_new_story_request = any(k in msg_lower for k in [
        "another one", "another story", "tell another", "new story", "make another", "different story", "start over"
    ]) or ("change character" in msg_lower or "change hero" in msg_lower)

    if is_new_story_request:
        if "change character" in msg_lower or "change hero" in msg_lower:
            context.pop("hero", None)
            context["waitingFor"] = "hero"
            return {
                "assistantMessage": "Who should be the new main hero of the story?",
                "suggestions": ["My child", "Friendly puppy", "Magical dragon", "Curious astronaut"],
                "storyContext": context,
                "type": "chat"
            }
        else:
            context["storySeed"] = uuid.uuid4().hex[:12]
            context.pop("dailyEvent", None)
            context["waitingFor"] = "event"
            hero_name = context.get("hero", "our hero")
            suggs = get_dynamic_suggestions(age=context.get("age"), event=context.get("goal", ""), character=hero_name)
            return {
                "assistantMessage": f"What should the new story for {hero_name} be about?",
                "suggestions": suggs,
                "storyContext": context,
                "type": "chat"
            }

    # Extract any details naturally stated in the message
    context = extract_context_from_text(last_user_msg, context)

    if waiting_for == "age":
        if any(a in msg_lower for a in ["4-5", "4–5", "preschool", "kindergarten", "4", "5"]):
            context["age"] = "4-5"
        elif any(a in msg_lower for a in ["6-8", "6–8", "school", "6", "7", "8"]):
            context["age"] = "6-8"
        elif any(a in msg_lower for a in ["4-8", "4–8"]):
            context["age"] = "4-8"
        else:
            context["age"] = last_user_msg

        context["waitingFor"] = "hero"

    elif waiting_for == "hero":
        context["hero"] = last_user_msg
        context["waitingFor"] = "event"

    elif waiting_for == "event":
        context["dailyEvent"] = last_user_msg
        context["waitingFor"] = "ready"

    else:
        # Initial turn / category selection
        if not context.get("goal"):
            context["goal"] = last_user_msg
        if not context.get("age"):
            context["waitingFor"] = "age"
        elif not context.get("hero"):
            context["waitingFor"] = "hero"
        elif not context.get("dailyEvent"):
            context["waitingFor"] = "event"
        else:
            context["storySeed"] = uuid.uuid4().hex[:12]

    # Step 1: Check if age is needed
    if not context.get("age"):
        context["waitingFor"] = "age"
        return {
            "assistantMessage": "What age group is this story for (ages 4–8)?",
            "suggestions": ["4–5 years", "6–8 years", "4–8 years"],
            "storyContext": context,
            "type": "chat"
        }

    # Step 2: Check if hero is needed
    if not context.get("hero"):
        context["waitingFor"] = "hero"
        return {
            "assistantMessage": f"Who should be the main hero of our story for ages {context['age']}?",
            "suggestions": ["My child", "Friendly puppy", "Magical dragon", "Curious astronaut"],
            "storyContext": context,
            "type": "chat"
        }

    # Step 3: Check if story event/topic is needed
    if not context.get("dailyEvent"):
        context["waitingFor"] = "event"
        hero_name = context.get("hero", "our hero")
        dynamic_suggs = get_dynamic_suggestions(
            age=context.get("age"),
            event=context.get("goal", ""),
            character=hero_name
        )
        return {
            "assistantMessage": f"What should the story be about for {hero_name}? Tell me about a situation, an everyday event, or something they experienced today.",
            "suggestions": dynamic_suggs,
            "storyContext": context,
            "type": "chat"
        }

    # Step 4: All details present -> Generate story via Qwen/Engine
    event = str(context.get("dailyEvent") or "A fun day of new adventures")
    age = str(context.get("age") or "6-8")
    goal = str(context.get("goal") or "Courage, kindness, and fun")
    character = str(context.get("hero") or "A curious little adventurer")
    language = str(context.get("language") or "English")
    story_seed = context.get("storySeed") or uuid.uuid4().hex[:12]

    result = generate_story(
        event=event,
        age=age,
        goal=goal,
        character=character,
        language=language,
        story_seed=story_seed
    )

    context["waitingFor"] = "feedback"
    context["storySeed"] = uuid.uuid4().hex[:12]

    return {
        "assistantMessage": f"Here is a brand new story about {character}!",
        "suggestions": ["Story for another child", "Tell another story", "Change hero", "Make it a bedtime story"],
        "storyContext": context,
        "story": {
            "title": result.get("title", "A Wonderful Adventure"),
            "content": result.get("story", "")
        },
        "type": "story"
    }

# ============================================================
# Parent Review API
# ============================================================

from typing import Optional
from pydantic import BaseModel, Field

from database import (
    init_database,
    save_review,
    get_review,
    get_all_reviews,
)

# Make sure SQLite tables exist whenever backend starts
init_database()


class ParentReviewRequest(BaseModel):
    storyId: str
    storyTitle: str = ""
    age: str = ""

    rating: int
    parentLiked: Optional[bool] = None
    childSatisfied: Optional[str] = None

    lengthFeedback: Optional[str] = None
    difficultyFeedback: Optional[str] = None

    improvementTags: list[str] = Field(default_factory=list)
    comment: str = ""


@app.post("/reviews")
def create_or_update_parent_review(review: ParentReviewRequest):
    if review.rating < 1 or review.rating > 10:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 10."
        )

    save_review(
        story_id=review.storyId,
        story_title=review.storyTitle,
        age=review.age,
        rating=review.rating,
        parent_liked=review.parentLiked,
        child_satisfied=review.childSatisfied,
        length_feedback=review.lengthFeedback,
        difficulty_feedback=review.difficultyFeedback,
        improvement_tags=review.improvementTags,
        comment=review.comment,
    )

    saved = get_review(review.storyId)

    return {
        "success": True,
        "message": "Parent review saved.",
        "review": saved,
    }


@app.get("/reviews")
def list_parent_reviews():
    return {
        "reviews": get_all_reviews()
    }


@app.get("/reviews/{story_id}")
def get_parent_review(story_id: str):
    review = get_review(story_id)

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Review not found."
        )

    return {
        "review": review
    }
