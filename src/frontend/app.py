# src/frontend/app.py
import streamlit as st
import requests

# Backend endpoint
BACKEND_URL = "http://localhost:8000"

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


# --- Trigger Generation ---
if st.button("🚀 Generate Research & Podcast"):
    if not topic:
        st.error("❗ Please enter a topic.")
    else:
        with st.spinner("⏳ Generating research..."):
            payload = {"topic": topic}
            if video_url:
                payload["video_url"] = video_url

            try:
                response = requests.post(f"{BACKEND_URL}/run", json=payload)
                response.raise_for_status()
                result = response.json()
                st.success("✅ Generation complete!")

                # === 📘 Research Report ===
                if "report" in result and result["report"]:
                    st.markdown("### 📘 Research Report")
                    st.markdown(result["report"], unsafe_allow_html=True)

                    st.download_button(
                        label="⬇️ Download Report (.md)",
                        data=result["report"],
                        file_name=f"{topic.replace(' ', '_')}.md",
                        mime="text/markdown",
                        key="download_report"
                    )

                # === 🎙️ Podcast Script ===
                if "podcast_script" in result and result["podcast_script"]:
                    st.markdown("### 🗒️ Podcast Script")
                    st.text(result["podcast_script"])

                # === 🔊 Podcast Audio ===
                if "podcast_filename" in result and result["podcast_filename"]:
                    st.markdown("### 🔊 Podcast Audio")

                    audio_url = f"{BACKEND_URL}/static/{result['podcast_filename']}"
                    audio_response = requests.get(audio_url)

                    if audio_response.status_code == 200:
                        st.audio(audio_response.content, format="audio/wav")

                        st.download_button(
                            label="⬇️ Download Podcast (.wav)",
                            data=audio_response.content,
                            file_name=result["podcast_filename"],
                            mime="audio/wav",
                            key="download_audio"
                        )
                    else:
                        st.error("⚠️ Failed to fetch audio. Make sure FastAPI is serving static files properly.")

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request error: {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
