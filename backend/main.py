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


class StoryRequest(BaseModel):
    age: str
    event: str
    goal: str
    character: str
    language: str


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