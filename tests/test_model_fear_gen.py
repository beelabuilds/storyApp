"""Standalone test verifying fear safety, single title extraction, and no duplicate paragraphs directly with Qwen GGUF."""

import os
import sys
import time
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from ai.prompts import get_system_prompt_for_age, build_user_message
from ai.story_cleaner import extract_title_and_content, normalize_for_comparison
from backend.story_generator import resolve_fictional_character
import re
from llama_cpp import Llama

model_path = root_dir / "models" / "qwen-model.gguf"
if not model_path.is_file():
    print(f"Model not found at {model_path}")
    sys.exit(1)

print(f"Loading {model_path.name}...")
t0 = time.time()
llm = Llama(
    model_path=str(model_path),
    n_ctx=2048,
    n_batch=256,
    n_threads=max(1, (os.cpu_count() or 2) - 1),
    verbose=False,
)
print(f"Model loaded in {time.time() - t0:.2f}s")

description = "My 5-year-old child is afraid of strange sounds at night in their bedroom"
age = "4-5"
# Test when parent selected 'My child'
hero_input = "My child"
hero = resolve_fictional_character(hero_input, description)
print(f"Resolved Hero: {hero}")

sys_prompt = get_system_prompt_for_age(age)
user_msg = build_user_message(description=description, age=age, hero=hero)

print("Generating story with real local Qwen model...")
t_gen = time.time()
res = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_msg},
    ],
    temperature=0.70,
    top_p=0.85,
    top_k=25,
    repeat_penalty=1.25,
    presence_penalty=1.6,
    max_tokens=500,
)
elapsed = time.time() - t_gen
raw_story = res["choices"][0]["message"]["content"]
print(f"Generation took {elapsed:.2f}s")

default_title = f"{hero}'s Bedtime Adventure"
title, content = extract_title_and_content(
    raw_story,
    default_title=default_title,
    character_name=hero,
)

print("\n" + "=" * 60)
print(f"EXTRACTED TITLE: {title}")
print("=" * 60)
print(f"CLEAN CONTENT:\n{content}")
print("=" * 60)

# Verifications
assert title and len(title) > 3, f"Title extraction failed: {title}"
assert "Your Creative Title" not in title, "Title contained placeholder text!"
assert "Creative Title" not in title, "Title contained placeholder text!"
assert "Your Creative Title" not in content, "Content contained placeholder text!"
assert "Title:" not in content, "Content still had Title: header line!"
assert not content.startswith(title), "Content should not start with title repetition!"
assert not content.startswith("**Title:"), "Content should not start with **Title:"
assert "**Story:**" not in content, "Boilerplate should not be in content"

# Ensure 'my child' is NOT in the story content
assert "my child" not in content.lower(), "'my child' was found in generated content!"
assert "our child" not in content.lower(), "'our child' was found in generated content!"
assert "explorer" not in content.lower(), "'explorer' placeholder found in content!"

# Check for duplicate consecutive paragraphs
paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
for i in range(1, len(paragraphs)):
    assert paragraphs[i] != paragraphs[i-1], f"Found duplicate paragraph at {i}: {paragraphs[i][:40]}..."

# Check that NO sentence (>20 chars) is repeated across the entire story
sentences = [s.strip() for p in paragraphs for s in re.split(r"(?<=[.!?])\s+", p) if len(s.strip()) > 20]
seen_sentences = set()
for s in sentences:
    norm_s = normalize_for_comparison(s)
    assert norm_s not in seen_sentences, f"Duplicate sentence found in story: '{s}'"
    seen_sentences.add(norm_s)

# Check fear safety: ensure no extreme horror or police/panic tropes
scary_words = ["blood", "demon", "murder", "horrifying", "nightmare", "police", "panic"]
for w in scary_words:
    assert w not in content.lower(), f"Scary word '{w}' found in fear story!"

# Check that positive resolution words are present
comfort_words = ["peace", "safe", "dreams", "gentle", "love", "cozy", "soft"]
assert any(cw in content.lower() for cw in comfort_words), "Story lacked comforting resolution words!"

print("\n[PASS] All fear-safety, single title, fictional character, and zero-repetition assertions passed!")
