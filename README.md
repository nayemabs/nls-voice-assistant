# On-Device Voice Assistant

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Complete-success.svg)]()

A **complete on-device voice assistant** for the Natural Language Systems course at Philipps-Universität Marburg (Winter 2025/26). Provides weather information and calendar management through spoken English interactions.

## Features

- **Automatic Speech Recognition (ASR)** - Faster-Whisper (4x faster than OpenAI Whisper)
- **Natural Language Understanding (NLU)** - Hybrid GLiNER + Regex or pure Regex
- **Natural Language Generation (NLG)** - Template-based response generation
- **Text-to-Speech (TTS)** - Piper neural TTS (high-quality, fast)
- **Weather Queries** - Current and forecast weather for any location
- **Calendar Management** - Full CRUD operations for appointments
- **Conversation Context** - Tracks history and resolves references
- **Docker Support** - Containerized deployment for any CPU

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Voice Assistant Pipeline                 │
├─────────────────────────────────────────────────────────────┤
│  Audio Input → ASR → NLU → Intent Execution → NLG → TTS    │
│                                                              │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌─────────┐    │
│  │ Faster  │   │ Hybrid  │   │ Weather/ │   │  Piper  │    │
│  │ Whisper │ → │ GLiNER  │ → │ Calendar │ → │   TTS   │    │
│  │  (ASR)  │   │  (NLU)  │   │   APIs   │   │         │    │
│  └─────────┘   └─────────┘   └──────────┘   └─────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Native Installation (Recommended for voice mode)

```bash
# Clone and setup
cd Project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run in text mode
python main.py --text

# Run in voice mode (requires microphone)
python main.py --voice
```

### Option 2: Docker (Works on any CPU)

```bash
# Build and run with Hybrid NLU (default)
docker compose up --build voice-assistant

# Run with Regex NLU (faster startup, lighter)
docker compose --profile regex up --build voice-assistant-regex

# Run evaluation
docker compose --profile evaluate up --build evaluator
```

### Option 3: Docker with NVIDIA GPU

```bash
# Requires nvidia-container-toolkit
docker compose --profile cuda up --build voice-assistant-cuda
```

## Project Structure

```
Project/
├── main.py                    # Main orchestrator
├── evaluate.py                # Evaluation script with SLU metrics
├── create_presentation.py     # PDF report generator
├── modules/
│   ├── asr_fast.py           # Faster-Whisper ASR (primary)
│   ├── asr.py                # Standard Whisper ASR (fallback)
│   ├── nlu_hybrid.py         # Hybrid GLiNER + Regex NLU
│   ├── nlu.py                # Regex-based NLU
│   ├── nlg.py                # Template-based NLG
│   ├── tts_fast.py           # Piper neural TTS (primary)
│   ├── tts.py                # pyttsx3 TTS (fallback)
│   ├── dialogue.py           # Dialogue state management
│   ├── weather_api.py        # Weather API client
│   └── calendar_api.py       # Calendar API client
├── tests/
│   ├── voice_commands_simple.txt  # Test commands
│   └── evaluation/           # Evaluation reports
├── data/                     # Audio test files
├── Dockerfile                # Container configuration
├── docker-compose.yml        # Docker services
└── requirements.txt          # Python dependencies
```

## Technical Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **ASR** | Faster-Whisper (small) | CTranslate2-based, 4x faster than OpenAI Whisper |
| **NLU** | GLiNER + Regex | Zero-shot entity extraction + rule-based intent |
| **NLG** | Template-based | Natural response generation with fillers |
| **TTS** | Piper | Fast neural TTS, works offline |
| **APIs** | REST | Weather & Calendar endpoints |

## Evaluation Metrics

Run the evaluation script to measure system performance:

```bash
# With Hybrid NLU
python evaluate.py --hybrid -d data/Shibin -c tests/voice_commands_simple.txt

# With Regex NLU
python evaluate.py -d data/Shibin -c tests/voice_commands_simple.txt
```

