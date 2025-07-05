import os
import wave
import logging
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from google.genai import Client, types
from typing import Optional, Tuple
from src.agent.configuration import Configuration

load_dotenv()

# Initialize Gemini client
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))

def display_gemini_response(response) -> tuple[str, str]:
    """
    Extracts and displays Gemini response content and grounding sources in console.

    Returns:
        Tuple containing (main_response_text, formatted_sources_text)
    """
    console = Console()
    candidate = response.candidates[0]
    content_parts = candidate.content.parts
    text = content_parts[0].text if content_parts else "[No content found]"
    
    console.print(Markdown(text))
    
    sources_text = ""

    if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
        grounding = candidate.grounding_metadata
        sources_list = []

        if grounding.grounding_chunks:
            console.print("\n" + "=" * 50)
            console.print("[bold blue]References & Sources[/bold blue]")
            console.print("=" * 50)
            console.print(f"\n[bold]Sources ({len(grounding.grounding_chunks)}):[/bold]")

            for i, chunk in enumerate(grounding.grounding_chunks, 1):
                if hasattr(chunk, "web") and chunk.web:
                    title = getattr(chunk.web, "title", "No title")
                    uri = getattr(chunk.web, "uri", "No URI")
                    console.print(f"{i}. {title}")
                    console.print(f"   [dim]{uri}[/dim]")
                    sources_list.append(f"{i}. {title}\n   {uri}")
            
            sources_text = "\n".join(sources_list)

        if grounding.grounding_supports:
            console.print(f"\n[bold]Text segments with source backing:[/bold]")
            for support in grounding.grounding_supports[:5]:
                if support.segment:
                    snippet = support.segment.text
                    short_snippet = snippet[:100] + "..." if len(snippet) > 100 else snippet
                    indices = ", ".join(str(i+1) for i in support.grounding_chunk_indices)
                    console.print(f"• \"{short_snippet}\" [dim](sources: {indices})[/dim]")

    return text, sources_text


def wave_file(filename: str, pcm: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2) -> None:
    """
    Saves raw PCM audio data to a WAV file.

    Args:
        filename: Output .wav file path
        pcm: Raw PCM audio data
        channels: Number of audio channels (default 1 = mono)
        rate: Sample rate in Hz (default 24000)
        sample_width: Sample width in bytes (default 2 for 16-bit)
    """
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def create_podcast_discussion(
    topic: str,
    search_text: str,
    video_text: str,
    search_sources_text: str,
    video_url: Optional[str],
    filename: Optional[str] = None,
    configuration: Optional[Configuration] = None
) -> Tuple[str, str]:
    """
    Creates a podcast conversation and generates audio using Gemini TTS.

    Args:
        topic: The topic for the podcast.
        search_text: Insights from web search.
        video_text: Insights from video analysis.
        search_sources_text: Citation text block from search.
        video_url: Optional URL to the analyzed video.
        filename: Custom output filename. If not provided, one is generated.
        configuration: Optional Configuration instance.

    Returns:
        Tuple containing:
            - podcast_script: The generated dialogue
            - podcast_filename: Name of the saved .wav file
    """
    if configuration is None:
        configuration = Configuration()

    # 1. Generate podcast script
    script_prompt = f"""
    Create a natural, engaging podcast conversation between Dr. Sarah (research expert) and Mike (curious interviewer) about "{topic}".

    Use this research content:

    SEARCH FINDINGS:
    {search_text}

    VIDEO INSIGHTS:
    {video_text}

    Format as a dialogue with:
    - Mike introducing the topic and asking questions
    - Dr. Sarah explaining key concepts and insights
    - Natural back-and-forth discussion (5–7 exchanges)
    - Mike asking follow-up questions
    - Dr. Sarah summarizing key takeaways
    - Keep it conversational and accessible (~3–4 mins)

    Format like:
    Mike: ...
    Dr. Sarah: ...
    """
    
    script_response = genai_client.models.generate_content(
        model=configuration.synthesis_model,
        contents=script_prompt,
        config={"temperature": configuration.podcast_script_temperature}
    )

    podcast_script = script_response.candidates[0].content.parts[0].text.strip()

    # 2. Generate multi-speaker TTS
    tts_prompt = f"TTS the following conversation between Mike and Dr. Sarah:\n{podcast_script}"

    audio_response = genai_client.models.generate_content(
        model=configuration.tts_model,
        contents=tts_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker="Mike",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=configuration.mike_voice
                                )
                            ),
                        ),
                        types.SpeakerVoiceConfig(
                            speaker="Dr. Sarah",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=configuration.sarah_voice
                                )
                            ),
                        ),
                    ]
                )
            )
        )
    )

    audio_data = audio_response.candidates[0].content.parts[0].inline_data.data

    # 3. Save the audio to 'podcasts' folder
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (" ", "-", "_")).rstrip().replace(" ", "_")
    os.makedirs("podcasts", exist_ok=True)

    podcast_filename = filename or f"mindcast_episode_{safe_topic}.wav"
    filepath = os.path.join("podcasts", podcast_filename)

    wave_file(filepath, audio_data, configuration.tts_channels, configuration.tts_rate, configuration.tts_sample_width)

    logging.getLogger(__name__).info(f"Podcast saved at: {filepath}")

    return podcast_script, podcast_filename

