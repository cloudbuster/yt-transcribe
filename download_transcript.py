#!/usr/bin/env python3
"""
YouTube Transcript Downloader

This module provides functionality to download YouTube video transcripts and save them as JSON.
Supports multi-language fetching with robust fallback logic using youtube-transcript-api.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from utils import (
    sanitize_url, 
    is_valid_youtube_url, 
    extract_video_id, 
    get_video_metadata,
    TranscriptData,
    TranscriptMetadata
)


def get_transcript_robustly(video_id: str, language: str | None = None) -> str | None:
    """
    Fetch transcript using youtube-transcript-api with fallback to English.
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import NoTranscriptFound
    
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        # Languages to try in order
        langs = [language] if language else []
        langs.extend(['en', 'en-US', 'en-GB'])
        
        try:
            transcript = transcript_list.find_transcript(langs)
            segments = transcript.fetch()
        except NoTranscriptFound:
            # Last resort: take the first available
            segments = next(iter(transcript_list)).fetch()
            
        # Handle both dict-based and object-based snippets
        text_parts = []
        for s in segments:
            if isinstance(s, dict):
                text_parts.append(s.get("text", ""))
            else:
                text_parts.append(getattr(s, "text", ""))
        
        return " ".join(text_parts).strip()
            
    except Exception as e:
        print(f"❌ Error fetching transcript: {e}", file=sys.stderr)
        return None


def download_transcript(url: str, output_dir: str = ".", language: str | None = None, output_json: bool = False, output_md: bool = False) -> bool:
    """
    Main logic to download transcript and process metadata.
    """
    from rich.console import Console
    from rich.status import Status
    
    console = Console(stderr=True)
    url = sanitize_url(url)
    
    if not is_valid_youtube_url(url):
        console.print(f"[bold red]❌ Invalid URL:[/bold red] {url}")
        return False
    
    video_id = extract_video_id(url)
    
    with Status(f"[bold blue]Processing {video_id}...", console=console) as status:
        # 1. Fetch Metadata
        status.update("[bold blue]Fetching video metadata...")
        metadata_raw = get_video_metadata(url)
        
        # 2. Fetch Transcript
        status.update("[bold blue]Downloading transcript...")
        full_text = get_transcript_robustly(video_id, language)
        if not full_text:
            return False
        
        # 3. Construct Pydantic Model
        data = TranscriptData(
            url=url,
            title=metadata_raw["title"],
            transcript=full_text,
            metadata=TranscriptMetadata(
                timestamp=datetime.now(timezone.utc).isoformat(),
                word_count=len(full_text.split()),
                language=language or "auto",
                author=metadata_raw["author"]
            )
        )
    
    # Handle Markdown saving (if requested)
    if output_md:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{video_id}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data.to_markdown())
        console.print(f"[bold green]✅ Saved Markdown to:[/bold green] {file_path}")

    # Handle Primary Output (JSON or File)
    if output_json:
        # Standardize: use model_dump_json() for consistent output
        print(data.model_dump_json(), flush=True)
    elif not output_md:
        # Save JSON file only if not outputting to stdout AND not already saved a MD file 
        # (Actually, we can always save JSON if not outputting JSON to stdout)
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / f"{video_id}_transcript.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data.model_dump_json(indent=2))
        
        console.print(f"[bold green]✅ Saved JSON to:[/bold green] {file_path}")
        console.print(f"[bold cyan]📝 Title:[/bold cyan] {data.title}")
        console.print(f"[bold yellow]📊 Words:[/bold yellow] {data.metadata.word_count}")
    
    return True


def main():
    # Detect if we should output JSON based on piping or flag
    is_piped = not sys.stdin.isatty()
    output_json = not sys.stdout.isatty() or '--json' in sys.argv or '-j' in sys.argv
    output_md = '--markdown' in sys.argv or '-m' in sys.argv
    
    if is_piped:
        url = sys.stdin.read().strip()
    elif len(sys.argv) > 1:
        # Filter out flags to find the URL
        args = [a for a in sys.argv[1:] if not a.startswith('-')]
        url = args[0] if args else ""
    else:
        print("Usage: python download_transcript.py <URL> [--markdown]", file=sys.stderr)
        sys.exit(1)

    if not url:
        print("Error: No URL provided", file=sys.stderr)
        sys.exit(1)

    success = download_transcript(url, output_json=output_json, output_md=output_md)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
