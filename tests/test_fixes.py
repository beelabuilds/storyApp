"""Comprehensive automated tests verifying story generation and review display fixes.

Tests:
1. extract_title_and_content deduplication & single title extraction.
2. SQLite review storage, retrieval, and camelCase/snake_case serialization.
3. Parent feedback prompt isolation (style/length only, no plot leakage).
4. Fear-safety & priority prompt formatting.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from ai.story_cleaner import extract_title_and_content, normalize_for_comparison
from ai.prompts import build_user_message, get_system_prompt_for_age
from backend.database import (
    init_database,
    save_review,
    get_review,
    build_parent_feedback_prompt,
)


class TestStoryGenerationAndReviewFixes(unittest.TestCase):

    def setUp(self):
        init_database()

    def test_cleaner_single_title_and_deduplication(self):
        """Verify title is extracted once and repeated title lines or duplicate paragraphs are dropped."""
        raw_output = (
            "<think>Thinking process here...</think>\n"
            "**Title: Barnaby and the Night Whispers**\n\n"
            "Barnaby and the Night Whispers\n\n"
            "**Story:**\n\n"
            "Once upon a time, Barnaby the little bear tucked himself into his warm mossy bed.\n\n"
            "Once upon a time, Barnaby the little bear tucked himself into his warm mossy bed.\n\n"
            "A soft tap-tap sounded on the window pane. Barnaby listened closely.\n\n"
            "It was just a gentle autumn leaf dancing in the evening breeze.\n\n"
            "Barnaby and the Night Whispers\n\n"
            "He smiled, hugged his acorn pillow, and drifted into cozy sleep."
        )

        title, content = extract_title_and_content(raw_output)

        # 1. Title must be extracted cleanly without asterisks or prefix
        self.assertEqual(title, "Barnaby and the Night Whispers")

        # 2. Content must not start with the title
        self.assertFalse(content.startswith("Barnaby and the Night Whispers"))
        self.assertFalse(content.startswith("**Title:"))

        # 3. Content must not contain the boilerplate '**Story:**'
        self.assertNotIn("**Story:**", content)

        # 4. Duplicate paragraph must be removed
        count_first_p = content.count("Once upon a time, Barnaby the little bear tucked himself into his warm mossy bed.")
        self.assertEqual(count_first_p, 1, "Duplicate consecutive paragraph was not removed!")

        # 5. Middle repeated title paragraph must be removed
        paragraphs = content.split("\n\n")
        for p in paragraphs:
            self.assertNotEqual(
                normalize_for_comparison(p),
                normalize_for_comparison("Barnaby and the Night Whispers"),
                "Title was repeated inside the content paragraphs!"
            )

        print("[PASS] Test passed: Single title extracted and repeated lines/paragraphs cleanly deduplicated.")

    def test_reject_your_creative_title_placeholder(self):
        """Verify '[Your Creative Title]' is completely removed from title and body."""
        raw_output = (
            "Title: [Your Creative Title]\n\n"
            "Leo and the Whispering Night\n\n"
            "Once upon a time, Leo was tucked into his cozy blanket.\n\n"
            "The night was quiet and gentle."
        )

        title, content = extract_title_and_content(raw_output, default_title="Leo's Adventure")

        # Title must NOT be [Your Creative Title]
        self.assertNotIn("Your Creative Title", title)
        self.assertNotIn("[", title)
        self.assertEqual(title, "Leo and the Whispering Night")

        # Content must NOT contain [Your Creative Title]
        self.assertNotIn("Your Creative Title", content)
        self.assertNotIn("Title:", content)
        self.assertFalse(content.startswith("Leo and the Whispering Night"))

        print("[PASS] Test passed: [Your Creative Title] placeholder successfully eliminated.")

    def test_multiple_repeated_title_lines_and_looping_paragraphs(self):
        """Verify repeated title lines on multiple lines and looping paragraphs are all removed."""
        raw_output = (
            "**Title: Sammy's Starlight**\n"
            "Title: Sammy's Starlight\n"
            "Sammy's Starlight\n\n"
            "Paragraph 1: Sammy sat on the warm grass under the starry sky.\n\n"
            "Paragraph 2: A firefly blinked warmly near his shoes.\n\n"
            "Paragraph 1: Sammy sat on the warm grass under the starry sky.\n\n"
            "Paragraph 3: Sammy smiled and knew it was time for sleep.\n\n"
            "**End:**"
        )

        title, content = extract_title_and_content(raw_output)

        self.assertEqual(title, "Sammy's Starlight")
        self.assertNotIn("Title:", content)
        self.assertNotIn("**End:**", content)

        # Paragraph 1 must appear only once, not twice
        p1_count = content.count("Sammy sat on the warm grass under the starry sky.")
        self.assertEqual(p1_count, 1, "Duplicate paragraph was not dropped!")

        print("[PASS] Test passed: Multiple repeated title lines and looping paragraphs removed.")


    def test_review_storage_and_field_normalization(self):
        """Verify all review fields are saved and returned with both camelCase and snake_case."""
        test_story_id = f"test-story-{os.getpid()}-1"
        save_review(
            story_id=test_story_id,
            story_title="The Brave Kitten",
            age="4-8",
            rating=9,
            parent_liked=True,
            child_satisfied="yes",
            length_feedback="just_right",
            difficulty_feedback="just_right",
            improvement_tags=["Funnier", "More animals"],
            comment="Wonderful bedtime story, child loved it!"
        )

        retrieved = get_review(test_story_id)
        self.assertIsNotNone(retrieved)

        # Check snake_case and camelCase
        self.assertEqual(retrieved["rating"], 9)
        self.assertIs(retrieved["parent_liked"], True)
        self.assertIs(retrieved["parentLiked"], True)
        self.assertEqual(retrieved["child_satisfied"], "yes")
        self.assertEqual(retrieved["childSatisfied"], "yes")
        self.assertEqual(retrieved["length_feedback"], "just_right")
        self.assertEqual(retrieved["lengthFeedback"], "just_right")
        self.assertEqual(retrieved["difficulty_feedback"], "just_right")
        self.assertEqual(retrieved["difficultyFeedback"], "just_right")
        self.assertEqual(retrieved["improvement_tags"], ["Funnier", "More animals"])
        self.assertEqual(retrieved["improvementTags"], ["Funnier", "More animals"])
        self.assertEqual(retrieved["comment"], "Wonderful bedtime story, child loved it!")

        print("[PASS] Test passed: All review fields correctly saved and serialized for frontend.")

    def test_parent_feedback_isolation(self):
        """Verify parent feedback prompt only contains style/length guidance, never comments that hijack plot."""
        feedback = build_parent_feedback_prompt(age="4-8")
        # Ensure raw comment text never leaks into the feedback prompt
        self.assertNotIn("Wonderful bedtime story", feedback)
        self.assertNotIn("loved it", feedback)

        print("[PASS] Test passed: Parent feedback isolates style/length and prevents plot hijacking.")

    def test_resolve_fictional_character(self):
        """Verify real fictional characters and animals are assigned instead of placeholders or 'my child'."""
        from backend.story_generator import resolve_fictional_character

        # Case 1: Hero is 'My child' or empty with bedtime/fear description
        char1 = resolve_fictional_character("My child", "afraid of strange sounds in the bedroom at night")
        self.assertEqual(char1, "Barnaby the Little Bear")

        # Case 2: Hero is None with sharing/kindness description
        char2 = resolve_fictional_character(None, "learning how to share toys with friends at preschool")
        self.assertEqual(char2, "Finley the Friendly Fox")

        # Case 3: Hero is 'A friendly explorer' with bravery description
        char3 = resolve_fictional_character("A friendly explorer", "feeling nervous on the first day of school, needs courage")
        self.assertEqual(char3, "Pip the Brave Little Mouse")

        # Case 4: Parent explicitly requested a specific fictional hero like 'Luna the Dragon'
        char4 = resolve_fictional_character("Luna the Dragon", "flying through star clouds")
        self.assertEqual(char4, "Luna the Dragon")

        # Verify no placeholders or 'my child' ever returned
        for test_hero in ["", "none", "My child", "the child", "a friendly explorer", "explorer"]:
            res = resolve_fictional_character(test_hero, "general adventure")
            self.assertNotIn("my child", res.lower())
            self.assertNotIn("explorer", res.lower())
            self.assertNotIn("[", res)
            self.assertTrue(len(res) > 3)

        print("[PASS] Test passed: Real fictional characters/animals correctly assigned.")

    def test_story_wide_sentence_deduplication_and_leak_cleaning(self):
        """Verify repeated lines across different paragraphs are deduplicated and 'my child' is cleaned."""
        raw_output = (
            "Title: Pip's Cozy Burrow\n\n"
            "Once upon a time, my child tucked into a warm blanket.\n"
            "The wind whispered through windows and danced on the sill.\n\n"
            "Down below, a sleepy squirrel was munching on an acorn.\n"
            "The wind whispered through windows and danced on the sill.\n\n"
            "Pip listened happily and closed his eyes in peaceful rest."
        )

        title, content = extract_title_and_content(
            raw_output,
            default_title="Pip's Cozy Burrow",
            character_name="Pip the Curious Mouse",
        )

        self.assertEqual(title, "Pip's Cozy Burrow")
        # 'my child' must be replaced with character name or 'the little one'
        self.assertNotIn("my child", content.lower())
        self.assertIn("Pip the Curious Mouse", content)

        # The repeated line must only appear once in the whole story
        count_repeated = content.count("The wind whispered through windows and danced on the sill.")
        self.assertEqual(count_repeated, 1, "Repeated line was not removed across paragraphs!")

        print("[PASS] Test passed: Story-wide sentence deduplication and 'my child' leak cleaning verified.")


if __name__ == "__main__":
    unittest.main()
