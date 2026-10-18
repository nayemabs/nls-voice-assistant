# Voice Assistant - Complete Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Running the Assistant](#running-the-assistant)
3. [Docker Usage](#docker-usage)
4. [Testing](#testing)
5. [Milestones](#milestones)
6. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Microphone (for voice mode)
- Docker (for containerized deployment)

### Step 1: Install System Dependencies

**On macOS:**
```bash
brew install portaudio ffmpeg espeak
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio ffmpeg espeak-ng
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Note**: The first run will download the Whisper model (~150MB for base model).

---

## Running the Assistant

### Text Mode (Recommended for Testing)
```bash
python main.py --text
```

Interact via keyboard input. This is faster and more reliable for development and testing.

### Voice Mode
```bash
python main.py
```

Speak to the assistant using your microphone. Press Ctrl+C to exit.

### Custom Calendar ID
```bash
python main.py --text --calendar-id your_team_id_here
```

Replace `your_team_id_here` with a unique identifier for your team.

---

## Docker Usage

### Build the Docker Image
```bash
docker build -t voice-assistant .
```

### Run in Text Mode (Default)
```bash
docker run -it voice-assistant
```

### Run in Voice Mode (Requires Audio Device Access)
```bash
docker run -it --device /dev/snd voice-assistant python main.py
```

### Run with Custom Calendar ID
```bash
docker run -it voice-assistant python main.py --text --calendar-id your_team_001
```

---

## Testing

### Test Required Commands
```bash
python test_commands.py
```

This will test all 7 required commands from the project specification:
1. "What will the weather be like today in Marburg?"
2. "What will the weather be on Friday in Frankfurt?"
3. "Will it rain there on Saturday?"
4. "Where is my next appointment?"
5. "Add an appointment titled XYZ for the 12th of January."
6. "Delete the previously created appointment."
7. "Change the place for my appointment tomorrow."

### Test Individual Modules

**Test ASR:**
```bash
cd modules
python asr.py
```

**Test TTS:**
```bash
cd modules
python tts.py
```

**Test Weather API:**
```bash
cd modules
python weather_api.py
```

**Test Calendar API:**
```bash
cd modules
python calendar_api.py
```

**Test NLU:**
```bash
cd modules
python nlu.py
```

---

## Milestones

### Milestone 1: ASR and TTS (Due: 14.11.2025) ✓
- [x] Implement ASR module using Whisper
- [x] Implement TTS module using pyttsx3/Coqui TTS
- [x] Test voice input and output

**Deliverable**: Working code in `modules/asr.py` and `modules/tts.py`

### Milestone 2: API Integration (Due: 28.11.2025) ✓
- [x] Implement Weather API client
- [x] Implement Calendar API client with full CRUD
- [x] Test API connections

**Deliverable**: Working code in `modules/weather_api.py` and `modules/calendar_api.py`

### Milestone 3: Working Voice Assistant (Due: 12.12.2025) ✓
- [x] Implement NLU module
- [x] Implement dialogue management
- [x] Implement NLG module
- [x] Integrate all components in main.py
- [x] Test all required commands

**Deliverable**: Complete working system

### Milestone 4: Docker + Evaluation (Due: 30.01.2025)
- [x] Create Dockerfile
- [ ] Run comprehensive evaluation
- [ ] Complete evaluation report
- [ ] Final testing and bug fixes

**Deliverable**: Docker container + evaluation report (max 2 pages + title sheet)

---

## Example Interactions

### Weather Queries
```
You: What's the weather in Marburg today?
Assistant: The weather in Marburg today will be few clouds, with temperatures between 7 and 15 degrees Celsius.

You: Will it rain there on Friday?
Assistant: Yes, it will rain in Marburg on Friday. The weather will be rain.
```

### Calendar Management
```
You: Where is my next appointment?
Assistant: Your appointment 'Team Meeting' is at Room 12, from Monday, November 03 at 09:00 AM to Monday, November 03 at 10:00 AM.

You: Add an appointment titled Project Review for tomorrow at 2 PM.
Assistant: I've successfully created the appointment 'Project Review'.

You: Change the location to Room 15.
Assistant: I've successfully updated the appointment.

You: Delete that appointment.
Assistant: I've successfully deleted the appointment.
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Microphone not detected
**Solution**:
1. Check system audio settings
2. Test with text mode: `python main.py --text`
3. Verify PyAudio installation:
   ```bash
   python -c "import pyaudio"
   ```

### Issue: Whisper model download fails
**Solution**:
1. Check internet connection
2. Manually download model:
   ```python
   import whisper
   whisper.load_model("base")
   ```

### Issue: TTS not working
**Solution**: The system automatically falls back to pyttsx3 if Coqui TTS fails. Check console output for errors.

### Issue: API connection errors
**Solution**:
1. Check internet connection
2. Verify API endpoints are accessible:
   ```bash
   curl -X POST -d "place=Marburg" https://api.responsible-nlp.net/weather.php
   curl https://api.responsible-nlp.net/calendar.php?calenderid=test
   ```

### Issue: Calendar ID conflicts
**Solution**: Use a unique calendar ID for your team:
```bash
python main.py --text --calendar-id unique_team_name_2025
```

---

## Project Structure
```
.
├── main.py                          # Main voice assistant orchestrator
├── modules/
│   ├── __init__.py
│   ├── asr.py                       # Automatic Speech Recognition
│   ├── tts.py                       # Text-to-Speech
│   ├── nlu.py                       # Natural Language Understanding
│   ├── dialogue.py                  # Dialogue Management
│   ├── nlg.py                       # Natural Language Generation
│   ├── weather_api.py               # Weather API client
│   └── calendar_api.py              # Calendar API client
├── test_commands.py                 # Test script for required commands
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker configuration
├── README.md                        # Project overview
├── USAGE_GUIDE.md                   # This file
├── evaluation_report_template.md   # Evaluation report template
└── Project Description.pdf          # Original project specification
```

---

## Development Tips

1. **Use text mode during development** for faster iteration
2. **Test modules independently** before integration
3. **Check console output** for debugging information
4. **Use unique calendar IDs** to avoid conflicts with other teams
5. **Test with the provided test script** before submission

---

## Submission Checklist

- [ ] All required commands work correctly
- [ ] Docker container builds successfully
- [ ] Evaluation report completed (max 2 pages + title sheet)
- [ ] All team members listed with matriculation IDs
- [ ] Code is well-commented and documented
- [ ] No cloud models used (except for required APIs)
- [ ] Conversation history tracking implemented
- [ ] Context resolution works for references to previous turns

---

## Support

For issues or questions:
1. Check this usage guide
2. Review the project description PDF
3. Test individual modules to isolate problems
4. Check the console output for error messages
5. Consult the course materials and lecture notes

Good luck with your project! 🎉
