from typing_extensions import TypedDict
from typing import Optional

class ResearchStateInput(TypedDict):
    """User-provided input for MindCast research + podcast workflow"""
    topic: str
    video_url: Optional[str]  # Optional video or YouTube link


class ResearchStateOutput(TypedDict):
    """Final output from the workflow"""
    report: Optional[str]
    podcast_script: Optional[str]
    podcast_filename: Optional[str]
    report_filename: Optional[str]
    pdf_filename: Optional[str]


class ResearchState(TypedDict):
    """Complete state used in the LangGraph workflow"""
    # Input
    topic: str
    video_url: Optional[str]

    # Intermediate values
    search_text: Optional[str]
    search_sources_text: Optional[str]
    video_text: Optional[str]

    # Final outputs
    report: Optional[str]
    podcast_script: Optional[str]
    podcast_filename: Optional[str]
    report_filename: Optional[str]
    pdf_filename: Optional[str]