### Metrics Measured

| Category | Metrics |
|----------|---------|
| **ASR** | Word Error Rate (WER), Character Error Rate (CER) |
| **Intent** | Accuracy, Precision, Recall, F1 (per-class and macro) |
| **Slots** | Slot F1 (entity extraction accuracy) |
| **End-to-End** | Semantic Error Rate (SER), Sentence Accuracy |
| **Latency** | ASR, NLU, NLG, Total (ms) |
| **Task Success** | Overall and per-intent success rates |

### Sample Results (Hybrid NLU)

| Metric | Value |
|--------|-------|
| WER | 20.11% |
| Intent Accuracy | 95.65% |
| Slot F1 | 91.70% |
| Sentence Accuracy | 85.09% |
| Avg Total Latency | ~2500ms (CPU) |

## Example Commands

### Weather Queries
- "What's the weather in Marburg today?"
- "Will it rain in Frankfurt tomorrow?"
- "Is it going to be sunny this weekend?"
- "What's the temperature in Berlin on Friday?"

### Calendar Management
- "Add an appointment titled Team Meeting for tomorrow at 9 AM"
- "What are my appointments today?"
- "Delete the Team Meeting appointment"
- "Change the time to 3 PM"
- "Do I have any meetings on Monday?"

## Docker Services

| Service | Profile | Description |
|---------|---------|-------------|
| `voice-assistant` | default, cpu | CPU with Hybrid NLU |
| `voice-assistant-regex` | regex | CPU with Regex NLU (lighter) |
| `voice-assistant-cuda` | cuda, gpu | NVIDIA GPU with Hybrid NLU |
| `evaluator` | evaluate | Batch evaluation with Hybrid NLU |
| `evaluator-regex` | evaluate-regex | Batch evaluation with Regex NLU |
| `voice-assistant-mic` | voice, mic | Linux only, with microphone |

## API Endpoints

### Weather API
- **Endpoint**: `https://api.responsible-nlp.net/weather.php`
- **Method**: POST
- **Parameter**: `place` (location name)

### Calendar API
- **Endpoint**: `https://api.responsible-nlp.net/calendar.php`
- **Methods**: GET, POST, PUT, DELETE
- **CRUD operations** for calendar entries

## Configuration

### Calendar ID
```bash
# Use a unique calendar ID to avoid conflicts
python main.py --text --calendar-id your_unique_team_id
```

### Environment Variables
```bash
WHISPER_MODEL_SIZE=small    # tiny, base, small, medium, large
WHISPER_COMPUTE_TYPE=int8   # int8 (CPU), float16 (GPU)
WHISPER_DEVICE=cpu          # cpu, cuda, auto
USE_HYBRID_NLU=true         # true for GLiNER, false for regex
```

## Team Members

| Name | Matriculation Number |
|------|---------------------|
| Abu Bakar Siddik Nayem | 3875335 |
| Shibin Benny | 3872714 |
| M A Moit Sowrav | 3854501 |
| Muhammad Safkat Uddin Jamie | 3864520 |

**Course**: Natural Language Systems
**University**: Philipps-Universität Marburg
**Semester**: Winter 2025/26

## Testing

### Run Evaluation
```bash
python evaluate.py --hybrid
```

### Test Individual Modules
```bash
python modules/asr_fast.py      # Test Faster-Whisper ASR
python modules/nlu_hybrid.py    # Test Hybrid NLU
python modules/nlg.py           # Test NLG
python modules/weather_api.py   # Test Weather API
python modules/calendar_api.py  # Test Calendar API
```

## Requirements

- Python 3.11+
- ~2GB disk space (models)
- 4GB+ RAM recommended
- Microphone (for voice mode)
- Docker (optional, for containerized deployment)

## License

This project was developed for educational purposes as part of the Natural Language Systems course at Philipps-Universität Marburg.
