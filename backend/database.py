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


if __name__ == "__main__":
    init_database()

    print("Database ready.")
    print(f"Location: {DB_PATH}")
