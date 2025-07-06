from pydantic import BaseModel
from typing import Optional

class ResearchStateInput(BaseModel):
    """User-provided input for MindCast research + podcast workflow"""
    topic: str
    video_url: Optional[str]  # Optional video or YouTube link


class ResearchStateOutput(BaseModel):
    """Final output from the workflow"""
    report: Optional[str]
    podcast_script: Optional[str]
    podcast_filename: Optional[str]
    report_filename: Optional[str]
    pdf_filename: Optional[str]


class ResearchState(BaseModel):
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
