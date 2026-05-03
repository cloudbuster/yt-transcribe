# Technical Specifications: YouTube Transcript Downloader

## 1. Project Overview
The **YouTube Transcript Downloader** is a modular, CLI-driven pipeline designed to automate the extraction, structured storage, and academic summarization of YouTube video transcripts. It prioritizes data integrity through strict typing via Pydantic and streamlined dependency management via `pyproject.toml` and `uv`.

It includes a **TUI Configurator (`yt-config`)** to manage LLM provider settings (Local/Cloud) without manual file editing.

## 2. Core Architecture
The system follows a Unix-style pipe-and-filter architecture, where each stage is a discrete Python script that consumes and produces standardized data.

### 2.1 Stage 1: Gatekeeper (`main.py`)
- **Purpose**: URL validation and pre-flight availability check.
- **Input**: YouTube URL (CLI argument).
- **Logic**: Uses `youtube-transcript-api` to check if any transcript tracks exist without downloading them.
- **Output**: The sanitized URL string to `stdout` (on success) or an error code (on failure).

### 2.2 Stage 2: Harvester (`download_transcript.py`)
- **Purpose**: Metadata enrichment and transcript retrieval.
- **Input**: YouTube URL (CLI argument or `stdin`).
- **Logic**:
    - Fetches video `title` and `author` via the YouTube oEmbed API (`https://www.youtube.com/oembed`).
    - Retrieves transcript segments and joins them into a continuous string.
    - Standardizes data using the `TranscriptData` Pydantic model.
- **Output**: Validated JSON payload to `stdout`, or a structured JSON/Markdown file in the local directory (use `--markdown` for MD).

### 2.3 Stage 3: Analyst (`summarize_transcript.py`)
- **Purpose**: Generates high-density summaries using LLMs.
- **Input**: `TranscriptData` JSON (CLI argument or `stdin`).
- **Logic**:
    - Connects to an Ollama server (local or remote).
    - Applies an academic summarization prompt.
    - Streams the response to the user's terminal.
- **Output**: Markdown-formatted summary to `stdout`.

## 3. Data Models (Pydantic)
Models are defined in `utils.py` to ensure consistency across the pipeline.

### 3.1 `AppConfig`
```python
class AppConfig(BaseModel):
    provider: ProviderType # "local" or "cloud"
    service: ServiceName   # "ollama", "lm-studio", "gemini", etc.
    url: Optional[str]     # Service URL (for local)
    model: str            # Target model name
    api_key: Optional[str] # Key for cloud services
```

### 3.2 `TranscriptMetadata`
```python
class TranscriptMetadata(BaseModel):
    timestamp: str      # ISO 8601 UTC timestamp
    word_count: int     # Total words in transcript
    language: str       # ISO language code or "auto"
    author: Optional[str] # YouTube channel name
```

### 3.3 `TranscriptData`
```python
class TranscriptData(BaseModel):
    url: str            # Original sanitized YouTube URL
    title: str          # Real video title from oEmbed
    transcript: str     # Full concatenated transcript text
    metadata: TranscriptMetadata
```

## 4. Integration Specifications

### 4.1 YouTube oEmbed
- **Endpoint**: `https://www.youtube.com/oembed?url={url}&format=json`
- **Fallback**: If the API fails, the system defaults to `Video {video_id}` for the title and `Unknown Author`.

### 4.2 AI Service Integration
- **Ollama**: Native streaming via the `ollama` Python client.
- **LM Studio**: OpenAI-compatible chat completion API (`/v1/chat/completions`) via `httpx`.
- **Gemini**: Direct streaming via the Google Generative Language API (`v1beta`) via `httpx`.
- **Precedence**: Settings are loaded from `config.json` first, then environment variables (`OLLAMA_HOST`, `OLLAMA_MODEL`), then hardcoded defaults.

## 5. Error Handling
- **Non-blocking Logs**: All status messages and errors are written to `stderr` to avoid polluting the stdout data pipe.
- **Exit Codes**:
    - `0`: Success.
    - `1`: Validation error, connection failure, or missing transcript.
- **Truncation**: Transcripts are capped at 10,000 characters by default before being sent to the LLM to prevent context window overflow.
