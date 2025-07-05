"""LangGraph implementation of the MindCast podcast + research workflow"""

from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from google.genai import types
from langsmith import traceable

from src.agent.state import ResearchState, ResearchStateInput, ResearchStateOutput
from src.agent.utils import (
    display_gemini_response,
    create_podcast_discussion,
    create_research_report,
    genai_client
)
from src.agent.configuration import Configuration


@traceable(run_type="llm", name="Web Research", project_name="MindCast")
def search_research_node(state: ResearchState, config: RunnableConfig) -> dict:
    topic = state["topic"]
    configuration = Configuration.from_runnable_config(config)

    search_response = genai_client.models.generate_content(
        model=configuration.search_model,
        contents=f"Research this topic and give me an overview: {topic}",
        config={
            "tools": [{"google_search": {}}],
            "temperature": configuration.search_temperature,
        },
    )

    search_text, search_sources_text = display_gemini_response(search_response)

    return {
        "search_text": search_text,
        "search_sources_text": search_sources_text,
    }


@traceable(run_type="llm", name="YouTube Video Analysis", project_name="MindCast")
def analyze_video_node(state: ResearchState, config: RunnableConfig) -> dict:
    topic = state["topic"]
    video_url = state.get("video_url")
    configuration = Configuration.from_runnable_config(config)

    if not video_url:
        return {"video_text": "No video provided for analysis."}

    video_response = genai_client.models.generate_content(
        model=configuration.video_model,
        contents=types.Content(
            parts=[
                types.Part(file_data=types.FileData(file_uri=video_url)),
                types.Part(text=f"Based on the video content, give me an overview of this topic: {topic}")
            ]
        )
    )

    video_text, _ = display_gemini_response(video_response)
    return {"video_text": video_text}


@traceable(run_type="llm", name="Create Report", project_name="MindCast")
def create_report_node(state: ResearchState, config: RunnableConfig) -> dict:
    configuration = Configuration.from_runnable_config(config)

    report, synthesis_text, report_filename, pdf_filename = create_research_report(
        topic=state["topic"],
        search_text=state.get("search_text", ""),
        video_text=state.get("video_text", ""),
        search_sources_text=state.get("search_sources_text", ""),
        video_url=state.get("video_url", ""),
        configuration=configuration,
    )

    return {
        "report": report,
        "synthesis_text": synthesis_text,
        "report_filename": report_filename,
        "pdf_filename": pdf_filename,
    }



@traceable(run_type="llm", name="Create Podcast", project_name="MindCast")
def create_podcast_node(state: ResearchState, config: RunnableConfig) -> dict:
    configuration = Configuration.from_runnable_config(config)

    safe_topic = "".join(c for c in state["topic"] if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"research_podcast_{safe_topic.replace(' ', '_')}.wav"

    podcast_script, podcast_filename = create_podcast_discussion(
        topic=state["topic"],
        search_text=state.get("search_text", ""),
        video_text=state.get("video_text", ""),
        search_sources_text=state.get("search_sources_text", ""),
        video_url=state.get("video_url", ""),
        filename=filename,
        configuration=configuration,
    )

    return {
        "podcast_script": podcast_script,
        "podcast_filename": podcast_filename,
    }


def should_analyze_video(state: ResearchState) -> str:
    """Decide whether to analyze video or go directly to report"""
    return "analyze_video" if state.get("video_url") else "create_report"


def create_research_graph() -> StateGraph:
    graph = StateGraph(
        state_schema=ResearchState,
        input_schema=ResearchStateInput,
        output_schema=ResearchStateOutput,
        config_schema=Configuration,
    )

    graph.add_node("search_research", search_research_node)
    graph.add_node("analyze_video", analyze_video_node)
    graph.add_node("create_report", create_report_node)
    graph.add_node("create_podcast", create_podcast_node)

    graph.add_edge(START, "search_research")
    graph.add_conditional_edges("search_research", should_analyze_video, {
        "analyze_video": "analyze_video",
        "create_report": "create_report"
    })
    graph.add_edge("analyze_video", "create_report")
    graph.add_edge("create_report", "create_podcast")
    graph.add_edge("create_podcast", END)

    return graph


def create_compiled_graph():
    return create_research_graph().compile()
