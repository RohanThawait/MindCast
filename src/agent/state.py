from pydantic import BaseModel
from typing import Optional

class ResearchStateInput(BaseModel):
    """User-provided input for MindCast research + podcast workflow"""
    topic: str
    video_url: Optional[str] = None  # Optional video or YouTube link

class ResearchStateOutput(BaseModel):
    """Final output from the workflow"""
    report: Optional[str] = None
    podcast_script: Optional[str] = None
    podcast_filename: Optional[str] = None 
    report_filename: Optional[str] = None
    pdf_filename: Optional[str] = None

class ResearchState(BaseModel):
    """Complete state used in the LangGraph workflow"""
    # Input
    topic: str
    video_url: Optional[str] = None

    # Intermediate values
    search_text: Optional[str] = None
    search_sources_text: Optional[str] = None
    video_text: Optional[str]

    # Final outputs
    report: Optional[str] = None
    podcast_script: Optional[str] = None
    podcast_filename: Optional[str] = None
    report_filename: Optional[str] = None
    pdf_filename: Optional[str] = None
