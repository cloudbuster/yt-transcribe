# 🎬 YouTube Transcript Downloader & Analyst

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-red.svg)](https://docs.pydantic.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-ready-orange.svg)](https://ollama.com/)

A modular, Unix-style pipeline for extracting, standardizing, and summarizing YouTube transcripts. Designed for researchers, developers, and power users who need high-density insights from video content.

---

## ✨ Features

- **🚀 Modular Pipeline**: Chain stages together using standard pipes or run them as standalone tools.
- **🛡️ Pydantic Validation**: Strict schema enforcement ensures data integrity across the entire workflow.
- **🏷️ Real Metadata**: Automatically fetches video titles and channel authors via the YouTube oEmbed API—no API key required.
- **🧠 AI Summarization**: Connects to **Ollama** (local or remote) to generate high-fidelity academic summaries.
- **🌍 Language Support**: Intelligent fallback logic to find the best available transcript (Manual > English > Auto-generated).

---

## 🛠️ Installation

This project uses `uv` for lightning-fast dependency management.

```bash
# Clone the repository
git clone https://github.com/yourusername/yt-transcript-downloader.git
cd yt-transcript-downloader

# Install dependencies using uv
uv sync
```

*Required dependencies: `pydantic`, `youtube-transcript-api`, `ollama`, `textual`, `httpx`.*

---

## ⚙️ Configuration

The project features a built-in TUI configurator to set up your LLM provider (Local or Cloud).

### 🖥️ Run the Configurator
```bash
uv run yt-config
```
This will guide you through:
- **Local Providers**: Ollama, LM Studio (with automatic model discovery).
- **Cloud Providers**: Gemini, OpenAI, Anthropic (secure API key storage).
- **Persistence**: Securely saving your settings to a standardized `config.json`.

---

## 🚀 Usage

### 🏭 The Factory (Recommended)
The simplest way to run the full pipeline:
```bash
uv run yt-factory "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 📝 Saving Markdown alongside Summary
If you want to save a `.md` transcript file while generating the summary:
```bash
uv run yt-factory "https://www.youtube.com/watch?v=VIDEO_ID" --markdown
```

### 🧬 Individual Stages
Each script is designed to be a discrete "processor" in the pipeline:

| Script | Role | CLI Command | Output |
| :--- | :--- | :--- | :--- |
| `main.py` | Gatekeeper | `yt-check` | Sanitized URL |
| `download_transcript.py` | Harvester | `yt-download` | JSON or Markdown |
| `summarize_transcript.py` | Analyst | `yt-summarize` | AI Analysis |

**Example of manual chaining:**
```bash
uv run yt-download "URL" | uv run yt-summarize
```

---

## 🛠️ Developer Information

### Configuration Precedence
1. `config.json` (created by `yt-config`)
2. Environment variables (`OLLAMA_HOST`, `OLLAMA_MODEL`)
3. Internal defaults

---

## 📐 Architecture & Specs

For a deep dive into the data models, Pydantic schemas, and API integration details, see [SPECIFICATIONS.md](./SPECIFICATIONS.md).

## 📄 License
MIT License - feel free to use and adapt for your own research pipelines.
