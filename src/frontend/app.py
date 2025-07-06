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
    video_url = st.text_input("🔗 Direct Video URL (.mp4, .webm, or YouTube)")

# --- Trigger Button ---
run_clicked = st.button("🚀 Generate Research & Podcast")

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
                response.raise_for_status()
                result = response.json()

                # ✅ Backend returned an error (like Gemini quota exceeded)
                if "error" in result:
                    if "quota" in result["error"].lower():
                        st.warning(f"⚠️ Processing video input quota exceeded. Please try later or only pass the topic.")
                    else:
                        st.error(f"⚠️ {result['error']}")
                else:
                    st.success("✅ Research complete!")

                    # --- Report Display + Download ---
                    if result.get("report"):
                        st.markdown("### 📘 Research Report")
                        st.markdown(result["report"], unsafe_allow_html=True)

                        st.download_button(
                            label="📄 Download Report (.md)",
                            data=result["report"],
                            file_name=f"{topic.replace(' ', '_')}.md",
                            mime="text/markdown"
                        )

                    # --- Podcast Script ---
                    if result.get("podcast_script"):
                        st.markdown("### 🎙️ Podcast Script")
                        st.text(result["podcast_script"])

                    # --- Audio Player + Download ---
                    if result.get("podcast_filename"):
                        audio_url = f"{BACKEND_URL}/static/{result['podcast_filename']}"
                        st.markdown("### 🔊 Podcast Audio")

                        audio_response = requests.get(audio_url)
                        if audio_response.status_code == 200:
                            st.audio(audio_response.content, format="audio/wav")

                            st.download_button(
                                label="⬇️ Download Podcast (.wav)",
                                data=audio_response.content,
                                file_name=result['podcast_filename'],
                                mime="audio/wav"
                            )
                        else:
                            st.error("⚠️ Failed to load podcast audio. Try again.")

            except Exception as e:
                st.error(f"❌ Request error: {e}")
