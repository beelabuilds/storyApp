# AI Integration Directory

This folder contains the integration code and Colab notebook for **Qwen3.5-9B**.

## Notebook & Model

- **Notebook**: [`Qwen3_5_9B_Interactive_Colab - final version.ipynb`](./Qwen3_5_9B_Interactive_Colab%20-%20final%20version.ipynb)
- **Model**: `unsloth/Qwen3.5-9B-GGUF` (`UD-Q4_K_XL` 4-bit quant, ~6 GB)
- **Inference**: `llama-cpp-python` with CUDA acceleration on Google Colab (T4 GPU).
- **Thinking tags removal**: Automatically filters out `<think>...</think>` reasoning tags for direct responses.
- **Sampling Settings**:
  - `temperature = 0.7`
  - `top_p = 0.8`
  - `top_k = 20`
  - `repeat_penalty = 1.0`
  - `presence_penalty = 1.5`
  - `max_tokens = 2048`

## How to Connect to Local Backend

1. Open [`Qwen3_5_9B_Interactive_Colab - final version.ipynb`](./Qwen3_5_9B_Interactive_Colab%20-%20final%20version.ipynb) in Google Colab.
2. Select **Runtime → Change runtime type → T4 GPU**.
3. Run the cells to load the model.
4. Expose via ngrok / tunnel and copy your public URL.
5. In `backend/.env`, set:
   ```env
   QWEN_API_URL=https://your-ngrok-url.ngrok-free.dev
   ```
6. Run the local backend (`python -m uvicorn main:app --reload`). The backend will automatically detect and route story generations directly through the Qwen3.5-9B Colab instance. If unreachable, it gracefully falls back to the rich local engine.
