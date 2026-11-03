import os

import ollama


# ==========================================
# 1. CONFIGURATION
# ==========================================

MODEL_NAME = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

# Empty means "use the local daemon on 127.0.0.1:11434" (ollama default).
OLLAMA_HOST = os.environ.get("OLLAMA_HOST") or None

# Seconds to wait for a completion before giving up.
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "120"))


class LLMUnavailable(RuntimeError):
    """Raised when the Ollama runtime cannot be reached or has no model loaded."""


_client = None


def _get_client():
    """Create the Ollama client once, honouring OLLAMA_HOST when it is set."""

    global _client

    if _client is None:
        _client = ollama.Client(
            host=OLLAMA_HOST,
            timeout=OLLAMA_TIMEOUT,
        )

    return _client


def generate_response(prompt):

    try:

        response = _get_client().chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            # Add options to drastically reduce the initial memory layout footprint
            options={
                "num_ctx": 2048,      # Shrinks active memory space from 8k to 2k context window
                "num_predict": 256,   # Caps response token generation length
                "num_thread": 4       # Restricts multi-threaded memory buffer spikes
            }
        )

    except Exception as error:  # network error, missing model, timeout, ...

        raise LLMUnavailable(
            f"Ollama request failed for model '{MODEL_NAME}': {error}"
        ) from error

    return response["message"]["content"]


if __name__ == "__main__":
    question = "What is a sales lead?"

    print("Sending request to local Llama 3.2 3B model (Low-Memory configuration)...")
    answer = generate_response(question)

    print("\nLLM Response:")
    print(answer)
