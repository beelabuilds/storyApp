import os
import sys

# Add project root to sys.path to allow importing from 'ai'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from prompts import build_story_prompt

try:
    from ai.qwen_integration import (
        generate_story_with_qwen,
        suggest_goals_with_qwen,
        is_qwen_available
    )
    HAS_QWEN = True
except (ImportError, ModuleNotFoundError):
    HAS_QWEN = False
    def is_qwen_available(): return False


import random
import uuid

def suggest_goals(age=None, event=None, character=None, language="English") -> list:
    """
    Returns context-grounded goal suggestions.
    Uses Qwen3.5-9B if reachable, otherwise returns smart grounded fallbacks.
    """
    if HAS_QWEN and is_qwen_available():
        try:
            res = suggest_goals_with_qwen(age=age, event=event, character=character, language=language)
            if res:
                return res
        except Exception as e:
            print("Qwen suggest_goals fallback:", e)

    ev = (event or "").lower()
    if any(k in ev for k in ["dark", "night", "sleep", "bed", "shadow"]):
        return ["Feeling safe in the dark", "Overcoming fear of bedtime", "Finding peace at night", "Being brave before sleeping"]
    elif any(k in ev for k in ["swim", "water", "pool", "deep", "drown"]):
        return ["Trying swimming again", "Taking small steps to feel confident", "Learning to feel safe in the water", "Facing the fear with support"]
    elif any(k in ev for k in ["school", "class", "kindergarten", "teacher"]):
        return ["Making new friends", "Feeling confident in class", "Speaking up bravely", "Enjoying school activities"]
    elif any(k in ev for k in ["share", "toy", "fight", "brother", "sister"]):
        return ["Sharing favorite toys", "Taking turns happily", "Showing kindness to siblings", "Playing together cooperatively"]
    elif any(k in ev for k in ["doctor", "dentist", "shot", "hospital", "sick"]):
        return ["Being brave at the doctor", "Understanding health visits", "Staying calm during checkups", "Feeling proud after the visit"]
    elif any(k in ev for k in ["fear", "scare", "afraid", "nervous"]):
        return ["Building inner confidence", "Taking small brave steps", "Learning to feel safe", "Facing challenges with courage"]
    else:
        return ["Building confidence", "Trying something new", "Being kind to others", "Feeling brave and curious"]

def prepare_story_prompt(event, age, goal, character, language, story_seed=None):
    """
    Prepare the prompt that will be sent to the AI model.
    """
    return build_story_prompt(
        event=event,
        age=age,
        goal=goal,
        character=character,
        language=language,
        story_seed=story_seed
    )


