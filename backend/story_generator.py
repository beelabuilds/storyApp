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



def _story_style_for_age(age):
    """Story length and reading time based on exact child age."""
    import re

    match = re.search(r"\d+", str(age or "6"))
    child_age = int(match.group()) if match else 6

    if child_age <= 4:
        return {
            "age": 4,
            "min_words": 300,
            "max_words": 400,
            "reading_time": "3–4 min",
            "scene_count": 5
        }

    if child_age == 5:
        return {
            "age": 5,
            "min_words": 400,
            "max_words": 550,
            "reading_time": "4–5 min",
            "scene_count": 6
        }

    if child_age == 6:
        return {
            "age": 6,
            "min_words": 550,
            "max_words": 700,
            "reading_time": "5–7 min",
            "scene_count": 7
        }

    if child_age == 7:
        return {
            "age": 7,
            "min_words": 700,
            "max_words": 850,
            "reading_time": "7–9 min",
            "scene_count": 8
        }

    return {
        "age": 8,
        "min_words": 850,
        "max_words": 1050,
        "reading_time": "9–11 min",
        "scene_count": 10
    }


def _cute_animal_description(animal):
    """
    Turn plain animal words into warmer child-friendly descriptions.
    """
    descriptions = {
        "cat": [
            "a tiny fluffy white kitten with soft pink paws",
            "a round little ginger kitten with bright curious eyes",
            "a silky gray kitten with a tail that curled like a question mark"
        ],
        "dog": [
            "a bouncy little puppy with floppy ears",
            "a fluffy golden puppy with a wagging tail",
            "a tiny brown puppy with shiny button-like eyes"
        ],
        "rabbit": [
            "a soft white bunny with long velvety ears",
            "a tiny round bunny with a twitchy pink nose",
            "a fluffy cream-colored bunny with bright little eyes"
        ],
        "bunny": [
            "a soft white bunny with long velvety ears",
            "a tiny round bunny with a twitchy pink nose",
            "a fluffy cream-colored bunny with bright little eyes"
        ],
        "bear": [
            "a big round brown bear with sleepy gentle eyes",
            "a soft-looking bear with chocolate-brown fur",
            "a chubby little bear with warm brown paws"
        ],
        "chicken": [
            "a small golden chicken with soft feathery wings",
            "a brave little chicken with bright yellow feathers",
            "a tiny fluffy chicken with quick little feet"
        ],
        "fox": [
            "a clever little fox with a bright orange tail",
            "a small red fox with shiny curious eyes",
            "a fluffy fox whose tail looked like a warm orange cloud"
        ],
        "dragon": [
            "a tiny round dragon with shiny green scales",
            "a baby dragon with soft purple wings and a warm little nose",
            "a small blue dragon with sparkling scales and enormous curious eyes"
        ]
    }

    import random
    key = str(animal or "").lower().strip()

    for animal_name, options in descriptions.items():
        if animal_name in key:
            return random.choice(options)

    return animal



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

    age_text = str(age or "6").lower()
    style = _story_style_for_age(age)
    child_age = style["age"]
    min_words = style["min_words"]
    max_words = style["max_words"]

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
        ("Coco", "a tiny fluffy white bunny with long velvety ears and a twitchy pink nose"),
        ("Pip", "a tiny sky-blue bird with soft feathers who asked far too many questions"),
        ("Momo", "a cheerful little orange fox with a huge fluffy tail and mismatched socks"),
        ("Nibbles", "a small round mouse with silky gray fur and surprisingly brave ideas"),
        ("Tara", "a gentle green turtle with shiny eyes who never rushed"),
        ("Biscuit", "a bouncy golden puppy with floppy ears and a tail that never stopped wagging")
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
        "The air smelled like fresh grass and sweet little flowers, while tiny birds chirped above.",
        "A warm breeze tickled the leaves, making them whisper softly to one another.",
        "Golden sunlight danced between the trees like tiny sparkling ribbons.",
        "The evening sky turned soft pink and purple while crickets began their quiet song.",
        "A cool breeze brushed past, carrying the smell of flowers and the soft rustle of leaves.",
        "Little drops of rain glittered on the grass like hundreds of tiny diamonds.",
        "The moon looked like a silver cookie hanging high in the dark blue sky."
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
        f'"You do not have to know everything before you begin," said {companion_name}, smiling warmly.',
        f'"We can try one teeny-tiny step first," {companion_name} said, wiggling happily.',
        f'"Being nervous does not mean you cannot be brave," whispered {companion_name}.',
        f'"Then we will figure it out together!" {companion_name} said with a huge grin.',
        f'"Come on," {companion_name} giggled. "Adventures are much nicer with a friend."'
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

    playful_moments = [
        f"{companion_name} suddenly sneezed so loudly that three tiny leaves jumped off a branch. "
        f"{hero} blinked, then burst into laughter.",

        f"A butterfly landed right on {companion_name}'s nose. "
        f"{companion_name} crossed their eyes trying to look at it, which made {hero} giggle.",

        f"They heard a tiny rustle nearby. For one nervous second they froze—"
        f"but it was only a round little beetle pushing a leaf twice its own size.",

        f"{companion_name} tried to whisper a serious plan, but their tummy made a loud 'GROOOOWL!' "
        f"They both laughed so hard they almost forgot to be worried."
    ]

    magical_moments = [
        "Tiny fireflies blinked around them like floating golden stars.",
        "A row of little mushrooms shimmered softly beside the path.",
        "A feather drifted slowly from the sky and landed perfectly on the hero's head.",
        "For just a moment, the clouds opened and a warm beam of sunlight followed them."
    ]

    playful_moment = rng.choice(playful_moments)
    magical_moment = rng.choice(magical_moments)

    if child_age <= 4:
        story = f"""
{opening}

{sensory}

{hero} felt a little worried.

{problem}

{dialogue_1}

{dialogue_2}

{turning}

{climax}

{ending}
""".strip()

    elif child_age == 5:
        story = f"""
{opening}

{sensory}

{problem}

{dialogue_1}

{dialogue_2}

{playful_moment}

{turning}

{climax}

{ending}
""".strip()

    elif child_age == 6:
        story = f"""
{opening}

{sensory}

{problem}

{dialogue_1}

{dialogue_2}

{playful_moment}

{turning}

{magical_moment}

{climax}

{ending}
""".strip()

    elif child_age == 7:
        reflection = rng.choice([
            f"{hero} realized that feeling nervous did not make anyone weak.",
            f"{hero} began to understand that brave choices could start with very small steps.",
            f"{hero} discovered that adventures felt less frightening when shared with a kind friend."
        ])

        story = f"""
{opening}

{sensory}

{problem}

{dialogue_1}

{dialogue_2}

{playful_moment}

{reflection}

{turning}

{magical_moment}

{climax}

For a moment, everything became wonderfully quiet.

{ending}
""".strip()

    else:
        reflection = rng.choice([
            f"{hero} realized that courage was not the absence of fear; it was deciding what to do while fear was still there.",
            f"{hero} began to see that the hardest problems sometimes looked different when viewed with curiosity instead of panic.",
            f"{hero} discovered that accepting help could be its own kind of strength."
        ])

        second_dialogue = rng.choice([
            f'"Wait," said {hero}. "I think I finally understand what we need to do."',
            f'"I have an idea," {hero} whispered. "It might be a little strange, though."',
            f'"Maybe we have been looking at this the wrong way," said {hero}.'
        ])

        story = f"""
{opening}

{sensory}

{problem}

{dialogue_1}

{dialogue_2}

{playful_moment}

{reflection}

{turning}

{magical_moment}

{second_dialogue}

{climax}

For a few heartbeats, nobody spoke. Then the answer became clear.

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