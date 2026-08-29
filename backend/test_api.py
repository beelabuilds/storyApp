
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_endpoints():
    # 1. Test root endpoint
    res = client.get("/")
    assert res.status_code == 200, f"Root endpoint failed: {res.status_code}"
    print(f"PASS: Root endpoint -> {res.json()}")

    # 2. Test test matrix of story generations
    test_cases = [
        {
            "name": "Dark theme (3-5)",
            "payload": {
                "age": "3-5",
                "event": "Scared of the dark at bedtime",
                "goal": "Being brave and peaceful",
                "character": "Leo",
                "language": "English"
            }
        },
        {
            "name": "School theme (6-8)",
            "payload": {
                "age": "6-8",
                "event": "First day of school",
                "goal": "Making new friends",
                "character": "Emma",
                "language": "English"
            }
        },
        {
            "name": "Tooth theme (9-12)",
            "payload": {
                "age": "9-12",
                "event": "Lost a tooth",
                "goal": "Accepting growing up",
                "character": "Sam",
                "language": "English"
            }
        },
        {
            "name": "Sharing theme (6-8)",
            "payload": {
                "age": "6-8",
                "event": "Sharing toys with brother",
                "goal": "Kindness and sharing",
                "character": "Maya",
                "language": "English"
            }
        },
        {
            "name": "General fallback theme (3-5)",
            "payload": {
                "age": "3-5",
                "event": "Visiting a museum",
                "goal": "Curiosity and patience",
                "character": "Oliver",
                "language": "English"
            }
        },
        {
            "name": "Empty string fields test",
            "payload": {
                "age": "",
                "event": "",
                "goal": "",
                "character": "",
                "language": ""
            }
        }
    ]

    for tc in test_cases:
        r = client.post("/generate-story", json=tc["payload"])
        assert r.status_code == 200, f"Failed test case '{tc['name']}': status {r.status_code}"
        data = r.json()
        assert "title" in data and len(data["title"]) > 0, f"Missing title in '{tc['name']}'"
        assert "story" in data and len(data["story"]) > 0, f"Missing story in '{tc['name']}'"
        print(f"PASS: {tc['name']} -> Title: '{data['title']}' | Engine: '{data.get('engine')}'")

    print("\nALL BACKEND TESTS PASSED WITH 0 ERRORS!")

if __name__ == "__main__":
    test_endpoints()
