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


def generate_story_locally(event: str, age: str, goal: str, character: str, language: str, story_seed: str = None) -> dict:
    """
    Generates a high-quality, customized children's story locally.
    Tailors the text based on age, event, goal, character, and ensures originality through dynamic seeds.
    """
    char_name = character.strip() or "A curious little adventurer"
    clean_event = event.strip() or "A brand new day of discovery"
    ev_lower = clean_event.lower()
    goal_lower = (goal or "").lower()
    
    # Determine goal phrasing
    if any(k in goal_lower for k in ["brave", "fear", "dark", "courage"]):
        goal_label = "being brave and believing in yourself"
        action_phrase = f"{char_name} took a deep breath and stood tall"
    elif any(k in goal_lower for k in ["share", "toy", "friend", "kind"]):
        goal_label = "kindness and the magic of sharing"
        action_phrase = f"{char_name} offered a warm smile and opened their hands to share"
    elif any(k in goal_lower for k in ["patient", "wait", "calm"]):
        goal_label = "patience and staying calm"
        action_phrase = f"{char_name} counted to three softly and waited with a calm heart"
    elif any(k in goal_lower for k in ["listen", "focus", "learn", "school"]):
        goal_label = "listening carefully and learning new things"
        action_phrase = f"{char_name} listened with curious eyes and an open mind"
    else:
        goal_label = goal.strip() if goal else "friendship, curiosity, and joy"
        action_phrase = f"{char_name} showed great heart and determination"

    # Seeded random generator for reproducible variety
    rng = random.Random(story_seed if story_seed else uuid.uuid4().hex)

    # Dynamic settings & companions
    settings = [
        "a sun-drenched garden filled with whispering blossoms",
        "a cheerful cozy home tucked under gentle hills",
        "a bustling neighborhood full of playful breezes",
        "a colorful playground painted with warm afternoon light",
        "a magical little corner where exciting ideas grow"
    ]
    setting = rng.choice(settings)

    # Dynamic titles
    title_templates = [
        f"{char_name} and the Day of {clean_event.title()[:30]}",
        f"{char_name}'s Big Surprise",
        f"The Adventure of {char_name}",
        f"{char_name} Finds the Way",
        f"{char_name}'s Bright Heart"
    ]
    title = rng.choice(title_templates)

    # 4-5 Years (Simple, sensory, rhythmic, comforting: 300–450 words / 3–5 min read)
    if any(k in age for k in ["4-5", "3-5", "4", "5", "preschool", "kindergarten", "toddler"]):
        intro_pool = [
            (
                f"Once upon a time, in {setting}, lived {char_name}. "
                f"{char_name} had soft, cuddly paws, bright curious eyes, and loved warm fuzzy blankets, sweet honey snacks, and giggling with friends. "
                f"The sun was beginning to dip below the treetops, painting the sky in lovely shades of peach and lavender. "
                f"Everything around the cozy house was quiet and calm, but today brought a brand new moment to explore: {clean_event}. "
                f"{char_name} stood near the soft rug and looked around with a little flutter in the tummy. "
                f"'I wonder what will happen now,' {char_name} whispered softly."
            ),
            (
                f"In a cozy corner of {setting}, {char_name} was having a very special day. "
                f"With bouncy little steps and a happy little tail wag, {char_name} loved chasing dandelion puffs and listening to the evening crickets. "
                f"As the shadows grew longer and bedtime came closer, it was time to experience {clean_event}. "
                f"{char_name} paused by the bedroom door, clutching a favorite plush toy. "
                f"The room felt very quiet, and {char_name}'s heart went pitter-patter like gentle raindrops on a windowpane."
            )
        ]
        scene2_pool = [
            (
                f"At first, {char_name} stopped and held on tight. "
                f"Facing {clean_event} felt a little new and a little mysterious. "
                f"A gentle voice came from nearby: 'It is okay to feel a little unsure, little one. We can take this one gentle step at a time.' "
                f"{char_name} took a slow, deep breath in—smelling fresh pine and cozy lavender—and let it out like blowing soft bubbles. "
                f"Whoosh! The funny flutter in the tummy began to calm down. "
                f"'I can try,' {char_name} said in a sweet, steady voice. 'I want to practice {goal_label}.'"
            ),
            (
                f"Looking closely at the room, {char_name} noticed the warm nightlight glowing like a friendly little star. "
                f"Even though {clean_event} had seemed big and scary a moment ago, {char_name} remembered the magic of {goal_label}. "
                f"'When I feel nervous, I can count my breath,' {char_name} thought. "
                f"One, two, three. In went the calm, and out went the worry. "
                f"{action_phrase}. With each small step forward, the space felt much warmer and safer."
            )
        ]
        scene3_pool = [
            (
                f"Step by step, {char_name} discovered that everything was friendly and safe. "
                f"The shapes on the wall were just gentle tree branches waving hello in the moonlight. "
                f"By focusing on {goal_label}, {char_name} felt strong and capable inside. "
                f"{action_phrase}. A big, joyful smile lit up {char_name}'s face, and all the previous hesitation melted away into pure happiness."
            ),
            (
                f"With newfound courage, {char_name} hopped right into the middle of the moment. "
                f"Putting {goal_label} into action made the whole world feel brighter. "
                f"{char_name} discovered that doing something new is just like opening a wonderful storybook—the first page might be a surprise, but it leads to something magical."
            )
        ]
        ending_pool = [
            (
                f"Hooray! {char_name} did it! A warm, proud glow filled {char_name}'s chest. "
                f"Snuggled up safe and sound under a fluffy cloud blanket, {char_name} gave the plush toy a gentle hug. "
                f"'I was so brave today,' {char_name} murmured happily with heavy eyelids. "
                f"Outside, the moon watched over {setting}, and {char_name} drifted off into sweet, peaceful dreams, proud of {goal_label}."
            ),
            (
                f"With a happy little yawn and a cozy stretch, {char_name} knew that everything was safe, peaceful, and full of love. "
                f"Facing {clean_event} had shown {char_name} just how special {goal_label} really is. "
                f"Tucked in warmly with a calm heart and a smiling face, {char_name} closed both eyes and welcomed a night full of happy adventures in dreamland."
            )
        ]

        intro = rng.choice(intro_pool)
        scene2 = rng.choice(scene2_pool)
        scene3 = rng.choice(scene3_pool)
        ending = rng.choice(ending_pool)
        story_body = f"{intro}\n\n{scene2}\n\n{scene3}\n\n{ending}"

        return {
            "title": title,
            "story": story_body,
            "seed": story_seed
        }

    # 6-8 Years (Relatable challenges, dialogue, gentle humor, early elementary: 500–750 words / 5–8 min read)
    elif any(k in age for k in ["6-8", "6", "7", "8", "school"]):
        intro_pool = [
            (
                f"The sun was just rising over {setting}, casting long golden rays through the tall trees. "
                f"{char_name} was carefully packing a favorite backpack with curious little notebooks, a smooth lucky pebble, and a heart full of excitement. "
                f"Today, however, was no ordinary morning. An important event was about to unfold: {clean_event}.\n\n"
                f"As the clock on the wall ticked closer, {char_name} felt a familiar fluttering sensation in the chest. "
                f"'I really want everything to go well today,' {char_name} murmured softly while adjusting the backpack straps. "
                f"Outside the window, a gentle breeze rustled the leaves, whispering words of encouragement into the morning air."
            ),
            (
                f"In the cheerful, bustling heart of {setting}, {char_name} was known by friends for having a quick imagination, boundless curiosity, and a kind heart. "
                f"Yet today presented a unique new adventure that brought a sudden wave of nervous excitement: {clean_event}.\n\n"
                f"Standing near the front door, {char_name} looked out at the winding path leading ahead. "
                f"'This feels much bigger and newer than what I usually do,' {char_name} thought, pausing for a moment on the porch. "
                f"Taking a deep breath of the fresh morning air, {char_name} decided to take the very first step forward."
            )
        ]
        scene2_pool = [
            (
                f"When {char_name} arrived at the center of the action, the surrounding sounds were buzzing with lively chatter and cheerful music. "
                f"Groups of friends were laughing together, and everyone seemed to know exactly what to do, but the reality of {clean_event} made {char_name} hesitate at the doorway.\n\n"
                f"A friendly companion walked over, noticing the hesitation, and asked with a warm, welcoming smile, 'Are you ready for today's big moment?'\n\n"
                f"{char_name} took a steady breath, looked down at sticky paws, and replied honestly, 'It feels a little scary, and my tummy feels like it is doing somersaults. But I really want to try.'\n\n"
                f"'That is completely normal,' the friend encouraged kindly. 'Every great explorer feels those butterflies. Taking the first step together is always where the real magic begins.'"
            ),
            (
                f"Stepping into the bright room, {char_name} noticed how quickly everything was moving around {clean_event}. "
                f"For a brief second, the temptation to step back into the hallway and wait where it felt quiet and safe was very strong.\n\n"
                f"Then {char_name} remembered the power and promise of {goal_label}. "
                f"'If I don't try now, I will always wonder what could have happened,' {char_name} thought with growing resolve.\n\n"
                f"Looking up with determination in bright eyes, {char_name} said, 'I can take this one small step at a time.' "
                f"{action_phrase}, and the initial hesitation began transforming into vibrant, curious energy."
            )
        ]
        scene3_pool = [
            (
                f"Right when the challenge reached its most interesting moment, quick thinking and true character were needed. "
                f"An unexpected obstacle popped up right in the middle of {clean_event}, catching almost everyone off guard.\n\n"
                f"Instead of panicking or giving up, {char_name} paused, observed the situation carefully, and remembered: {goal_label}. "
                f"{action_phrase}.\n\n"
                f"With patience, active listening, and a creative spark, {char_name} suggested a clever idea that nobody else had thought of. "
                f"What had seemed complicated and intimidating just moments before started unfolding smoothly, piece by piece.\n\n"
                f"Everyone nearby cheered in appreciation, and {char_name} felt a glorious burst of genuine warmth spreading through every step."
            ),
            (
                f"Facing the very heart of {clean_event}, {char_name} made a thoughtful choice to lead with kindness and resolve. "
                f"When things got tricky, {char_name} stayed calm and offered a helping hand to others who were also feeling uncertain.\n\n"
                f"By focusing on {goal_label}, {action_phrase}. "
                f"The obstacles began to clear away like morning mist under the warm sun, revealing an exciting path forward that brought bright smiles to everyone involved."
            )
        ]
        ending_pool = [
            (
                f"By late afternoon, the golden sky turned into soft shades of twilight and rose over {setting}. "
                f"{char_name} looked back at everything that had happened during {clean_event} with a proud, beaming smile.\n\n"
                f"The worry and hesitation from the morning were now completely replaced by an empowering sense of accomplishment. "
                f"'I did it,' {char_name} whispered happily. 'Facing something new with {goal_label} makes all the difference in the world.'\n\n"
                f"Walking home with a light, bouncy step, {char_name} couldn't wait to share the story with family and felt ready for whatever exciting adventures tomorrow might bring."
            ),
            (
                f"As the first evening stars began to twinkle peacefully above {setting}, a deep sense of confidence filled {char_name}'s thoughts. "
                f"Navigating {clean_event} had proven that true bravery doesn't mean never feeling nervous—it means acknowledging the nervousness, choosing {goal_label}, and taking the hop forward anyway.\n\n"
                f"Snuggled up warmly in bed with peaceful thoughts and joyful memories, {char_name} fell asleep with a calm heart and a confident smile, dreaming of new horizons."
            )
        ]

        intro = rng.choice(intro_pool)
        scene2 = rng.choice(scene2_pool)
        scene3 = rng.choice(scene3_pool)
        ending = rng.choice(ending_pool)
        story_body = f"{intro}\n\n{scene2}\n\n{scene3}\n\n{ending}"

        return {
            "title": title,
            "story": story_body,
            "seed": story_seed
        }

    # 9-12 Years (Richer narrative, thoughtful reflection, agency)
    else:
        intro_pool = [
            f"Across {setting}, the day unfolded with high expectations for {char_name}. An important moment had arrived: {clean_event}.",
            f"For {char_name}, solving puzzles and navigating new situations was a daily passion. Yet today brought a distinctive test in the form of {clean_event}.",
            f"The morning began with clear skies and a thoughtful mindset for {char_name}. Little did they know, {clean_event} would push them to put their principles into practice."
        ]
        middle_pool = [
            f"Confronted with the reality of {clean_event}, {char_name} carefully weighed their choices. True progress required {goal_label}. {action_phrase}. By taking initiative and looking at the challenge from a fresh angle, {char_name} discovered a thoughtful solution.",
            f"The complexity of {clean_event} demanded focus and integrity. Remembering that real strength comes from {goal_label}, {action_phrase}. Step by step, {char_name} navigated the obstacles with poise.",
            f"Rather than taking the easy route, {char_name} embraced the responsibility that {clean_event} brought. Committing to {goal_label}, {action_phrase}. Their decisive actions inspired everyone nearby."
        ]
        ending_pool = [
            f"Reflecting on how the situation resolved, {char_name} felt a deep sense of maturity and accomplishment. They proved that embracing {goal_label} turns any challenge into a lasting triumph.",
            f"As the evening settled peacefully over {setting}, {char_name} stood proud. Overcoming {clean_event} demonstrated that genuine character and {goal_label} make every journey worthwhile.",
            f"With newfound perspective and confidence, {char_name} knew this experience would stay with them for years to come—a shining example of {goal_label} in action."
        ]

    intro = rng.choice(intro_pool)
    middle = rng.choice(middle_pool)
    ending = rng.choice(ending_pool)

    story_body = f"{intro}\n\n{middle}\n\n{ending}"

    return {
        "title": title,
        "story": story_body,
        "seed": story_seed
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