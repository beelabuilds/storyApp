"""Automated integration tests for multi-turn chat goal preservation and character fidelity."""

import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.main import app


class TestChatGoalPreservation(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch("backend.main.generate_story", new_callable=AsyncMock)
    def test_multi_turn_funnier_preserves_primary_goal(self, mock_gen):
        mock_gen.return_value = {
            "title": "Barnaby the Little Bear and the Dancing Shadows",
            "content": (
                "Once upon a time, Barnaby the Little Bear tucked into his warm mossy bed.\n\n"
                "A shadow danced on the wall. Barnaby wiggled his toes and giggled as the shadow made a bunny ear.\n\n"
                "He realized shadows were just ticklish friends dancing in the moonlight."
            ),
            "character": "Barnaby the Little Bear",
            "engine": "Qwen Local GGUF",
            "is_fallback": False,
        }

        # Multi-turn conversation: Turn 1 parent describes fear, Turn 2 clicks "Make it funnier"
        payload = {
            "messages": [
                {"role": "user", "content": "Leo is 5 and afraid of the dark and strange shadows in his bedroom"},
                {"role": "assistant", "content": "Here is a story about Barnaby..."},
                {"role": "user", "content": "Make it funnier"}
            ],
            "storyContext": {"age": "4-5", "hero": "Barnaby the Little Bear"}
        }

        response = self.client.post("/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check call arguments to generate_story
        mock_gen.assert_called_once()
        kwargs = mock_gen.call_args.kwargs

        # PRIMARY GOAL must be preserved as description!
        self.assertEqual(kwargs["description"], "Leo is 5 and afraid of the dark and strange shadows in his bedroom")
        self.assertIn("Make the story funnier", kwargs["feedback_prompt"])
        self.assertIn("giggles", kwargs["feedback_prompt"])

        # Character must be returned in response and storyContext
        self.assertEqual(data["story"]["character"], "Barnaby the Little Bear")
        self.assertEqual(data["storyContext"]["hero"], "Barnaby the Little Bear")
        self.assertIn("Barnaby", data["assistantMessage"])

        print("[PASS] Test passed: 'Make it funnier' successfully preserved primary goal and attached modifier.")

    @patch("backend.main.generate_story", new_callable=AsyncMock)
    def test_multi_turn_longer_preserves_primary_goal_and_increases_tokens(self, mock_gen):
        mock_gen.return_value = {
            "title": "Barnaby's Moonlit Journey",
            "content": "A longer bedtime story about overcoming fear...",
            "character": "Barnaby the Little Bear",
            "engine": "Qwen Local GGUF",
            "is_fallback": False,
        }

        payload = {
            "messages": [
                {"role": "user", "content": "My child is nervous about nighttime sounds in their room"},
                {"role": "assistant", "content": "Story here..."},
                {"role": "user", "content": "Make it longer"}
            ],
            "storyContext": {"age": "4-5"}
        }

        response = self.client.post("/chat", json=payload)
        self.assertEqual(response.status_code, 200)

        kwargs = mock_gen.call_args.kwargs
        # Must preserve description
        self.assertEqual(kwargs["description"], "My child is nervous about nighttime sounds in their room")
        # Must increase max_tokens for longer story
        self.assertEqual(kwargs["max_tokens"], 850)
        self.assertIn("Make the story longer", kwargs["feedback_prompt"])

        print("[PASS] Test passed: 'Make it longer' preserved primary goal and allocated 850 tokens.")


if __name__ == "__main__":
    unittest.main()
