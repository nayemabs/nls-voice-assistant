# Optimized ASR and TTS Engines

## Overview

This project now uses high-performance, cross-platform ASR and TTS engines:

- **ASR**: faster-whisper (4x faster than openai-whisper, same accuracy)
- **TTS**: Piper TTS (fast neural voice synthesis, cross-platform)

Both engines are:
- **Cross-platform**: Work on macOS, Linux, Windows
- **Docker-friendly**: No system dependencies required
- **Production-ready**: Better performance and quality than fallback engines

## Architecture

### Automatic Engine Selection

The system automatically detects and uses the best available engines:

```python
# Priority order:
# ASR: faster-whisper > openai-whisper
# TTS: Piper TTS > pyttsx3
```

If optimized engines are not available, the system falls back to:
- ASR: Standard Whisper (from modules/asr.py)
- TTS: pyttsx3 (from modules/tts.py or tts_fast.py)

### Module Structure

- `modules/asr_fast.py` - faster-whisper implementation
- `modules/tts_fast.py` - Piper TTS implementation
- `modules/asr.py` - Fallback Whisper implementation
- `modules/tts.py` - Fallback pyttsx3 implementation

## faster-whisper (ASR)

### Features

- **4x faster** than openai-whisper
- **Same accuracy** as original Whisper
- Uses CTranslate2 for optimized inference
- Supports CPU and GPU (CUDA)
- Quantization support (int8, float16, float32)

### Configuration

Current settings in `modules/asr_fast.py`:

```python
model_size = "small"        # 244M parameters (recommended)
device = "cpu"              # or "cuda" for GPU
compute_type = "int8"       # fastest, recommended for CPU
```

### Model Sizes

| Model    | Parameters | Speed      | Accuracy | Use Case           |
|----------|------------|------------|----------|--------------------|
| tiny     | 39M        | Very Fast  | Low      | Testing only       |
| base     | 74M        | Fast       | OK       | Quick testing      |
| small    | 244M       | Medium     | Good     | **Production** ✓   |
| medium   | 769M       | Slow       | Great    | High accuracy      |
| large-v3 | 1550M      | Very Slow  | Best     | Maximum accuracy   |

### Optimizations

- **VAD (Voice Activity Detection)**: Removes silence automatically
- **Beam search**: beam_size=5 for better accuracy
- **Deterministic**: temperature=0.0 (no randomness)
- **Best of 5**: Tries 5 decodings, picks best
- **Dynamic energy threshold**: Adapts to ambient noise

## Piper TTS

### Features

- **Fast**: Neural TTS with minimal latency
- **High quality**: Natural-sounding voices
- **Cross-platform**: Works on macOS, Linux, Windows, Docker
- **Offline**: No internet required after initial download
- **Multiple voices**: Support for different languages and accents

### Configuration

Current settings in `modules/tts_fast.py`:

```python
voice_name = "en_US-lessac-medium"  # Natural male voice (recommended)
```

### Available Voices

| Voice                  | Language | Gender | Quality | Description        |
|------------------------|----------|--------|---------|-------------------|
| en_US-lessac-medium    | English  | Male   | High    | Natural (default) |
| en_US-amy-medium       | English  | Female | High    | Natural           |
| en_GB-alan-medium      | English  | Male   | High    | British accent    |

### Voice Download

Voices are automatically downloaded on first use:
- Downloaded to: `~/.local/share/piper-tts/`
- Size: ~15-20MB per voice
- No internet required after download

## Installation

### Requirements

Already included in `requirements.txt`:

```txt
# Optimized engines (recommended)
faster-whisper>=1.0.0
piper-tts>=1.2.0

# Fallback engines
pyttsx3>=2.90
openai-whisper
```

### Install Dependencies

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
source venv/bin/activate
pip install -r requirements.txt
```

## Testing

### Test faster-whisper ASR

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
source venv/bin/activate
python modules/asr_fast.py
```

