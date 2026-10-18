# Voice Mode Improvements Guide

## What Was Improved

### ASR (Speech Recognition) Improvements

1. **Better Whisper Model**: Changed from "base" to "small" model
   - Base: ~139M parameters, faster but less accurate
   - Small: ~244M parameters, better accuracy (recommended)
   - Medium: ~769M parameters, even better (slower)

2. **Improved Audio Settings**:
   - Energy threshold: 300 (more sensitive to speech)
   - Dynamic energy threshold: Adapts to ambient noise
   - Pause threshold: 0.8 seconds (better phrase detection)
   - Sample rate: 16kHz (optimal for Whisper)
   - Ambient noise calibration: 1 second (better noise filtering)

3. **Better Transcription Settings**:
   - Temperature: 0.0 (more deterministic, less random)
   - Best of: 5 (tries 5 decodings, picks best)
   - Beam size: 5 (better accuracy with beam search)
   - No previous text conditioning (cleaner results)

4. **Longer phrase time**: 15 seconds instead of 10 (for longer sentences)

### TTS (Speech Output) Improvements

- Now uses **Coqui TTS** by default (high-quality neural TTS)
- Fallback to pyttsx3 if Coqui fails

## How to Use Voice Mode

### Basic Usage

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
source venv/bin/activate
python main.py
```

### Tips for Better Recognition

1. **Environment**:
   - Use in a quiet room
   - Reduce background noise
   - Keep microphone at consistent distance

2. **Speaking**:
   - Speak clearly and at normal pace
   - Don't rush or speak too slowly
   - Wait for "Listening..." prompt before speaking
   - Finish your sentence and pause for 0.8 seconds

3. **Microphone**:
   - Built-in Mac microphone works fine
   - External microphone may be better
   - Check System Preferences → Sound → Input for levels

### Choosing Model Size

You can change the model in `main.py` line 43:

```python
# Fast (less accurate):
self.asr = ASRModule(model_size="tiny")   # Fastest
self.asr = ASRModule(model_size="base")   # Fast

# Balanced (recommended):
self.asr = ASRModule(model_size="small")  # Good balance ✓

# Accurate (slower):
self.asr = ASRModule(model_size="medium") # Very accurate
self.asr = ASRModule(model_size="large")  # Most accurate, very slow
```

## Testing Speech Recognition

Test your microphone and Whisper accuracy:

```bash
cd "/Users/nayemabs/Study/Marburg/Winter 25/NLS/Project"
source venv/bin/activate
python modules/asr.py
```

This will:
1. Load the Whisper model
2. Listen to your microphone
3. Show what it transcribed

## Common Issues

### "No speech detected"
- Speak louder or closer to microphone
- Check microphone permissions in System Preferences
- Try increasing timeout in `main.py`

### Incorrect transcriptions
- Upgrade to "medium" model (slower but more accurate)
- Speak more clearly
- Reduce background noise
- Check microphone quality

### "Could not find PyAudio"
Install PyAudio:
```bash
brew install portaudio
source venv/bin/activate
pip install pyaudio
```

## Model Comparison

| Model  | Size   | Speed      | Accuracy | Recommended For          |
|--------|--------|------------|----------|-------------------------|
| tiny   | 39M    | Very Fast  | Low      | Testing only            |
| base   | 74M    | Fast       | OK       | Quick testing           |
| small  | 244M   | Medium     | Good     | **Production (default)**|
| medium | 769M   | Slow       | Great    | High accuracy needed    |
| large  | 1550M  | Very Slow  | Best     | Maximum accuracy        |

## Current Settings (After Improvements)

- **Model**: small (244M parameters)
- **Language**: English
- **Sample Rate**: 16kHz
- **Ambient Noise Calibration**: 1.0 seconds
- **Energy Threshold**: 300
- **Pause Threshold**: 0.8 seconds
- **Phrase Time Limit**: 15 seconds
- **Beam Search**: Enabled (size=5)
- **Temperature**: 0.0 (deterministic)

These settings provide the best balance of speed and accuracy for English speech recognition.
