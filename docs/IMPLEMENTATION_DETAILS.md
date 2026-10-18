# Implementation Details

## System Architecture

The voice assistant follows a modular pipeline architecture:

```
[Audio Input] → [ASR] → [NLU] → [Dialogue Manager] → [Task Execution] → [NLG] → [TTS] → [Audio Output]
                                         ↓
                                  [Context Store]
                                         ↓
                              [Weather API / Calendar API]
```

---

## Module Descriptions

### 1. ASR Module (`modules/asr.py`)
**Technology**: OpenAI Whisper (base model)

**Key Features**:
- Local speech-to-text conversion
- Microphone input support
- Audio file transcription
- Automatic noise adjustment

**Model Choice Rationale**:
- Base model: Good balance between speed and accuracy
- ~150MB download size
- Supports English language
- No cloud API required

**Performance**:
- Real-time transcription
- ~15% WER on clean audio
- Works offline after initial model download

---

### 2. TTS Module (`modules/tts.py`)
**Technology**: pyttsx3 (primary), Coqui TTS (fallback)

**Key Features**:
- Local text-to-speech synthesis
- Configurable voice properties (rate, volume)
- Audio file output support
- Automatic fallback mechanism

**Implementation Choice**:
- pyttsx3 chosen for reliability and ease of use
- No external dependencies beyond system libraries
- Cross-platform support (macOS, Linux, Windows)

---

### 3. NLU Module (`modules/nlu.py`)
**Technology**: Rule-based with regex patterns

**Intents Supported**:
1. `weather_query` - Weather information requests
2. `get_appointment` - Retrieve calendar entries
3. `create_appointment` - Create new calendar entries
4. `update_appointment` - Modify existing entries
5. `delete_appointment` - Remove calendar entries

**Entity Types**:
- **place**: Location names (e.g., "Marburg", "Frankfurt")
- **day**: Temporal references (e.g., "today", "Friday", "tomorrow")
- **condition**: Weather conditions (e.g., "rain", "snow")
- **title**: Appointment titles
- **location**: Appointment locations
- **time**: Time information
- **date**: Date information
- **temporal_reference**: Anaphoric references (e.g., "there", "previously")

**Pattern Matching**:
- Regular expressions for intent detection
- Entity extraction using capture groups
- Handles variations in phrasing

**Limitations**:
- Limited to predefined patterns
- May miss complex or unusual phrasings
- No learning capability

**Future Improvements**:
- Replace with ML-based NLU (e.g., BERT-based intent classifier)
- Add few-shot learning capability
- Support for more languages

---

### 4. Dialogue Manager (`modules/dialogue.py`)
**Key Features**:
- Conversation history tracking (last 10 turns)
- Context resolution for anaphoric references
- State management
- API result caching

**Context Resolution**:
The system resolves references like:
- "Will it rain **there**?" → Uses location from previous turn
- "Delete **the previously created** appointment" → Uses last created appointment ID

**Implementation**:
```python
# Example context resolution
if current_entities.get('temporal_reference'):
    if 'place' not in resolved and 'place' in self.last_entities:
        resolved['place'] = self.last_entities['place']
```

**Conversation History Format**:
```json
{
  "timestamp": "2025-11-03T14:30:00",
  "user_input": "What's the weather in Frankfurt?",
  "intent": "weather_query",
  "entities": {"place": "Frankfurt"},
  "response": "The weather in Frankfurt..."
}
```

---

### 5. NLG Module (`modules/nlg.py`)
**Technology**: Template-based generation

**Response Generation Strategy**:
1. Select template based on intent and data availability
2. Fill in entity values
3. Format dates/times for natural output
4. Handle error cases gracefully

**Example Templates**:
```python
# Weather response
"The weather in {place} on {day} will be {condition},
with temperatures between {min} and {max} degrees Celsius."

# Appointment creation confirmation
"I've successfully created the appointment '{title}'."
```

**Date/Time Formatting**:
- Input: "2025-11-03T09:00"
- Output: "Monday, November 03 at 09:00 AM"

---

### 6. Weather API Client (`modules/weather_api.py`)
**Endpoint**: `https://api.responsible-nlp.net/weather.php`

**Methods**:
- `get_weather(place)`: Get 7-day forecast
- `get_weather_for_day(place, day)`: Get specific day forecast
- `check_weather_condition(place, day, condition)`: Check for condition

**Response Format**:
```json
{
  "place": "Marburg",
  "forecast": [
    {
      "day": "thursday",
      "temperature": {"min": 7, "max": 15},
      "weather": "few clouds"
    }
  ]
}
```

**Supported Weather Conditions**:
- clear sky, few clouds, scattered clouds, broken clouds
- shower rain, rain, thunderstorm
- snow, mist

---

### 7. Calendar API Client (`modules/calendar_api.py`)
**Endpoint**: `https://api.responsible-nlp.net/calendar.php`

**CRUD Operations**:

**CREATE**:
```python
create_appointment(title, start_time, end_time, description=None, location=None)
```

**READ**:
```python
get_all_appointments()  # GET /calendar.php
get_appointment(id)      # GET /calendar.php?id=X
```

**UPDATE**:
```python
update_appointment(id, **kwargs)  # PUT /calendar.php?id=X
```

**DELETE**:
```python
delete_appointment(id)  # DELETE /calendar.php?id=X
```

