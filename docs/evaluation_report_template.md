# Voice Assistant Evaluation Report

## Team Members
- Name 1 (Matriculation ID: XXXXXXXX)
- Name 2 (Matriculation ID: XXXXXXXX)
- Name 3 (Matriculation ID: XXXXXXXX)
- Name 4 (Matriculation ID: XXXXXXXX)

---

## 1. System Overview

### 1.1 Architecture
The voice assistant consists of the following components:
- **ASR (Automatic Speech Recognition)**: OpenAI Whisper (base model)
- **NLU (Natural Language Understanding)**: Rule-based intent detection with regex patterns
- **Dialogue Management**: Context tracking with conversation history
- **API Integration**: Weather API and Calendar API clients
- **NLG (Natural Language Generation)**: Template-based response generation
- **TTS (Text-to-Speech)**: pyttsx3 for local speech synthesis

### 1.2 Key Features
- Local processing (no cloud dependencies except APIs)
- Conversation history tracking (last 10 turns)
- Context resolution for anaphoric references
- Full CRUD support for calendar management
- Weather forecast retrieval for any location

---

## 2. Evaluation Methodology

### 2.1 Evaluation Criteria
Based on the NLS lecture content, we evaluated the system on:

1. **Intent Recognition Accuracy**: How well the system identifies user intents
2. **Entity Extraction Precision**: Accuracy of extracted entities (location, date, time, etc.)
3. **Dialogue Context Management**: Ability to handle references to previous turns
4. **API Integration Success Rate**: Success rate of API calls
5. **Response Quality**: Naturalness and correctness of generated responses

### 2.2 Test Dataset
We created a test set of 50 utterances covering:
- 15 weather queries (various locations and temporal expressions)
- 10 appointment retrieval queries
- 10 appointment creation commands
- 8 appointment update commands
- 7 appointment deletion commands

### 2.3 Evaluation Metrics
- **Intent Recognition Accuracy**: Correct intent / Total utterances
- **Slot Filling F1-Score**: Precision and recall for entity extraction
- **Task Completion Rate**: Successfully completed tasks / Total tasks
- **Dialogue Success Rate**: Multi-turn dialogues completed successfully

---

## 3. Results

### 3.1 Intent Recognition
| Intent | Test Cases | Correct | Accuracy |
|--------|-----------|---------|----------|
| weather_query | 15 | 14 | 93.3% |
| get_appointment | 10 | 9 | 90.0% |
| create_appointment | 10 | 9 | 90.0% |
| update_appointment | 8 | 7 | 87.5% |
| delete_appointment | 7 | 7 | 100% |
| **Overall** | **50** | **46** | **92.0%** |

### 3.2 Entity Extraction Performance
| Entity Type | Precision | Recall | F1-Score |
|------------|-----------|--------|----------|
| Place | 95% | 90% | 92.4% |
| Day/Date | 88% | 85% | 86.5% |
| Weather Condition | 100% | 80% | 88.9% |
| Appointment Title | 85% | 90% | 87.4% |
| Location | 90% | 85% | 87.4% |

### 3.3 Task Completion Rates
- Weather queries: 93.3% (14/15)
- Appointment retrieval: 90.0% (9/10)
- Appointment creation: 80.0% (8/10)
- Appointment updates: 75.0% (6/8)
- Appointment deletion: 100% (7/7)

**Overall Task Completion Rate**: 88.0%

### 3.4 Context Resolution
Tested with 10 multi-turn dialogues involving anaphoric references:
- "What's the weather in Frankfurt?" → "Will it rain there tomorrow?"
- Successfully resolved: 8/10 (80%)

---

## 4. Error Analysis

### 4.1 Common Errors
1. **Missing entities in appointment creation**: When users don't specify time/date
2. **Ambiguous temporal references**: "next week", "in two days" not handled
3. **Complex appointment titles**: Titles with special characters or long phrases
4. **Multiple appointments on same day**: Difficulty selecting which to update

### 4.2 Limitations
- No support for recurring appointments
- Limited to 7-day weather forecast
- No support for relative temporal expressions beyond basic day names
- No multi-language support (English only)
- No error recovery mechanisms for failed API calls

---

## 5. Comparison with Baselines

### 5.1 ASR Performance
- Word Error Rate (WER): ~15% on clean audio
- Whisper base model chosen for balance of speed and accuracy
- Performance degrades with background noise

### 5.2 Intent Classification
Compared to supervised ML approach (hypothetical):
- Our rule-based system: 92% accuracy
- Expected supervised model: 95-98% accuracy
- Trade-off: No training data required, faster development

---

## 6. Conclusions

### 6.1 Achievements
- Successfully implemented all required functionality
- Met all project requirements
- Achieved >85% task completion rate
- Local processing with no cloud dependencies (except APIs)

### 6.2 Future Improvements
1. Implement machine learning-based NLU for better robustness
2. Add support for more complex temporal expressions
3. Implement error recovery and clarification dialogues
4. Add support for recurring calendar events
5. Improve context tracking for longer conversations

### 6.3 Lessons Learned
- Rule-based systems work well for limited domains
- Context management is crucial for natural interactions
- User testing reveals edge cases not considered in development
- Trade-offs between system complexity and reliability

---

## 7. References
- OpenAI Whisper: https://github.com/openai/whisper
- Coqui TTS: https://github.com/coqui-ai/TTS
- Natural Language Systems course materials (WS 2025)

---

**Note**: Replace the example metrics and results above with your actual evaluation results. Conduct thorough testing using the test_commands.py script and additional test cases. Document all findings and provide evidence for your claims.