def generate_story_locally(
    event: str,
    age: str,
    goal: str,
    character: str,
    language: str,
    story_seed: str = None
) -> dict:
    """
    Diverse offline fallback story engine.

    This is used only when the real Qwen model is unavailable.
    It intentionally varies setting, plot structure, companion,
    conflict, dialogue and resolution so new requests do not all
    follow the same canned story.
    """

    import random
    import uuid
    import re as _re

    seed = story_seed or uuid.uuid4().hex
    rng = random.Random(seed)

    event = (event or "").strip()
    goal = (goal or "").strip()
    character = (character or "").strip()

    hero = character or rng.choice([
        "Milo",
        "Luna",
        "Pip",
        "Nora",
        "Theo",
        "Maya"
    ])

    situation = event or "an unexpected adventure"

    age_text = str(age or "6-8").lower()

    # Try to make the setting fit the user's actual situation.
    lower = situation.lower()

    if any(x in lower for x in ["school", "class", "teacher", "homework"]):
        settings = [
            "a bright classroom just before the morning bell",
            "a busy school courtyard full of chatter",
            "a quiet library at the end of the school hall"
        ]
    elif any(x in lower for x in ["dark", "night", "bed", "sleep", "shadow"]):
        settings = [
            "a moonlit bedroom where shadows danced on the walls",
            "a sleepy garden beneath a silver moon",
            "a quiet house during a windy night"
        ]
    elif any(x in lower for x in ["water", "swim", "pool", "river", "sea"]):
        settings = [
            "the edge of a sparkling blue pool",
            "a peaceful river surrounded by reeds",
            "a sunny beach where tiny waves curled onto the sand"
        ]
    elif any(x in lower for x in ["forest", "bear", "animal", "bunny", "rabbit"]):
        settings = [
            "a forest path beneath tall green trees",
            "a meadow beside the Whispering Woods",
            "a small woodland clearing filled with wildflowers"
        ]
    else:
        settings = [
            "a colorful neighborhood on a breezy afternoon",
            "a hidden garden behind an old wooden gate",
            "a little hill overlooking a sleepy town",
            "a lively park filled with birds and butterflies",
            "a cozy home where an ordinary day was about to become extraordinary"
        ]

    setting = rng.choice(settings)

    companions = [
        ("Coco", "a quick-thinking bunny"),
        ("Pip", "a tiny bird who asked far too many questions"),
        ("Momo", "a cheerful fox with mismatched socks"),
        ("Nibbles", "a nervous mouse with surprisingly brave ideas"),
        ("Tara", "a curious turtle who never rushed"),
        ("Biscuit", "a playful puppy who could find trouble anywhere")
    ]

    companion_name, companion_desc = rng.choice(companions)

    plot_style = rng.choice([
        "mystery",
        "unexpected_friendship",
        "small_quest",
        "mistake_and_recovery",
        "discovery",
        "challenge"
    ])

    sensory = rng.choice([
        "The air smelled like rain and fresh grass.",
        "A warm breeze carried the sound of distant birds.",
        "Somewhere nearby, leaves rustled like quiet applause.",
        "Golden sunlight slipped between the trees in thin bright ribbons.",
        "The evening air felt cool and smelled faintly of flowers."
    ])

    opening_lines = [
        f"{hero} had expected an ordinary day. Instead, {situation}.",
        f"Nothing about the morning suggested an adventure, until {situation}.",
        f"{hero} was in {setting} when something happened that changed the whole day: {situation}.",
        f"It began with one small moment. {situation}. For {hero}, that moment suddenly felt enormous."
    ]

    opening = rng.choice(opening_lines)

    if plot_style == "mystery":
        problem = (
            f"Something about the situation did not make sense. "
            f"{hero} noticed a tiny clue that everyone else had missed. "
            f"Following it led to {companion_name}, {companion_desc}."
        )
        turning = (
            f"Together they followed three strange clues. The last one finally revealed "
            f"that the scary-looking problem was not quite what {hero} had imagined."
        )

    elif plot_style == "unexpected_friendship":
        problem = (
            f"At first, {hero} wanted to handle everything alone. "
            f"Then {companion_name}, {companion_desc}, appeared at exactly the wrong—or perhaps right—moment."
        )
        turning = (
            f"They disagreed about what to do, then discovered that each of them understood "
            f"one part of the problem the other had missed."
        )

    elif plot_style == "small_quest":
        problem = (
            f"To make things right, {hero} needed to reach a place on the other side of {setting}. "
            f"The journey looked simple until a surprising obstacle blocked the way."
        )
        turning = (
            f"{companion_name}, {companion_desc}, suggested an idea so unusual that "
            f"{hero} laughed before realizing it might actually work."
        )

    elif plot_style == "mistake_and_recovery":
        problem = (
            f"{hero} tried to fix the situation quickly—and accidentally made it worse. "
            f"For a moment, everything felt hopeless."
        )
        turning = (
            f"Instead of hiding the mistake, {hero} admitted what happened. "
            f"{companion_name}, {companion_desc}, helped think of a new plan."
        )

    elif plot_style == "discovery":
        problem = (
            f"While trying to understand what to do, {hero} discovered something unexpected nearby. "
            f"It changed the meaning of the whole situation."
        )
        turning = (
            f"{companion_name}, {companion_desc}, helped {hero} look at the problem from another angle."
        )

    else:
        problem = (
            f"The challenge became harder than {hero} expected. "
            f"Walking away would have been easy, but something inside said to try once more."
        )
        turning = (
            f"That was when {companion_name}, {companion_desc}, arrived with a simple idea "
            f"that required courage rather than perfection."
        )

    goal_phrase = goal or rng.choice([
        "being brave even when things feel uncertain",
        "showing kindness",
        "trying again after a mistake",
        "asking for help when it is needed",
        "believing that small steps still count"
    ])

    dialogue_1 = rng.choice([
        f'"I am not sure I can do this," {hero} admitted.',
        f'"What if it goes wrong?" {hero} whispered.',
        f'"I wish this felt easier," said {hero}.',
        f'"Maybe I should just go home," {hero} said quietly.'
    ])

    dialogue_2 = rng.choice([
        f'"You do not have to know everything before you begin," said {companion_name}.',
        f'"We can try one small thing first," {companion_name} replied.',
        f'"Being nervous does not mean you cannot be brave," said {companion_name}.',
        f'"Then we will figure it out together," {companion_name} said with a grin.'
    ])

    climax_options = [
        (
            f"When the hardest moment finally arrived, {hero} remembered {goal_phrase}. "
            f"Instead of rushing, {hero} stopped, looked carefully, and chose one small action."
        ),
        (
            f"The problem suddenly seemed bigger than ever. "
            f"But {hero} remembered everything learned along the way and made a choice no one expected."
        ),
        (
            f"For one long second, {hero} wanted to turn back. "
            f"Then {hero} looked at {companion_name}, took a breath, and stepped forward."
        )
    ]

    climax = rng.choice(climax_options)

    endings = [
        (
            f"The solution was not perfect, but it worked. More importantly, {hero} understood "
            f"that {goal_phrase} could begin with one very small decision."
        ),
        (
            f"By the time the adventure ended, the original problem looked completely different. "
            f"{hero} had not become fearless—just more confident about what to do when fear appeared."
        ),
        (
            f"On the way home, {hero} and {companion_name} laughed about the strangest parts of the day. "
            f"What had begun as a difficult moment had become a story they would remember for a long time."
        ),
        (
            f"That night, {hero} thought about everything that had happened and smiled. "
            f"The best part was not winning or being perfect. It was discovering the courage to keep going."
        )
    ]

    ending = rng.choice(endings)

    if any(x in age_text for x in ["3-5", "4-5", "3", "4", "5"]):
        story = f"""
{opening}

{sensory} {hero} felt a little worried.

{problem}

{dialogue_1}

{dialogue_2}

{turning}

{climax}

{ending}
""".strip()

    elif any(x in age_text for x in ["9-12", "9", "10", "11", "12"]):
        reflection = rng.choice([
            f"{hero} began to realize that courage could exist beside fear rather than replacing it.",
            f"{hero} understood that solving a problem sometimes meant changing the way you looked at it.",
            f"{hero} realized that accepting help was not weakness; it was part of making a good decision."
        ])

        story = f"""
{opening}

{sensory}

{problem}

{dialogue_1}

{dialogue_2}

{reflection}

{turning}

{climax}

For a moment, everything was quiet. Then the situation finally began to change.

{ending}
""".strip()

    else:
        extra = rng.choice([
            f"{companion_name} made a ridiculous face, and even {hero} had to laugh.",
            f"A sudden gust of wind sent leaves spinning around them like tiny dancers.",
            f"For a moment, both friends stood still, listening and thinking."
        ])

        story = f"""
{opening}

{sensory}

{problem}

{dialogue_1}

{dialogue_2}

{extra}

{turning}

{climax}

{ending}
""".strip()

    # Make title vary with both story and situation.
    words = [w.capitalize() for w in _re.findall(r"[A-Za-z]+", situation) if len(w) > 3]
    key_word = rng.choice(words[:8]) if words else rng.choice(["Adventure", "Surprise", "Secret"])

    titles = [
        f"{hero} and the {key_word} Surprise",
        f"The Day {hero} Tried Again",
        f"{hero} and {companion_name}'s Unexpected Adventure",
        f"The Secret of the {key_word}",
        f"{hero}'s Brave Little Step",
        f"When {hero} Met {companion_name}"
    ]

    return {
        "title": rng.choice(titles),
        "story": story,
        "seed": seed,
        "engine": "Diverse-Local-Fallback"
    }



