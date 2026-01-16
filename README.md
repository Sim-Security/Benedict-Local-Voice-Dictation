# Benedict - Local Voice Dictation

**Hold a key → Speak → Release → Clean text appears**

100% local • 100% private • Powered by Whisper + Ollama

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

| Feature | Description |
|---------|-------------|
| 🎤 **Live Transcription** | See words appear as you speak |
| 🧹 **Text Cleaning** | Removes "um", "uh", "like" and fixes grammar |
| 📄 **Auto-Documents** | Timestamped session files with organized summaries |
| 📝 **Multiple Modes** | clean, rewrite, bullets, email, raw |
| 🔒 **100% Local** | No cloud APIs, all processing on your machine |

---

## Quick Start

```bash
# Clone and enter the project
git clone https://github.com/Sim-Security/Benedict-Local-Voice-Dictation.git
cd Benedict-Local-Voice-Dictation

# Install dependencies
pip install -r requirements.txt

# Make sure Ollama is running
ollama pull mistral-nemo  # or llama3.2

# Run
python main.py
```

---

## Usage

```bash
python main.py
```

1. Hold **CTRL** and speak naturally
2. Release when done
3. See cleaned text appear + copied to clipboard
4. Press **CTRL+C** to exit and get organized summary

### Options

```bash
python main.py --mode rewrite    # Improve clarity
python main.py --mode bullets    # Convert to bullets
python main.py --mode email      # Format as email
python main.py --mode raw        # No processing
python main.py --hotkey alt      # Use different hotkey
python main.py --no-session      # Don't save to file
python main.py --no-copy         # Don't copy to clipboard
```

---

## Processing Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `clean` | Remove fillers, fix grammar | Quick notes |
| `rewrite` | Professional language | Business comms |
| `bullets` | Convert to bullet points | Meeting notes |
| `email` | Format as email | Quick emails |
| `raw` | No processing | Just transcribe |

---

## Auto-Session Documents

Each dictation session creates a markdown file in `sessions/`:

```markdown
# Project Planning Discussion

**Session Started:** 2026-01-08 13:00

---

## Raw Transcription

**[13:00:15]** First thing I said...
**[13:02:30]** Second thing I said...

---

## Organized Summary

(Auto-generated organized version)
```

---

## Configuration

Copy `.env.example` to `.env`:

```bash
# Model Settings
OLLAMA_MODEL=mistral-nemo
OLLAMA_BASE_URL=http://localhost:11434

# Dictation Settings
DICTATION_HOTKEY=ctrl
DEFAULT_MODE=clean
```

### Recommended Models (RTX 3090)

| Model | Size | Quality | Command |
|-------|------|---------|---------|
| `mistral-nemo` | 7GB | Excellent | `ollama pull mistral-nemo` |
| `llama3.2` | 2GB | Good | `ollama pull llama3.2` |
| `qwen2.5:14b` | 9GB | Excellent | `ollama pull qwen2.5:14b` |

---

## Project Structure

```
benedict/
├── main.py              # CLI entry point
├── src/
│   ├── transcriber.py   # Whisper STT with live display
│   ├── text_processor.py # LangChain text cleaning
│   ├── session_manager.py # Auto-document creation
│   └── document_editor.py # Post-session refining
├── sessions/            # Auto-generated session docs
├── requirements.txt
└── README.md
```

---

## Tech Stack

- **Speech-to-Text**: [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) (Whisper)
- **Text Processing**: [LangChain](https://python.langchain.com/) + [Ollama](https://ollama.com/)
- **Hotkeys**: [keyboard](https://github.com/boppreh/keyboard)

---

## License

MIT