import os
import logging
from textwrap import wrap
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

def create_research_report(topic, search_text, video_text, search_sources_text, video_url, configuration=None):
    """Create a comprehensive research report by synthesizing search and video content"""

    if configuration is None:
        from agent.configuration import Configuration
        configuration = Configuration()

    # Step 1: Create synthesis using Gemini
    synthesis_prompt = f"""
    You are a research analyst. I have gathered information about "{topic}" from two sources:

    SEARCH RESULTS:
    {search_text}

    VIDEO CONTENT:
    {video_text}

    Please create a comprehensive synthesis that:
    1. Identifies key themes and insights from both sources
    2. Highlights any complementary or contrasting perspectives
    3. Provides an overall analysis of the topic based on this multi-modal research
    4. Keep it concise but thorough (3-4 paragraphs)

    Focus on creating a coherent narrative that brings together the best insights from both sources.
    """

    synthesis_response = genai_client.models.generate_content(
        model=configuration.synthesis_model,
        contents=synthesis_prompt,
        config={"temperature": configuration.synthesis_temperature}
    )

    synthesis_text = synthesis_response.candidates[0].content.parts[0].text

    # Step 2: Create markdown report
    report = f"""# Research Report: {topic}

## Executive Summary

{synthesis_text}

## Video Source
- **URL**: {video_url}

## Additional Sources
{search_sources_text}

---
*Report generated using multi-modal AI research combining web search and video analysis*
"""

    # Safe file name
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip().replace(' ', '_')

    # Create directory
    os.makedirs("reports", exist_ok=True)

    # Save Markdown
    report_filename = os.path.join("reports", f"mindcast_report_{safe_topic}.md")
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)

    # Save PDF
    pdf_filename = os.path.join("reports", f"mindcast_report_{safe_topic}.pdf")
    c = canvas.Canvas(pdf_filename, pagesize=LETTER)
    width, height = LETTER
    c.setFont("Helvetica", 12)

    lines = report.split("\n")
    y = height - 50

    for line in lines:
        wrapped_lines = wrap(line, width=90)
        for wrapped_line in wrapped_lines:
            c.drawString(40, y, wrapped_line)
            y -= 18
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height - 50

    c.save()

    logger = logging.getLogger(__name__)
    logger.info(f"Report saved as: {report_filename}")
    logger.info(f"PDF saved as: {pdf_filename}")

    return report, synthesis_text, os.path.basename(report_filename), os.path.basename(pdf_filename)
