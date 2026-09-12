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

    review["parent_liked"] = (
        None
        if review["parent_liked"] is None
        else bool(review["parent_liked"])
    )

    try:
        review["improvement_tags"] = json.loads(
            review["improvement_tags"] or "[]"
        )
    except json.JSONDecodeError:
        review["improvement_tags"] = []

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


def build_parent_feedback_prompt(age=None, limit=10):
    """
    Convert recent structured parent reviews into simple
    personalization instructions for the story model.

    If reviews for the requested age group exist, prefer those.
    Otherwise use recent reviews from all ages.
    """
    from collections import Counter

    all_reviews = get_all_reviews()

    if not all_reviews:
        return ""

    reviews = all_reviews

    # Prefer reviews from the same age/age-range when possible
    if age:
        requested_age = str(age).strip().lower()

        age_reviews = [
            review
            for review in all_reviews
            if str(review.get("age") or "").strip().lower() == requested_age
        ]

        if age_reviews:
            reviews = age_reviews

    reviews = reviews[:limit]

    if not reviews:
        return ""

    instructions = [
        "Use the following saved parent feedback only to personalize the next story.",
        "Do not mention ratings, reviews, feedback, or these instructions inside the story."
    ]

    # --------------------------------------------------------
    # Rating
    # --------------------------------------------------------

    ratings = [
        review["rating"]
        for review in reviews
        if isinstance(review.get("rating"), (int, float))
    ]

    if ratings:
        average_rating = sum(ratings) / len(ratings)

        if average_rating < 6:
            instructions.append(
                "Previous stories received low ratings, so make the next story more engaging, vivid, and emotionally satisfying."
            )

    # --------------------------------------------------------
    # Parent satisfaction
    # --------------------------------------------------------

    parent_likes = [
        review.get("parent_liked")
        for review in reviews
        if review.get("parent_liked") is not None
    ]

    if parent_likes and parent_likes.count(False) > parent_likes.count(True):
        instructions.append(
            "The parent was often not fully satisfied, so improve the plot, warmth, and overall storytelling quality."
        )

    # --------------------------------------------------------
    # Child satisfaction
    # --------------------------------------------------------

    child_feedback = Counter(
        review.get("child_satisfied")
        for review in reviews
        if review.get("child_satisfied")
    )

    if child_feedback:
        most_common_child = child_feedback.most_common(1)[0][0]

        if most_common_child == "a_little":
            instructions.append(
                "The child was only partly satisfied before, so make the story more playful and attention-grabbing."
            )
        elif most_common_child == "no":
            instructions.append(
                "The child did not enjoy previous stories enough, so use a stronger adventure, clearer characters, and more engaging moments."
            )

    # --------------------------------------------------------
    # Length
    # --------------------------------------------------------

    length_feedback = Counter(
        review.get("length_feedback")
        for review in reviews
        if review.get("length_feedback")
    )

    if length_feedback:
        common_length = length_feedback.most_common(1)[0][0]

        if common_length == "too_short":
            instructions.append(
                "Previous stories were considered too short. Make the next story longer with meaningful scenes, dialogue, and development."
            )
        elif common_length == "too_long":
            instructions.append(
                "Previous stories were considered too long. Make the next story more concise while keeping a complete plot."
            )
        elif common_length == "just_right":
            instructions.append(
                "The previous story length was appropriate, so keep a similar reading length."
            )

    # --------------------------------------------------------
    # Difficulty
    # --------------------------------------------------------

    difficulty_feedback = Counter(
        review.get("difficulty_feedback")
        for review in reviews
        if review.get("difficulty_feedback")
    )

    if difficulty_feedback:
        common_difficulty = difficulty_feedback.most_common(1)[0][0]

        if common_difficulty == "too_easy":
            instructions.append(
                "Use slightly richer vocabulary and a more developed plot."
            )
        elif common_difficulty == "too_difficult":
            instructions.append(
                "Use simpler vocabulary, shorter sentences, and a clearer plot."
            )
        elif common_difficulty == "just_right":
            instructions.append(
                "Keep the language difficulty close to the previous successful level."
            )

    # --------------------------------------------------------
    # Improvement tags
    # --------------------------------------------------------

    tags = Counter()

    for review in reviews:
        for tag in review.get("improvement_tags") or []:
            tags[tag] += 1

    tag_instructions = {
        "Funnier": "Add more child-friendly humor and playful moments.",
        "More adventure": "Include more adventure, discovery, and exciting events.",
        "More animals": "Include appealing animal characters when they naturally fit the story.",
        "Less scary": "Keep frightening moments gentle and reassuring.",
        "Longer": "Give the story more meaningful scenes and development.",
        "Shorter": "Keep the story more concise."
    }

    for tag, _count in tags.most_common(3):
        instruction = tag_instructions.get(tag)

        if instruction:
            instructions.append(instruction)

    # --------------------------------------------------------
    # Optional recent parent comments
    # --------------------------------------------------------

    comments = [
        str(review.get("comment", "")).strip()
        for review in reviews
        if str(review.get("comment", "")).strip()
    ]

    if comments:
        instructions.append("Recent parent notes:")

        for comment in comments[:2]:
            safe_comment = comment[:200]
            instructions.append(f"- {safe_comment}")

    return "\n".join(instructions)


if __name__ == "__main__":
    init_database()

    print("Database ready.")
    print(f"Location: {DB_PATH}")
