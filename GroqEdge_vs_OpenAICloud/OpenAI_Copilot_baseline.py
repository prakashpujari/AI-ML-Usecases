import importlib
try:
    _openai_mod = importlib.import_module("openai")
    OpenAI = getattr(_openai_mod, "OpenAI", None)
except Exception:
    OpenAI = None
import time
import os

_OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=_OPENAI_KEY) if OpenAI and _OPENAI_KEY else None

def openai_answer(query, context):
    start = time.time()
    if client is None:
        latency = time.time() - start
        return ("OpenAI client not available. Ensure `openai` is installed and OPENAI_API_KEY is set.", latency)
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user", "content": f"Context: {context}\nQuestion: {query}"}]
    )
    latency = time.time() - start
    # Best-effort access to response content
    try:
        return res.choices[0].message.content, latency
    except Exception:
        return str(res), latency
