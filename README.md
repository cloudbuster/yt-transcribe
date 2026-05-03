# 🎬 YouTube Transcript Downloader & Analyst

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-red.svg)](https://docs.pydantic.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-ready-orange.svg)](https://ollama.com/)

A modular, Unix-style pipeline for extracting, standardizing, and summarizing YouTube transcripts. Designed for researchers, developers, and power users who need high-density insights from video content.

---

## 📋 Table of Contents
- [✨ Features](#-features)
- [📦 Prerequisites](#-prerequisites)
- [🛠️ Installation](#️-installation)
- [⚙️ Configuration](#️-configuration)
- [🚀 Usage](#-usage)
- [❓ Troubleshooting](#-troubleshooting)
- [📐 Architecture](#-architecture)

---

## ✨ Features

- **🚀 Modular Pipeline**: Chain stages together using standard pipes (`|`) or run them as a single command via the Factory.
- **🛡️ Pydantic Validation**: Strict schema enforcement ensures data integrity across the entire workflow.
- **🏷️ Metadata Enrichment**: Automatically fetches video titles and channel authors via oEmbed—no API key required.
- **🧠 AI Summarization**: Connects to **Ollama**, **LM Studio**, or **Google Gemini** for high-fidelity summaries.
- **🌍 Global Compatibility**: Works on Windows, macOS, and Linux with native handling of platform-specific quirks.

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:
1. **Python 3.10+**
2. **[uv](https://github.com/astral-sh/uv)**: The recommended package manager for this project.
3. **Local LLM Service (Optional)**: 
   - [Ollama](https://ollama.com/) (Recommended)
   - [LM Studio](https://lmstudio.ai/)

---

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/yt-transcript-downloader.git
cd yt-transcript-downloader
```

### 2. Set Up the Environment
We use `uv` to manage dependencies. It will automatically handle the virtual environment for you.
```bash
# Sync dependencies
uv sync
```

---

## ⚙️ Configuration

The project features a built-in TUI (Terminal User Interface) configurator to set up your LLM provider.

### 🖥️ Run the Configurator
```bash
uv run yt-config
```

**Key Steps:**
- **Provider**: Choose between **Local** (Ollama/LM Studio) or **Cloud** (Gemini/OpenAI/Anthropic).
- **Discovery**: For Ollama and LM Studio, the tool will automatically try to discover available models from your running service.
- **Cloud Setup**: If using a Cloud provider, you will be prompted for your API Key.
- **Persistence**: Your settings are saved to `config.json` in the root directory.

---

## 🚀 Usage

### 🏭 The Factory (Simplest Way)
The Factory handles the entire pipeline—checking availability, downloading, and summarizing—in one command.

```bash
uv run yt-factory "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Optional: Save a Markdown copy of the transcript**
```bash
uv run yt-factory "URL" --markdown
```

### 🧬 Manual Pipeline (Unix-Style)
If you want more control, you can chain the individual scripts:
```bash
# Stage 1: Check availability -> Stage 2: Download JSON -> Stage 3: Summarize
uv run yt-check "URL" | uv run yt-download | uv run yt-summarize
```

---

## ❓ Troubleshooting

### 1. "Ollama not found" or empty model list
If `yt-config` doesn't show any models:
*   **Is it running?** Make sure you have started the service. On Windows/macOS, look for the tray icon or run:
    ```bash
    ollama serve
    ```
*   **Have you pulled a model?** You must download a model before it appears in the list:
    ```bash
    ollama pull qwen2.5:7b
    ```

### 2. Windows Path Errors
If you see `"The system cannot find the path specified"`, ensure you have the latest version of the code. We have implemented cross-platform fixes to handle the differences between Windows `NUL` and POSIX `/dev/null`.

### 3. "No transcript found"
Some videos have transcripts disabled by the creator or contain no spoken words. `yt-check` will catch these early and inform you.

---

## 📐 Architecture

| Script | Command | Purpose |
| :--- | :--- | :--- |
| `main.py` | `yt-check` | Validates URL and transcript availability. |
| `download_transcript.py` | `yt-download` | Fetches metadata and raw transcript data. |
| `summarize_transcript.py` | `yt-summarize` | Sends data to LLM and streams the summary. |
| `configure.py` | `yt-config` | TUI for managing `config.json`. |

For more detailed technical specs, see [SPECIFICATIONS.md](./SPECIFICATIONS.md).

---

## 📄 License
MIT License. Created by [Your Name/Github].