This will:
1. Load faster-whisper "small" model
2. Listen to microphone
3. Transcribe and display text

### Test Piper TTS

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
source venv/bin/activate
python modules/tts_fast.py
```

This will:
1. Download Piper voice (if needed)
2. Load Piper TTS
3. Speak test sentence
4. Play audio

### Test Full System

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
source venv/bin/activate
python main.py
```

## Docker Support

Both engines work perfectly in Docker containers:

### Dockerfile Example

```dockerfile
FROM python:3.11-slim

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Run assistant
CMD ["python", "main.py"]
```

### Key Advantages in Docker

1. **No audio libraries needed**: Piper TTS doesn't require espeak or festival
2. **Faster startup**: faster-whisper loads models quickly
3. **Smaller images**: Fewer system dependencies
4. **Cross-platform**: Same image works on Linux, macOS, Windows hosts

## Performance Comparison

### ASR Performance

| Engine          | Model | Transcription Time | Real-time Factor |
|-----------------|-------|--------------------|------------------|
| openai-whisper  | small | ~4.0s (5s audio)  | 0.8x             |
| faster-whisper  | small | ~1.0s (5s audio)  | 5.0x (4x faster) |

### TTS Performance

| Engine     | Quality | Latency  | CPU Usage | Platform Support |
|------------|---------|----------|-----------|------------------|
| Coqui TTS  | High    | ~600ms   | High      | Limited          |
| pyttsx3    | Low     | Instant  | Low       | Good             |
| Piper TTS  | High    | ~100ms   | Medium    | Excellent        |

## Troubleshooting

### faster-whisper Issues

**Error: "Could not load model"**
- Check model_size is valid (tiny, base, small, medium, large-v3)
- Ensure enough RAM (small model needs ~2GB)
- Try smaller model: `model_size="tiny"`

**Slow transcription**
- Use int8 quantization: `compute_type="int8"`
- Reduce model size: `model_size="base"`
- Enable GPU if available: `device="cuda"`

### Piper TTS Issues

**Error: "Failed to download voice"**
- Check internet connection
- Ensure write permissions to `~/.local/share/piper-tts/`
- Try manual download from Piper voice repository

**No audio output**
- Check system audio player (afplay on macOS, aplay on Linux)
- Verify audio file created in `~/.local/share/piper-tts/`
- System will fall back to pyttsx3 automatically

### Fallback Behavior

If optimized engines fail, system automatically falls back:

```
faster-whisper fails → openai-whisper (modules/asr.py)
Piper TTS fails → pyttsx3 (modules/tts_fast.py)
```

## Advanced Configuration

### Change Whisper Model

Edit `main.py` line 57:

```python
self.asr = ASRModule(model_size="medium")  # More accurate, slower
```

### Change Piper Voice

Edit `main.py` line 60:

```python
self.tts = TTSModule(use_piper=True, voice_name="en_US-amy-medium")  # Female voice
```

### Enable GPU Acceleration

Edit `modules/asr_fast.py` line 14:

```python
def __init__(self, model_size="small", device="cuda", compute_type="float16"):
```

Requires NVIDIA GPU with CUDA support.

## Production Recommendations

### For Speed
- ASR: `faster-whisper` with `model_size="small"`, `compute_type="int8"`
- TTS: `Piper TTS` with `voice_name="en_US-lessac-medium"`

### For Accuracy
- ASR: `faster-whisper` with `model_size="medium"`, `compute_type="float16"`
- TTS: `Piper TTS` with any voice

### For Docker
- Use optimized engines (faster-whisper + Piper TTS)
- Minimal system dependencies required
- Fast startup and execution

## References

- faster-whisper: https://github.com/guillaumekln/faster-whisper
- Piper TTS: https://github.com/rhasspy/piper
- Whisper: https://github.com/openai/whisper
- CTranslate2: https://github.com/OpenNMT/CTranslate2
