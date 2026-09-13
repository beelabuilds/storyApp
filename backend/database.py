from pathlib import Path
import json
import sqlite3
from datetime import datetime, timezone


DB_PATH = Path(__file__).with_name("storyapp.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS parent_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT NOT NULL UNIQUE,
                story_title TEXT,
                age TEXT,
                rating INTEGER NOT NULL,
                parent_liked INTEGER,
                child_satisfied TEXT,
                length_feedback TEXT,
                difficulty_feedback TEXT,
                improvement_tags TEXT DEFAULT '[]',
                comment TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_review(
    story_id,
    story_title,
    age,
    rating,
    parent_liked,
    child_satisfied,
    length_feedback=None,
    difficulty_feedback=None,
    improvement_tags=None,
    comment=""
):
    now = datetime.now(timezone.utc).isoformat()
    tags_json = json.dumps(improvement_tags or [])

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT created_at FROM parent_reviews WHERE story_id = ?",
            (story_id,)
        ).fetchone()

        created_at = existing["created_at"] if existing else now

        conn.execute("""
            INSERT INTO parent_reviews (
                story_id,
                story_title,
                age,
                rating,
                parent_liked,
                child_satisfied,
                length_feedback,
                difficulty_feedback,
                improvement_tags,
                comment,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(story_id) DO UPDATE SET
                story_title = excluded.story_title,
                age = excluded.age,
                rating = excluded.rating,
                parent_liked = excluded.parent_liked,
                child_satisfied = excluded.child_satisfied,
                length_feedback = excluded.length_feedback,
                difficulty_feedback = excluded.difficulty_feedback,
                improvement_tags = excluded.improvement_tags,
                comment = excluded.comment,
                updated_at = excluded.updated_at
        """, (
            story_id,
            story_title,
            age,
            rating,
            None if parent_liked is None else int(parent_liked),
            child_satisfied,
            length_feedback,
            difficulty_feedback,
            tags_json,
            comment,
            created_at,
            now
        ))

        conn.commit()

    return get_review(story_id)


def _review_to_dict(row):
    if row is None:
        return None

    review = dict(row)

    # Convert parent_liked back to boolean
    parent_liked_value = (
        None
        if review["parent_liked"] is None
        else bool(review["parent_liked"])
    )

    review["parent_liked"] = parent_liked_value
    review["parentLiked"] = parent_liked_value

    # Convert improvement_tags JSON string back to list
    try:
        tags = json.loads(review["improvement_tags"] or "[]")
    except json.JSONDecodeError:
        tags = []

    review["improvement_tags"] = tags
    review["improvementTags"] = tags

    # CamelCase aliases for frontend compatibility
    review["childSatisfied"] = review.get("child_satisfied")
    review["lengthFeedback"] = review.get("length_feedback")
    review["difficultyFeedback"] = review.get("difficulty_feedback")
    review["storyId"] = review.get("story_id")
    review["storyTitle"] = review.get("story_title")

    return review


def get_review(story_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM parent_reviews WHERE story_id = ?",
            (story_id,)
        ).fetchone()

    return _review_to_dict(row)


def get_all_reviews():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT *
            FROM parent_reviews
            ORDER BY updated_at DESC
        """).fetchall()

    return [_review_to_dict(row) for row in rows]


def _normalize_age(value):
    """
    Normalize age strings so:
    4–8
    4-8
    4 — 8
    all match the same way.
    """
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("–", "-")
        .replace("—", "-")
        .replace(" ", "")
    )


def build_parent_feedback_prompt(age=None, limit=10):
    """
    Convert the most recent relevant parent review into short,
    clear instructions for the next story.

    The review changes style, length, and difficulty only.
    It must not replace the parent's new story goal.
    """

    reviews = get_all_reviews()

    if not reviews:
        return ""

    # --------------------------------------------------------
    # Pick the most recent review for the same age group
    # --------------------------------------------------------

    selected_review = None

    if age:
        requested_age = _normalize_age(age)

        same_age_reviews = [
            review
            for review in reviews
            if _normalize_age(review.get("age")) == requested_age
        ]

        if same_age_reviews:
            selected_review = same_age_reviews[0]

    # If no age match, use the newest review overall
    if selected_review is None:
        selected_review = reviews[0]

    review = selected_review

    instructions = []

    # --------------------------------------------------------
    # Rating
    # --------------------------------------------------------

    rating = review.get("rating")

    if isinstance(rating, (int, float)):
        if rating <= 4:
            instructions.append(
                "The previous story received a low rating. "
                "Make the next story more engaging and natural."
            )
        elif rating <= 6:
            instructions.append(
                "Improve the next story's flow, warmth, and engagement."
            )

    # --------------------------------------------------------
    # Parent liked / disliked
    # --------------------------------------------------------

    parent_liked = review.get("parent_liked")

    if parent_liked is False:
        instructions.append(
            "The parent did not like the previous story. "
            "Improve the storytelling style and make it more enjoyable."
        )

    # --------------------------------------------------------
    # Child satisfaction
    # --------------------------------------------------------

    child_satisfied = str(
        review.get("child_satisfied") or ""
    ).strip().lower()

    if child_satisfied in {
        "no",
        "not_really",
        "not really",
        "a_little",
        "a little"
    }:
        instructions.append(
            "Make the next story more enjoyable and engaging for the child."
        )

    # --------------------------------------------------------
    # Length feedback
    # --------------------------------------------------------

    length_feedback = str(
        review.get("length_feedback") or ""
    ).strip().lower()

    if length_feedback == "too_long":
        instructions.append(
            "Make the next story shorter, around 250 to 350 words."
        )

    elif length_feedback == "too_short":
        instructions.append(
            "Make the next story longer with more useful story development."
        )

    # --------------------------------------------------------
    # Difficulty / vocabulary
    # --------------------------------------------------------

    difficulty_feedback = str(
        review.get("difficulty_feedback") or ""
    ).strip().lower()

    if difficulty_feedback == "too_difficult":
        instructions.append(
            "Use simple, familiar words and shorter sentences."
        )

    elif difficulty_feedback == "too_easy":
        instructions.append(
            "Use slightly richer vocabulary and a more developed story."
        )

    # --------------------------------------------------------
    # Improvement tags
    # --------------------------------------------------------

    improvement_tags = review.get("improvement_tags") or []

    for tag in improvement_tags:
        tag_lower = str(tag).strip().lower()

        if tag_lower == "funnier":
            instructions.append(
                "Make the story funnier with gentle humor."
            )

        elif tag_lower == "more adventure":
            instructions.append(
                "Add more safe adventure and discovery."
            )

        elif tag_lower == "more animals":
            instructions.append(
                "Include more lovable animal characters."
            )

        elif tag_lower == "less scary":
            instructions.append(
                "Make the story gentler and less scary."
            )

        elif tag_lower == "longer":
            instructions.append(
                "Make the story longer."
            )

        elif tag_lower == "shorter":
            instructions.append(
                "Make the story shorter."
            )

    # --------------------------------------------------------
    # Optional comment
    # --------------------------------------------------------

    comment = str(review.get("comment") or "").strip()

    if comment:
        instructions.append(
            f"Parent comment: {comment}"
        )

    return "\n".join(instructions)


if __name__ == "__main__":
    init_database()
    print("Database ready.")
    print(f"Location: {DB_PATH}")