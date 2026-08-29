import os
import sys

# Add project root to sys.path to allow importing from 'ai'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from prompts import build_story_prompt

# Check if Qwen integration is configured and can be imported
try:
    from ai.qwen_integration import generate_story_with_qwen
    HAS_QWEN = True
except (ImportError, ModuleNotFoundError):
    HAS_QWEN = False


def prepare_story_prompt(event, age, goal, character, language):
    """
    Prepare the prompt that will be sent to the AI model.
    """
    return build_story_prompt(
        event=event,
        age=age,
        goal=goal,
        character=character,
        language=language
    )


def generate_story_locally(event: str, age: str, goal: str, character: str, language: str) -> dict:
    """
    Generates a high-quality, customized children's story locally using templates.
    Tailors the text based on age, event, goal, and character.
    """
    # Clean inputs
    char_name = character.strip() or "A friendly little friend"
    ev_lower = event.lower()
    goal_lower = goal.lower()
    
    # Identify themes from event
    theme = "general"
    if "dark" in ev_lower or "night" in ev_lower or "sleep" in ev_lower or "bed" in ev_lower:
        theme = "dark"
    elif "school" in ev_lower or "class" in ev_lower or "teacher" in ev_lower or "kindergarten" in ev_lower:
        theme = "school"
    elif "tooth" in ev_lower or "teeth" in ev_lower:
        theme = "tooth"
    elif "share" in ev_lower or "toy" in ev_lower or "friend" in ev_lower or "fight" in ev_lower:
        theme = "sharing"

    # Identify goal label
    goal_label = "being brave"
    if "share" in goal_lower or "empathy" in goal_lower:
        goal_label = "sharing with others"
    elif "patience" in goal_lower or "wait" in goal_lower:
        goal_label = "being patient"
    elif "kind" in goal_lower or "help" in goal_lower:
        goal_label = "showing kindness"
    elif "calm" in goal_lower or "anger" in goal_lower or "breath" in goal_lower:
        goal_label = "staying calm and taking deep breaths"

    # Build age-based styling details
    # 3-5: Simple, short sentences, repetitive, cozy.
    # 6-8: Moderate length, some minor drama/resolution, slightly richer descriptions.
    # 9-12: Richer vocab, deeper character reflection, longer paragraphs.
    
    title = ""
    paragraphs = []

    if theme == "dark":
        title = f"{char_name}'s Sparkly Starry Night"
        
        intro_3_5 = f"Once upon a time, there was a little friend named {char_name}. {char_name} loved playing in the bright sunshine. But when the night came, {char_name} did not like the dark. Every night, when the lights went click-clack, the bedroom felt too big and too quiet."
        intro_6_8 = f"In a cozy treehouse near the whispering woods lived a cheerful explorer named {char_name}. {char_name} spent the days climbing high branches and chasing colorful butterflies. But when night fell and the shadows grew long, {char_name} felt a little squeeze in their heart. The dark was mysterious, and {char_name} preferred the sunny daylight."
        intro_9_12 = f"Deep within the valley of Everglow, a curious young adventurer named {char_name} spent their days studying ancient maps and exploring hidden paths. While {char_name} was known for their bright spirit during the day, the sunset brought a different feeling. When the shadows stretched across the room, {char_name} would stare at the dark corners, wishing for just a little more light."

        middle_3_5 = f"Tonight was special. {char_name} was trying to sleep. But it was very dark! {char_name} felt nervous. Then, {char_name} remembered their goal: {goal_label}. {char_name} looked up at the window. There were tiny stars blinking like nightlights. They seemed to whisper, 'You are safe!'"
        middle_6_8 = f"Tonight, {char_name} was facing a challenge: {event}. The room was filled with soft shadows, and it felt a little scary. {char_name} wanted to practice {goal_label}. {char_name} took a slow, deep breath, just like a wise owl. {char_name} looked out the window and noticed that the moon was shining like a silver nightlight, casting a warm and friendly glow."
        middle_9_12 = f"On this particular night, {char_name} faced a new situation: {event}. The darkness seemed to cover everything. Remembering their promise to practice {goal_label}, {char_name} decided to try a new perspective. Instead of seeing the dark as a scary mystery, they thought of it as the earth's natural blanket, allowing the flowers, trees, and animals to rest. {char_name} sat up, closed their eyes, and listened to the gentle hum of the cricket symphony outside."

        ending_3_5 = f"{char_name} hugged their teddy close. {char_name} took a deep breath. 1... 2... 3... and smiled. The dark was just a cozy blanket! {char_name} closed their eyes and had sweet, happy dreams. {char_name} was so proud of {goal_label}!"
        ending_6_8 = f"With a brave smile, {char_name} pulled the soft blanket up to their chin. They cuddled their favorite toy and thought of all the fun adventures waiting tomorrow. Realizing that the dark was just a quiet time for sweet dreams, {char_name} drifted off to sleep, feeling incredibly proud of {goal_label}."
        ending_9_12 = f"Taking a long, calming breath, {char_name} let the tension leave their shoulders. They realized that courage didn't mean never being afraid; it meant finding peace even in the quiet dark. Wrapped in the soft covers, {char_name} fell into a deep, restful sleep. In the morning, they woke up feeling refreshed, strong, and ready for a new day, proud of their growth in {goal_label}."

    elif theme == "school":
        title = f"{char_name}'s Big School Adventure"
        
        intro_3_5 = f"Meet {char_name}! {char_name} had a brand new backpack. Today was the first day of school. {char_name} held their parent's hand tightly. The school looked very big, and there were many new faces."
        intro_6_8 = f"It was a sunny Monday morning, and {char_name} was standing right in front of the school gates. Today was a big day: {event}. With a new pencil box and a shiny lunchbox, {char_name} felt excitement and a little bit of butterflies in their tummy."
        intro_9_12 = f"The morning bell rang, echoing across the crowded school yard. {char_name} stood near the entrance, adjusting their backpack straps. Today brought a new chapter: {event}. Surrounded by groups of students talking and laughing, {char_name} felt a sudden wave of shyness."

        middle_3_5 = f"Inside the classroom, {char_name} saw toys and colorful drawings. But {char_name} felt shy. Then, {char_name} remembered to practice {goal_label}. {char_name} saw a child sitting alone near the puzzle blocks. {char_name} walked over, step by step."
        middle_6_8 = f"Walking into the classroom, {char_name} felt unsure about where to sit. The teacher, Miss Robin, gave a warm smile. {char_name} remembered their goal to focus on {goal_label}. Instead of waiting in the corner, {char_name} walked up to a table where a classmate was drawing and asked if they could join."
        middle_9_12 = f"Entering the classroom, {char_name} scaned the room for an empty desk. They knew this was a prime opportunity to work on {goal_label}. Resisting the urge to hide in the back row, {char_name} walked over to a group working on a science poster. They offered a friendly greeting and asked how they could help contribute to the project."

        ending_3_5 = f"{char_name} showed a big smile. 'Can I play?' {char_name} asked. The child said, 'Yes!' They built a tall tower together. School was fun! {char_name} was happy they practiced {goal_label}."
        ending_6_8 = f"The classmate smiled brightly and shared a blue crayon. Soon, they were laughing and talking about their favorite games. By the time the final bell rang, {char_name} had made a new friend and realized that school is a place for discovery. They walked home happily, proud of {goal_label}."
        ending_9_12 = f"The team welcomed {char_name} warmly, and within minutes, they were brainstorming ideas together. {char_name} felt the nervous butterflies disappear, replaced by a sense of belonging. Walking home after school, {char_name} realized that taking the initiative and showing {goal_label} made all the difference in turning a nervous day into a successful one."

    elif theme == "tooth":
        title = f"{char_name} and the Magic Tooth Fairy"
        
        intro_3_5 = f"Pop! {char_name} had a loose tooth, and today it came out! {char_name} looked in the mirror. There was a tiny window in their smile. It felt funny when they touched it with their tongue."
        intro_6_8 = f"It finally happened! {char_name} was chewing a crunchy apple when—wiggle, wiggle, pop!—their tooth came out. {char_name} held the tiny, white tooth in their hand. It was their very first lost tooth, representing {event}."
        intro_9_12 = f"During lunch, {char_name} felt a sudden pop. They realized they had finally lost another tooth, which was related to {event}. Looking at the tiny tooth in their palm, {char_name} realized how much they were growing up."

        middle_3_5 = f"{char_name} was a little bit worried. Would their smile look silly? But {char_name} remembered to practice {goal_label}. {char_name} washed the tiny tooth. They put it under their soft pillow before going to bed."
        middle_6_8 = f"{char_name} was proud but also had a few questions. Would a new tooth grow back quickly? They decided to practice {goal_label}. They carefully cleaned the tooth, wrote a tiny letter, and placed both safely under their pillow."
        middle_9_12 = f"Though losing a tooth is a normal part of growing up, it always felt a bit strange. {char_name} decided to practice {goal_label}. They placed the tooth in a special pouch under their pillow, feeling curious about the folklore and wondering what the night would bring."

        ending_3_5 = f"In the morning, {char_name} looked under the pillow. The tooth was gone! In its place was a shiny coin. {char_name} smiled a big, happy, gappy smile. {char_name} was so happy about {goal_label}!"
        ending_6_8 = f"When the sun rose, {char_name} searched under the pillow. The tooth was replaced by a shiny silver coin and a tiny note thanking them for being so clean. {char_name} smiled a big, proud, toothy smile, excited to show their friends, happy about {goal_label}."
        ending_9_12 = f"The next morning, the tooth was replaced with a crisp coin and a note praising their independence. {char_name} stood in front of the mirror, smiling at the new gap, recognizing it as a mark of growth and feeling incredibly proud of {goal_label}."

    elif theme == "sharing":
        title = f"{char_name} Shares the Joy"
        
        intro_3_5 = f"{char_name} had a beautiful, shiny red ball. It was {char_name}'s favorite toy. {char_name} was playing in the park. Then, another child came by and looked at the ball with sad eyes."
        intro_6_8 = f"It was a busy afternoon at the playground. {char_name} was playing with their brand new, remote-controlled toy truck. It could climb over rocks and spin around. A little boy stood nearby, watching the truck with wide, hopeful eyes."
        intro_9_12 = f"At the community center, {char_name} was working on a beautiful art kit they had received for their birthday. It had every color of paint imaginable. Another kid, who was sitting at the same table, only had a few broken crayons and was looking longingly at {char_name}'s colors."

        middle_3_5 = f"{char_name} wanted to keep the ball. Sharing felt hard! But {char_name} remembered their goal: {goal_label}. {char_name} took a deep breath. {char_name} held out the shiny red ball. 'Do you want to roll it?'"
        middle_6_8 = f"{char_name} felt a little protective of the new truck. What if it got scratched? But {char_name} wanted to practice {goal_label}. They remembered how it felt to want to play. {char_name} walked over, showed the remote, and said, 'Do you want to take turns steering it?'"
        middle_9_12 = f"{char_name} hesitated, feeling a bit possessive of the clean, new paints. However, they realized this was a moment to choose {goal_label}. Recognizing the other kid's situation, {char_name} pushed the paint set to the center of the table. 'Hey, we can share these paints if you want! What are you drawing?'"

        ending_3_5 = f"The child smiled so big! They rolled the ball back and forth. They laughed together. Playing together was twice as fun! {char_name} was so happy they practiced {goal_label}."
        ending_6_8 = f"The boy's face lit up. They spent the next hour building ramps and taking turns driving the truck. {char_name} realized that sharing the toy didn't make the fun go away; it actually doubled it. They walked home with a warm feeling in their heart, proud of {goal_label}."
        ending_9_12 = f"The other kid smiled with relief and accepted the offer. They spent the afternoon painting a giant mural of a space castle, blending their ideas and colors together. {char_name} realized that by sharing their paints, they didn't lose anything—instead, they gained a collaborative project and a new friend, feeling proud of {goal_label}."

    else:
        # General Fallback theme
        title = f"{char_name}'s Special Day"
        
        intro_3_5 = f"Once upon a time, there was a happy little friend named {char_name}. {char_name} lived in a cozy house. Today, something new happened. {char_name} had to deal with {event}."
        intro_6_8 = f"In a green valley where the flowers always bloomed lived a kind adventurer named {char_name}. {char_name} loved exploring. But today brought a brand new challenge: {event}."
        intro_9_12 = f"In the quiet town of Oakridge, a bright student named {char_name} always looked forward to new experiences. However, today brought a unique situation: {event}. It was something {char_name} hadn't faced before, and it made them think deeply."

        middle_3_5 = f"{char_name} felt a little unsure. It was hard! But {char_name} remembered to practice {goal_label}. {char_name} took a slow breath. 1... 2... 3... and decided to try their best."
        middle_6_8 = f"{char_name} wasn't sure how to handle it. They felt a mix of feelings. But {char_name} wanted to practice {goal_label}. They sat down, thought of a good plan, and decided to take action."
        middle_9_12 = f"{char_name} stood still for a moment, weighing their options. They knew that the best way forward was to practice {goal_label}. Taking a deep breath to steady their mind, they approached the situation calmly and looked for a creative solution."

        ending_3_5 = f"It worked! {char_name} did it. {char_name} was so happy and felt very warm inside. {char_name} knew that {goal_label} was a wonderful thing!"
        ending_6_8 = f"Everything turned out beautifully. {char_name} felt a wave of pride wash over them. They realized that by choosing {goal_label}, they had turned a difficult moment into a happy success. They couldn't wait to share their day with their parents."
        ending_9_12 = f"The situation was resolved in a positive way. {char_name} felt a strong sense of accomplishment. They learned that facing challenges with {goal_label} builds character and strength. They walked away with a smile, ready for whatever came next."

    # Select paragraph based on age group
    if "3-5" in age:
        paragraphs = [intro_3_5, middle_3_5, ending_3_5]
    elif "6-8" in age:
        paragraphs = [intro_6_8, middle_6_8, ending_6_8]
    else:  # "9-12" or fallback
        paragraphs = [intro_9_12, middle_9_12, ending_9_12]

    # Combine paragraphs into a clean text block
    story_body = "\n\n".join(paragraphs)
    
    return {
        "title": title,
        "story": story_body
    }


