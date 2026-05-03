import sys
from utils import sanitize_url, is_valid_youtube_url, extract_video_id


def check_transcript_availability(video_id: str) -> bool:
    """Check if a transcript is listed for the video."""
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
    
    try:
        api = YouTubeTranscriptApi()
        api.list(video_id)
        return True
    except (NoTranscriptFound, TranscriptsDisabled, Exception):
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <URL>", file=sys.stderr)
        sys.exit(1)
    
    url = sanitize_url(sys.argv[1])
    if not is_valid_youtube_url(url):
        print(f"❌ Invalid YouTube URL", file=sys.stderr)
        sys.exit(1)
    
    video_id = extract_video_id(url)
    if check_transcript_availability(video_id):
        # Output URL to stdout for piping
        print(url)
        sys.exit(0)
    else:
        print(f"⚠️  Transcript disabled or unavailable for: {video_id}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()