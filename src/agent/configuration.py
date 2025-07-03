"""Configuration settings for the MindCast AI research and podcast generator"""

import os
from dataclasses import dataclass, fields
from typing import Optional, Any
from langchain_core.runnables import RunnableConfig


@dataclass(kw_only=True)
class Configuration:
    """Config schema used by LangGraph and FastAPI."""

    # 🌐 Model versions
    search_model: str = "gemini-2.5-flash"
    synthesis_model: str = "gemini-2.5-flash"
    video_model: str = "gemini-2.5-flash"
    tts_model: str = "gemini-2.5-flash-preview-tts"

    # 🔥 Temperature controls
    search_temperature: float = 0.0          # factual, no hallucination
    synthesis_temperature: float = 0.3       # analytical report
    podcast_script_temperature: float = 0.4  # more creative

    # 🎙️ TTS voice settings
    mike_voice: str = "Kore"   # Male
    sarah_voice: str = "Puck"  # Female
    tts_channels: int = 1
    tts_rate: int = 24000
    tts_sample_width: int = 2

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Support LangGraph's config injection and .env fallbacks."""
        configurable = config.get("configurable", {}) if config else {}
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v is not None})

    def to_dict(self):
        return self.__dict__
