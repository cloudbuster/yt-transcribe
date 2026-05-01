from pydantic import BaseModel, HttpUrl

class VideoSource(BaseModel):
    url: HttpUrl
    type: str  # e.g., 'youtube', 'vimeo', etc.

class TranscriptionTask(BaseModel):
    video_source: VideoSource
    transcript_url: HttpUrl = None
    transcription_status: str = 'pending'  # e.g., 'pending', 'completed', 'failed'
    transcription_text: str = None