import re

def format_into_short_paragraphs(text: str) -> str:
    """
    Ensures story text has short, bite-sized paragraphs (1-2 sentences max per paragraph),
    creating an engaging, airy, child-friendly reading experience.
    """
    if not text:
        return ""
    
    paragraphs = text.strip().split("\n\n")
    reformatted = []
    
    for para in paragraphs:
        cleaned_para = para.strip()
        if not cleaned_para:
            continue
        
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned_para) if s.strip()]
        
        chunk = []
        for s in sentences:
            chunk.append(s)
            if len(chunk) == 2 or (len(chunk) == 1 and len(s) > 130):
                reformatted.append(" ".join(chunk))
                chunk = []
        if chunk:
            reformatted.append(" ".join(chunk))
                
    return "\n\n".join(reformatted)


def generate_story(event: str, age: str, goal: str, character: str, language: str = "English", story_seed: str = None) -> dict:
    """
    Main entry point for generating stories.
    Tries to use Qwen3.5-9B if reachable (e.g. running via Colab notebook),
    otherwise falls back to customized local story generation.
    """
    if not story_seed:
        story_seed = uuid.uuid4().hex[:12]

    prompt = prepare_story_prompt(event, age, goal, character, language, story_seed=story_seed)
    
    if HAS_QWEN and is_qwen_available():
        try:
            res = generate_story_with_qwen(
                age=age,
                event=event,
                goal=goal,
                character=character,
                language=language
            )
            res["story"] = format_into_short_paragraphs(res.get("story", ""))
            res["prompt"] = prompt
            res["seed"] = story_seed
            return res
        except Exception as e:
            local_res = generate_story_locally(event, age, goal, character, language, story_seed=story_seed)
            local_res["story"] = format_into_short_paragraphs(local_res.get("story", ""))
            local_res["prompt"] = prompt
            local_res["engine"] = f"Template-Fallback (Qwen Error: {str(e)})"
            return local_res
    else:
        local_res = generate_story_locally(event, age, goal, character, language, story_seed=story_seed)
        local_res["story"] = format_into_short_paragraphs(local_res.get("story", ""))
        local_res["prompt"] = prompt
        local_res["engine"] = "Template-Engine"
        return local_res