def generate_story(event: str, age: str, goal: str, character: str, language: str) -> dict:
    """
    Main entry point for generating stories.
    Tries to use Qwen3.5-9B if it's imported, otherwise falls back to local template generation.
    """
    prompt = prepare_story_prompt(event, age, goal, character, language)
    
    if HAS_QWEN:
        try:
            story_text = generate_story_with_qwen(prompt)
            # Parse story_text into title and body
            # Expected format: Title: [Title]\n\n[Body]
            lines = story_text.strip().split("\n")
            title = "A Special Story"
            body_lines = []
            
            for line in lines:
                if line.lower().startswith("title:"):
                    title = line[len("title:"):].strip()
                else:
                    body_lines.append(line)
            
            body = "\n".join(body_lines).strip()
            if not body:
                body = story_text
                
            return {
                "title": title,
                "story": body,
                "prompt": prompt,
                "engine": "Qwen3.5-9B"
            }
        except Exception as e:
            # Fall back to template generation on error
            local_res = generate_story_locally(event, age, goal, character, language)
            local_res["prompt"] = prompt
            local_res["engine"] = f"Template-Fallback (Qwen Error: {str(e)})"
            return local_res
    else:
        local_res = generate_story_locally(event, age, goal, character, language)
        local_res["prompt"] = prompt
        local_res["engine"] = "Template-Engine"
        return local_res