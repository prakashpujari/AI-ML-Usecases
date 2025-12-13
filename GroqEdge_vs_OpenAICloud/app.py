import importlib
try:
    _st_mod = importlib.import_module("streamlit")
    st = _st_mod
except Exception:
    st = None

from OpenAI_Copilot_baseline import openai_answer
from groq_client import groq_answer

if st:
    st.title("Groq vs OpenAI — Inference Comparison")
    st.markdown("A minimal interface to compare inference responses and latency between Groq and OpenAI.")
    query = st.text_input("Prompt / Question:")

    if st.button("Run"):
        # No context textbox — always pass empty context
        groq_res, groq_time = groq_answer(query, "")
        openai_res, openai_time = openai_answer(query, "")

        st.subheader("Groq response")
        st.write(groq_res)
        st.caption(f"Latency: {groq_time:.3f} sec")

        st.subheader("OpenAI response")
        st.write(openai_res)
        st.caption(f"Latency: {openai_time:.3f} sec")

        st.subheader("Latency Comparison")
        st.bar_chart({
            "Groq": [groq_time],
            "OpenAI": [openai_time]
        })
else:
    # Fallback CLI behavior when Streamlit isn't available
    print("Streamlit not installed. Running CLI fallback for Groq vs OpenAI inference.")
    query = input("Prompt / Question:\n")
    groq_res, groq_time = groq_answer(query, "")
    openai_res, openai_time = openai_answer(query, "")
    print("--- Groq response ---")
    print(groq_res)
    print(f"Latency: {groq_time:.3f} sec")
    print("--- OpenAI response ---")
    print(openai_res)
    print(f"Latency: {openai_time:.3f} sec")
