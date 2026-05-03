#!/usr/bin/env python3
"""
YouTube URL Utilities

Common utilities for YouTube URL processing including sanitization, validation,
and video ID extraction. Used by main.py and download_transcript.py.
"""

import re
import json
import urllib.request
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel, Field

CONFIG_FILE = Path("config.json")


def load_config() -> Optional["AppConfig"]:
    """Load configuration from config.json if it exists."""
    if CONFIG_FILE.exists():
        try:
            return AppConfig.model_validate_json(CONFIG_FILE.read_text())
        except Exception:
            return None
    return None


# Centralized Regex Patterns
YT_PATTERNS = [
    r'^https?://(?:www\.)?youtube\.com/watch\?(?:.*&)?v=([a-zA-Z0-9_-]+)',
    r'^https?://youtu\.be/([a-zA-Z0-9_-]+)',
    r'^https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)',
    r'^https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)',
]


from enum import Enum


class ProviderType(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class ServiceName(str, Enum):
    OLLAMA = "ollama"
    LM_STUDIO = "lm-studio"
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AppConfig(BaseModel):
    """Configuration schema for the summarization service."""
    provider: ProviderType
    service: ServiceName
    url: Optional[str] = None
    model: str
    api_key: Optional[str] = None

    class Config:
        use_enum_values = True


class TranscriptMetadata(BaseModel):
    """Pydantic model for transcript metadata."""
    timestamp: str
    word_count: int
    language: str = "auto"
    author: Optional[str] = None


class TranscriptData(BaseModel):
    """Pydantic model for the complete transcript payload."""
    url: str
    title: str
    transcript: str
    metadata: TranscriptMetadata

    def to_markdown(self) -> str:
        """Export the transcript data as a formatted Markdown string."""
        return f"""# {self.title}

- **URL**: {self.url}
- **Author**: {self.metadata.author or 'Unknown'}
- **Word Count**: {self.metadata.word_count}
- **Date**: {self.metadata.timestamp}
- **Language**: {self.metadata.language}

## Transcript

{self.transcript}
"""


def sanitize_url(url: str) -> str:
    """
    Sanitize a YouTube URL by removing whitespace and backslashes.
    """
    if not url:
        return ""
    return url.strip().replace("\\", "")


def is_valid_youtube_url(url: str) -> bool:
    """
    Validate the YouTube URL format.
    """
    for pattern in YT_PATTERNS:
        if re.match(pattern, url):
            return True
    return False


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.
    """
    for pattern in YT_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_video_metadata(url: str) -> dict:
    """
    Fetch video metadata (title, author) via YouTube oEmbed API.
    Returns a dict with title and author, falling back to placeholders on error.
    """
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        with urllib.request.urlopen(oembed_url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return {
                "title": data.get("title", "Unknown Title"),
                "author": data.get("author_name", "Unknown Author")
            }
    except Exception:
        video_id = extract_video_id(url)
        return {
            "title": f"Video {video_id}" if video_id else "Unknown Video",
            "author": "Unknown Author"
        }