# src/frontend/app.py
import streamlit as st
import requests
import time

# Backend endpoint
BACKEND_URL = "https://mindcast-gyl6.onrender.com"

# Page setup
st.set_page_config(page_title="🎙️ MindCast AI", layout="centered")
st.title("🎙️ MindCast: AI Research & Podcast Generator")
st.markdown("Enter a topic to generate a podcast + report. Optionally add a video for deeper insights.")

# --- User Input Section ---
topic = st.text_input("📝 Research Topic", placeholder="e.g. AI in healthcare")

video_method = st.radio("🎥 Optional Video Input", ["None", "Paste URL"])
video_url = None

if video_method == "Paste URL":
    video_url = st.text_input("🔗 Direct Video URL (.mp4, .webm or YT video)")

# Persistent state across reruns
if "disable_run" not in st.session_state:
    st.session_state.disable_run = False
if "retry_in" not in st.session_state:
    st.session_state.retry_in = 0


def countdown(seconds: int):
    for i in range(seconds, 0, -1):
        st.warning(f"⚠️ Gemini quota exceeded. Please wait {i} seconds before retrying...")
        time.sleep(1)
        st.experimental_rerun()


# --- Button ---
run_clicked = st.button("🚀 Generate Research & Podcast", disabled=st.session_state.disable_run)

if run_clicked:
    if not topic:
        st.error("❗ Please enter a topic.")
    else:
        with st.spinner("⏳ Processing..."):
            payload = {"topic": topic}
            if video_url:
                payload["video_url"] = video_url

            try:
                response = requests.post(f"{BACKEND_URL}/run", json=payload)

                # 429 Quota Exceeded
                if response.status_code == 429:
                    st.session_state.disable_run = True
                    st.session_state.retry_in = 60  # Gemini returns 56s; rounding to 60
                    st.warning("⚠️ Gemini API quota exceeded. Please try again in 60 seconds.")
                    countdown(st.session_state.retry_in)
                else:
                    response.raise_for_status()
                    result = response.json()
                    st.success("✅ Done! Here's your output.")

                    # --- (Keep existing rendering logic here for report, audio, script) ---
                    # ...
                    # st.markdown(...)

            except Exception as e:
                st.error(f"❌ Request error: {e}")
