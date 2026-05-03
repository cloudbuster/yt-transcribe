#!/usr/bin/env python3
import subprocess
import sys
import os
from utils import sanitize_url, is_valid_youtube_url, extract_video_id
from rich.console import Console
from rich.panel import Panel

console = Console()
error_console = Console(stderr=True)

# Determine the null device based on the operating system
NULL_DEVICE = "NUL" if os.name == "nt" else "/dev/null"

def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/bold red] yt-factory <YouTube URL> [--markdown]")
        sys.exit(1)

    url = sanitize_url(sys.argv[1])
    output_md = '--markdown' in sys.argv or '-m' in sys.argv

    if not is_valid_youtube_url(url):
        console.print(f"[bold red]❌ Error:[/bold red] Invalid YouTube URL: {url}")
        sys.exit(1)

    video_id = extract_video_id(url)
    
    console.print(Panel.fit(
        f"[bold cyan]YouTube Transcript Pipeline[/bold cyan]\n"
        f"[dim]Target ID:[/dim] [green]{video_id}[/green]" + 
        ("\n[dim]Format:[/dim] [yellow]Markdown Export Enabled[/yellow]" if output_md else ""),
        title="🏭 Run Factory",
        border_style="blue"
    ))

    # Construct the pipeline command
    download_cmd = "uv run yt-download"
    if output_md:
        download_cmd += " --markdown"

    full_cmd = (
        f'uv run yt-check "{url}" 2>{NULL_DEVICE} | '
        f'{download_cmd} | '
        f'uv run yt-summarize'
    )
    
    try:
        result = subprocess.run(full_cmd, shell=True, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError:
        error_console.print("\n[bold red]❌ Pipeline failed.[/bold red] [dim]Check if transcript is enabled in Studio.[/dim]")
        sys.exit(1)

if __name__ == "__main__":
    main()