**Calendar ID Parameter**:
All requests include `calenderid` parameter to avoid team data conflicts:
```
https://api.responsible-nlp.net/calendar.php?calenderid=team_001
```

**Helper Methods**:
- `get_next_appointment()`: Returns next upcoming appointment
- `get_appointments_by_date(date)`: Returns appointments for specific date

---

## Main Orchestrator (`main.py`)

### VoiceAssistant Class
Coordinates all modules to provide end-to-end functionality.

**Initialization**:
1. Load ASR model (if voice mode)
2. Initialize TTS engine
3. Load NLU patterns
4. Initialize dialogue manager
5. Create API clients

**Main Loop**:
```
while True:
    user_input = listen()           # ASR or text input
    nlu_result = nlu.understand()   # Intent + entities
    resolved = dialogue.resolve()   # Context resolution
    data = execute_intent()         # API calls
    response = nlg.generate()       # Response generation
    speak(response)                 # TTS or text output
    dialogue.add_turn()             # Update history
```

**Intent Execution Flow**:

**Weather Query**:
1. Extract place and day from entities
2. Call Weather API
3. Store result in dialogue context
4. Return weather data for NLG

**Create Appointment**:
1. Extract title, date, time, location
2. Ask user for missing required fields
3. Format datetime to ISO format
4. Call Calendar API POST
5. Store appointment ID in context
6. Return success/failure

**Update Appointment**:
1. Resolve which appointment (from context or day)
2. Get appointment ID
3. Extract fields to update
4. Call Calendar API PUT
5. Return success/failure

**Delete Appointment**:
1. Resolve which appointment (usually from context)
2. Get appointment ID
3. Call Calendar API DELETE
4. Return success/failure

---

## Design Decisions

### Why Rule-based NLU?
**Pros**:
- Fast development
- No training data required
- Transparent and debuggable
- Sufficient for limited domain

**Cons**:
- Limited robustness
- Doesn't generalize well
- Requires manual pattern maintenance

**Decision**: Rule-based is appropriate for this project's scope and timeline.

### Why pyttsx3 over Coqui TTS?
**Pros**:
- More reliable
- Faster initialization
- Smaller dependencies
- Cross-platform

**Cons**:
- Less natural-sounding
- Fewer voice options

**Decision**: Reliability over quality for demo purposes. Coqui TTS available as option.

### Why Whisper Base Model?
**Pros**:
- Good accuracy/speed tradeoff
- Moderate model size
- Well-tested and maintained

**Cons**:
- Larger than tiny model
- Slower than streaming ASR

**Decision**: Base model provides best balance for project requirements.

---

## Error Handling

### ASR Errors
- Timeout: Return None, prompt user to repeat
- No speech detected: Continue waiting
- Transcription error: Log error, ask user to repeat

### API Errors
- Connection error: Return error message to user
- Timeout: Retry once, then fail gracefully
- Invalid response: Log error, return None

### NLU Errors
- Unknown intent: Provide help message
- Missing entities: Use dialogue to ask for clarification
- Ambiguous input: Request clarification

---

## Testing Strategy

### Unit Tests
Each module has a `__main__` block for standalone testing:
```bash
python modules/asr.py      # Test ASR
python modules/tts.py      # Test TTS
python modules/weather_api.py  # Test Weather API
```

### Integration Tests
`test_commands.py` tests all required commands end-to-end.

### Manual Testing
Use text mode for faster iteration:
```bash
python main.py --text
```

---

## Performance Considerations

### Latency
- ASR: ~1-3 seconds for transcription
- NLU: <10ms (regex matching)
- API calls: ~500ms - 2s depending on network
- NLG: <10ms (template filling)
- TTS: ~500ms - 2s depending on text length

**Total response time**: 2-7 seconds typical

### Memory Usage
- Whisper base model: ~500MB RAM
- Other components: ~100MB RAM
- **Total**: ~600MB RAM typical

### Disk Space
- Whisper model: ~150MB
- Python dependencies: ~500MB
- **Total**: ~650MB

---

## Docker Deployment

### Image Size
- Base image (python:3.10-slim): ~150MB
- Dependencies: ~800MB
- **Total**: ~950MB

### Running Container
```bash
# Text mode (default)
docker run -it voice-assistant

# Voice mode (requires audio device)
docker run -it --device /dev/snd voice-assistant python main.py
```

---

## Known Limitations

1. **Temporal expressions**: Only basic support (today, tomorrow, day names)
2. **Multi-turn clarification**: Limited to single follow-up
3. **Error recovery**: Basic error handling only
4. **Language**: English only
5. **Concurrent appointments**: Difficulty selecting when multiple exist
6. **Recurring events**: Not supported
7. **Natural date parsing**: Limited (e.g., "next Tuesday" not supported)

---

## Future Enhancements

1. **ML-based NLU**: Replace regex with BERT or similar
2. **Advanced temporal parsing**: Support relative dates
3. **Multi-language support**: Add German language support
4. **Streaming ASR**: Replace Whisper with streaming model
5. **Proactive suggestions**: Suggest actions based on context
6. **Calendar conflict detection**: Warn about overlapping appointments
7. **Integration with real calendar services**: Google Calendar, Outlook

---

## Conclusion

This implementation provides a fully functional voice assistant meeting all project requirements. The modular architecture allows easy extension and maintenance. While using simple rule-based approaches, the system demonstrates understanding of core NLS concepts including ASR, NLU, dialogue management, and NLG.
