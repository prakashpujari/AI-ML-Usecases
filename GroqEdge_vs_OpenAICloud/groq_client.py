import importlib
import time
import os

try:
    _groq_mod = importlib.import_module("groq")
    Groq = getattr(_groq_mod, "Groq", None)
    NotFoundError = getattr(_groq_mod, "NotFoundError", None)
except Exception:
    Groq = None
    NotFoundError = None

_GROQ_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=_GROQ_KEY) if Groq and _GROQ_KEY else None

def groq_answer(query, context):
    start = time.time()
    if groq_client is None:
        latency = time.time() - start
        return ("Groq client not available. Ensure `groq` is installed and GROQ_API_KEY is set.", latency)

    # Models to attempt (env override first)
    # Prefer an explicit model provided via env var. If not set,
    # require the user to opt-in to automatic fallback attempts.
    models = []
    env_model = os.getenv("GROQ_MODEL")
    if env_model:
        models.append(env_model)
    else:
        auto_fallback = os.getenv("AUTO_GROQ_FALLBACK", "0")
        if auto_fallback in ("1", "true", "True"):
            models.extend(["mixtral-8x7b", "mixtral-8x7b-instruct", "mixtral-7b"])
        else:
            latency = time.time() - start
            return ("No GROQ_MODEL set. Set the GROQ_MODEL env var or enable AUTO_GROQ_FALLBACK=1 to try defaults.", latency)

    last_err = None
    for model in models:
        try:
            res = groq_client.chat.completions.create(
                model=model,
                messages=[{"role":"user", "content": f"Context: {context}\nQuestion: {query}"}]
            )
            latency = time.time() - start
            try:
                return res.choices[0].message.content, latency
            except Exception:
                return str(res), latency
        except Exception as e:
            last_err = e
            # If it's a model-not-found type error, try next model
            if NotFoundError and isinstance(e, NotFoundError):
                continue
            msg = str(e).lower()
            if "model" in msg and ("does not exist" in msg or "not found" in msg):
                continue
            # For other error types, return immediately
            latency = time.time() - start
            return (f"Groq error: {e}", latency)

    latency = time.time() - start
    tried = ", ".join(models)
    return (f"Model not available. Tried: {tried}. Last error: {last_err}", latency)
