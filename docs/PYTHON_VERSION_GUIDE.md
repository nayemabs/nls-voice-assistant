# Python Version Guide

## Recommended: Python 3.11

For the best experience with **all features** including Coqui TTS (better quality text-to-speech), use **Python 3.11**.

---

## Why Python 3.11?

- ✅ **Full compatibility** with all packages
- ✅ **Coqui TTS support** (better voice quality than pyttsx3)
- ✅ **PyTorch** support
- ✅ **OpenAI Whisper** support
- ✅ **All other dependencies** work perfectly

---

## Installation Options

### Option 1: Install Python 3.11 (Recommended)

**macOS (using Homebrew)**:
```bash
brew install python@3.11
```

**macOS (using pyenv)**:
```bash
# Install pyenv if not already installed
brew install pyenv

# Install Python 3.11
pyenv install 3.11.9
pyenv global 3.11.9
```

**Linux (Ubuntu/Debian)**:
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**Windows**:
Download from [python.org](https://www.python.org/downloads/) and install Python 3.11.x

---

### Option 2: Use Python 3.13 (Limited Features)

If you must use Python 3.13, the system will work but:
- ❌ Coqui TTS **not available** (will automatically fall back to pyttsx3)
- ✅ All other features work normally
- ✅ Project still meets all requirements

---

## Setup Instructions

### With Python 3.11 (Full Features)

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"

# Run the Python 3.11 setup script
./setup_venv_py311.sh

# Or manually:
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### With Python 3.13 (Limited TTS)

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"

# Use regular setup
./setup_venv.sh

# System will automatically use pyttsx3 instead of Coqui TTS
```

---

## Verifying Your Setup

After installation, check which TTS is available:

```bash
source venv/bin/activate
python -c "from modules.tts import COQUI_AVAILABLE; print(f'Coqui TTS available: {COQUI_AVAILABLE}')"
```

**Output**:
- `Coqui TTS available: True` → Python 3.11, full features ✅
- `Coqui TTS available: False` → Python 3.13, using pyttsx3 instead ⚠️

---

## TTS Quality Comparison

| Feature | Coqui TTS (Python 3.11) | pyttsx3 (Any Python) |
|---------|------------------------|----------------------|
| **Voice Quality** | ⭐⭐⭐⭐⭐ Natural, human-like | ⭐⭐⭐ Robotic |
| **Languages** | Multiple models available | System dependent |
| **Speed** | Slower (neural network) | Fast |
| **Setup** | Requires Python 3.11 | Works anywhere |
| **File Size** | Large models (~100MB) | Small |

---

## Docker Note

The Docker container uses **Python 3.11** to ensure all features work including Coqui TTS.

```bash
docker build -t voice-assistant .
docker run -it voice-assistant
```

Docker will have full Coqui TTS support regardless of your host Python version.

---

## Recommendation

**For development and testing**:
- Use Python 3.11 for best experience
- Coqui TTS provides much better voice quality

**For quick testing**:
- Python 3.13 works fine with pyttsx3
- All core functionality is identical

**For submission**:
- Docker uses Python 3.11 automatically
- Evaluators get full Coqui TTS experience

---

## Troubleshooting

### "Command 'python3.11' not found"

Install Python 3.11 first (see installation options above).

### TTS still using pyttsx3 with Python 3.11

1. Check Python version: `python --version`
2. Reinstall in clean venv:
   ```bash
   rm -rf venv
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Want to force pyttsx3 even with Python 3.11?

Edit [main.py](main.py) line where TTSModule is initialized:
```python
self.tts = TTSModule(use_coqui=False)  # Force pyttsx3
```

---

## Summary

| Python Version | Coqui TTS | pyttsx3 | Recommended |
|----------------|-----------|---------|-------------|
| 3.11 | ✅ Yes | ✅ Yes (fallback) | ⭐ **Best** |
| 3.12 | ❌ No | ✅ Yes | ⚠️ OK |
| 3.13 | ❌ No | ✅ Yes | ⚠️ OK |

**Bottom line**: Use Python 3.11 for the complete experience with high-quality TTS!
