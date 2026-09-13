# AI Worker & Local Story Generation Engine

This directory houses the core AI logic, prompt templates, and local worker process for **StoryApp**.

## Architecture Overview

```
Frontend / Browser ──► FastAPI (Port 8000) ──► multiprocessing.Queue ──► Qwen Worker Process ──► Local GGUF
                             │
                             ▼
                   SQLite (storyapp.db)
```

1. **Pure Python Execution**: No Jupyter, Colab, or ngrok required for running the demo.
2. **Dedicated Worker Process** ([`ai/qwen_worker.py`](./qwen_worker.py)):
   - Loads the GGUF model once at startup using `llama-cpp-python` and keeps it in memory.
   - Listens on a Python `multiprocessing.Queue` for story generation tasks.
   - Applies the system prompt, chat template, strips `<think>...</think>` tags, and returns the finished story.
   - If model weights are not loaded, it generates an explicitly labeled fallback story so the thesis demo remains functional without confusion.
3. **Lifespan Management** ([`backend/main.py`](../backend/main.py)):
   - FastAPI's `lifespan` context manager is the single owner of the worker process and IPC queues.
   - Manages graceful startup and shutdown upon `Ctrl+C`.
4. **Non-Blocking IPC Dispatcher** ([`ai/qwen_ipc.py`](./qwen_ipc.py)):
   - Uses correlation IDs and non-blocking background queue resolution (`asyncio.to_thread` / `call_soon_threadsafe`) so FastAPI's async event loop never blocks.

## How to Run the Demo

From the project root:

```bash
python run_app.py
```

Then open your browser to:
👉 **`http://localhost:8000`**

- **Web Demo Studio**: Generate personalized stories, select ages (4–5, 6–8), and choose hero archetypes.
- **SQLite Bookshelf & Reviews**: Rate stories (1–10) and submit feedback. All reviews are stored in `backend/storyapp.db` and automatically personalize subsequent story prompts.
- **API Documentation**: Available at `http://localhost:8000/docs`.

## Model Configuration (Optional)

By default, the worker searches for any `.gguf` file in `models/`, `ai/models/`, or the Hugging Face cache.

To point to a specific local model:
```env
# In .env or shell environment
QWEN_MODEL_PATH="C:/path/to/qwen-model.gguf"
```

## Notebooks

- [`Qwen3_5_9B_Story_Generator_Colab_with_API_updated.ipynb`](./Qwen3_5_9B_Story_Generator_Colab_with_API_updated.ipynb): Retained solely for testing and remote experiments. It is **not** required for running the local demo.
