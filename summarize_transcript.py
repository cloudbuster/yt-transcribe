#!/usr/bin/env python3
"""
YouTube Transcript Summarizer

This module provides functionality to generate academic summaries of YouTube video transcripts
using a local LLM via Ollama (qwen3:8b).

Requires: ollama package and a running Ollama instance with qwen3:8b model.
"""

import json
import os
import sys
from pathlib import Path
import ollama
from typing import Optional
from utils import TranscriptData, load_config, ServiceName, ProviderType

# Default Fallbacks (Legacy)
DEFAULT_OLLAMA_HOST = 'http://100.94.41.13:11434'
DEFAULT_OLLAMA_MODEL = 'qwen3:8b'


def get_llm_config():
    """Retrieve config from file or environment."""
    config = load_config()
    if config:
        return config
    
    # Fallback to environment variables
    return {
        "provider": ProviderType.LOCAL,
        "service": ServiceName.OLLAMA,
        "url": os.environ.get('OLLAMA_HOST', DEFAULT_OLLAMA_HOST),
        "model": os.environ.get('OLLAMA_MODEL', DEFAULT_OLLAMA_MODEL),
        "api_key": None
    }


def generate_summary(data: TranscriptData, max_length: int = 10000) -> str:
    """
    Generate an academic summary of the transcript using the configured LLM.
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    import httpx
    
    console = Console()
    config = get_llm_config()
    
    # Extract config values (handling both object and dict for safety)
    if hasattr(config, "model"):
        service = config.service
        url = config.url
        model = config.model
        api_key = config.api_key
    else:
        service = config["service"]
        url = config["url"]
        model = config["model"]
        api_key = config["api_key"]

    # Truncate transcript for context window safety
    text = data.transcript[:max_length]
    
    console.print(f"\n[bold cyan]📝 Summarizing:[/bold cyan] {data.title}")
    console.print(f"   [dim]Provider:[/dim] {service.upper()} ({model})")
    console.print(f"   [dim]Words:[/dim] {data.metadata.word_count}")

    prompt = f"""Task: Provide a high-density academic summary of the following transcript.
    Video Title: {data.title}
    Author: {data.metadata.author or 'Unknown'}

    Constraints:
    1. **Thesis**: One high-impact sentence on the core premise.
    2. **Strategic Insights**: 5-7 bullet points of the most valuable information.
    3. **Logical Flow**: A brief description of the argumentative structure.

    Transcript:
    {text}
    """

    try:
        from rich.markdown import Markdown
        full_response = []
        
        with Live(console=console, refresh_per_second=10) as live:
            # Show a simple status while waiting for the first chunk
            live.update("[bold yellow]⚙️ AI is thinking...[/bold yellow] [dim]Analyzing transcript...[/dim]")
            
            if service == ServiceName.OLLAMA:
                client = ollama.Client(host=url)
                response = client.generate(model=model, prompt=prompt, stream=True)
                for chunk in response:
                    content = chunk.get('response', '')
                    full_response.append(content)
                    live.update(Markdown("".join(full_response)))
            
            elif service == ServiceName.LM_STUDIO:
                # LM Studio uses OpenAI compatible chat completions
                openai_url = f"{url}/v1/chat/completions"
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True
                }
                with httpx.stream("POST", openai_url, json=payload, timeout=60.0) as r:
                    for line in r.iter_lines():
                        if line.startswith("data: "):
                            if line.strip() == "data: [DONE]":
                                break
                            try:
                                chunk_data = json.loads(line[6:])
                                content = chunk_data["choices"][0]["delta"].get("content", "")
                                full_response.append(content)
                                live.update(Markdown("".join(full_response)))
                            except:
                                continue

            elif service == ServiceName.GEMINI:
                # Basic Gemini implementation via HTTP
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                with httpx.stream("POST", gemini_url, json=payload, timeout=60.0) as r:
                    for line in r.iter_lines():
                        if not line: continue
                        # Gemini returns JSON chunks in an array-like stream
                        try:
                            clean_line = line.lstrip(" ,[").rstrip(" ,]")
                            if not clean_line: continue
                            chunk_data = json.loads(clean_line)
                            content = chunk_data["candidates"][0]["content"]["parts"][0]["text"]
                            full_response.append(content)
                            live.update(Markdown("".join(full_response)))
                        except:
                            continue
            else:
                return f"❌ Service {service} not yet fully implemented for streaming."
            
        # Final clean print for easy copying
        final_md = "".join(full_response)
        console.print("\n---")
        console.print(Markdown(final_md))
        return final_md
        
    except Exception as e:
        console.print(f"❌ {service.upper()} Error: {e}", style="bold red")
        console.print("\n[yellow]💡 Tip:[/yellow] Your configuration might be incorrect or the service is down.")
        console.print("   Run [bold cyan]uv run yt-config[/bold cyan] to update your settings.")
        return ""


def list_models():
    """List available models using the configured service."""
    config = get_llm_config()
    if hasattr(config, "model"):
        service = config.service
        url = config.url
    else:
        service = config["service"]
        url = config["url"]

    if service != ServiceName.OLLAMA:
        print(f"📦 Model listing not yet implemented for {service}.")
        return

    try:
        import ollama
        client = ollama.Client(host=url)
        models = client.list()
        print(f"📦 Models on {url}:")
        for m in models.get('models', []):
            print(f"   - {m['name']}")
    except Exception as e:
        print(f"❌ Failed to fetch models: {e}")


def main():
    if '--list' in sys.argv or '-l' in sys.argv:
        list_models()
        return

    # Read from stdin (expected for the pipeline)
    if not sys.stdin.isatty():
        input_data = sys.stdin.read()
    elif len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            input_data = f.read()
    else:
        print("Usage: cat transcript.json | python summarize_transcript.py", file=sys.stderr)
        sys.exit(1)

    try:
        # Standardize: Use Pydantic to parse the JSON
        data = TranscriptData.model_validate_json(input_data)
        generate_summary(data)
    except Exception as e:
        print(f"❌ Invalid Input: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
