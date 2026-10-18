#!/usr/bin/env python3
"""
Main Voice Assistant Orchestrator
Coordinates all modules to provide a complete voice assistant experience
"""

import sys
import os
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import re  # Moved to top for all regex usage

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Auto-detect and use best available engines
# Priority: faster-whisper > standard whisper, Piper TTS > Coqui > pyttsx3
ASR_ENGINE = "standard"
TTS_ENGINE = "standard"

try:
    from asr_fast import ASRModule
    ASR_ENGINE = "faster-whisper"
except ImportError:
    from asr import ASRModule

try:
    from tts_fast import TTSModule
    TTS_ENGINE = "piper"
except ImportError:
    from tts import TTSModule

# NLU: Try hybrid (GLiNER-based) first, fallback to regex-based
NLU_ENGINE = "regex"
HybridNLUAvailable = False
try:
    from nlu_hybrid import get_nlu_module
    HybridNLUAvailable = True
except ImportError:
    pass

from nlu import NLUModule
from dialogue import DialogueManager
from nlg import NLGModule
from weather_api import WeatherAPIClient
from calendar_api import CalendarAPIClient


class VoiceAssistant:
    """Main Voice Assistant that orchestrates all components"""

    def __init__(self, calenderid="nayem_marburg_2026", use_voice=True, use_hybrid_nlu=False):
        """
        Initialize Voice Assistant

        Args:
            calenderid: Unique calendar ID for the team
            use_voice: If True, use voice I/O; if False, use text I/O (for testing)
            use_hybrid_nlu: If True, use GLiNER-based hybrid NLU (requires gliner package)
        """
        global NLU_ENGINE
        print("Initializing Voice Assistant...")

        self.use_voice = use_voice

        # Initialize modules
        if self.use_voice:
            print(f"Loading ASR module ({ASR_ENGINE})...")
            self.asr = ASRModule(model_size="small")

            print(f"Loading TTS module ({TTS_ENGINE})...")
            self.tts = TTSModule(use_piper=True)  # Will auto-fallback to pyttsx3 if Piper unavailable
        else:
            self.asr = None
            self.tts = None

        # Initialize NLU - try hybrid if requested and available
        if use_hybrid_nlu and HybridNLUAvailable:
            print("Loading NLU module (hybrid/GLiNER)...")
            try:
                self.nlu = get_nlu_module(prefer_hybrid=True)
                NLU_ENGINE = "hybrid/GLiNER"
            except Exception as e:
                print(f"Hybrid NLU failed, falling back to regex: {e}")
                self.nlu = NLUModule()
        else:
            print("Loading NLU module (regex)...")
            self.nlu = NLUModule()

        print("Loading NLG module...")
        self.nlg = NLGModule()

        print("Initializing dialogue manager...")
        self.dialogue = DialogueManager()

        print("Connecting to Weather API...")
        self.weather_client = WeatherAPIClient()

        print("Connecting to Calendar API...")
        self.calendar_client = CalendarAPIClient(calenderid=calenderid)

        print("\nVoice Assistant initialized successfully!\n")

    def run(self):
        """Run the voice assistant main loop"""
        self._speak("Hello! I am your voice assistant. I can help you with weather information and calendar appointments. How can I help you?")

        while True:
            try:
                # Get user input
                user_input = self._listen()

                if not user_input:
                    self._speak("Sorry, I didn't hear you. Please repeat.")  # New: Reprompt for empty
                    continue

                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'goodbye', 'bye']:
                    self._speak("Goodbye! Have a great day!")
                    break

                # Process the input
                response = self.process_input(user_input)

                # Speak the response
                if response:
                    self._speak(response)

            except KeyboardInterrupt:
                print("\nShutting down...")
                self._speak("Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                self._speak("I'm sorry, I encountered an error. Please try again.")
                self.dialogue.clear_state()  # Clear state on error

    def process_input(self, user_input):
        """
        Process user input and generate response

        Args:
            user_input: User's input text

        Returns:
            str: Response text
        """
        print(f"\nUser: {user_input}")

        state = self.dialogue.get_state()

        if state:
            # Continue multi-turn based on state
            response_data, intent, resolved_entities = self._handle_state_continuation(state, user_input)
        else:
            # Normal NLU path
            nlu_result = self.nlu.understand(user_input)
            intent = nlu_result['intent']
            entities = nlu_result['entities']
            print(f"Intent: {intent}")
            print(f"Entities: {entities}")

            resolved_entities = self.dialogue.resolve_reference(entities)

            # Handle corrections or missed intents (e.g., place provided after weather)
            # Only treat as weather follow-up if there's an explicit reference or new place mentioned
            if intent == 'unknown':
                if self.dialogue.last_intent == 'weather_query':
                    # Only follow up if user explicitly references "there" or provides a new place
                    if resolved_entities.get('temporal_reference') or (resolved_entities.get('place') and not resolved_entities.get('resolved_place')):
                        intent = 'weather_query'  # Treat as weather follow-up/correction

            response_data = self._execute_intent(intent, resolved_entities)

        # Generate natural language response
        response = self.nlg.generate_response(intent, response_data, resolved_entities)

        # Add to conversation history
        self.dialogue.add_turn(user_input, intent, resolved_entities, response)

        print(f"Assistant: {response}\n")

        return response

    def _handle_state_continuation(self, state, user_input):
        """Handle continuation of multi-turn interactions"""
        if not user_input.strip():
            # Reprompt if empty in state
            return {'prompt': self.dialogue.temp_context.get('last_prompt', "Please provide more details.")}, state, {}

        nlu_result = self.nlu.understand(user_input)  # Re-parse for new entities
        new_intent = nlu_result['intent']
        new_entities = nlu_result['entities']
        resolved_entities = self.dialogue.resolve_reference(new_entities)

        # Check if user wants to switch to a completely different action
        # Only switch if user explicitly starts with an action verb
        explicit_action_starters = ['create ', 'add ', 'make ', 'schedule ', 'book ',  # create actions
                                    'delete ', 'remove ', 'cancel ',  # delete actions
                                    'update ', 'change ', 'modify ', 'edit ',  # update actions
                                    'what ', 'where ', 'when ', 'do i have ', 'show ']  # query actions

        user_starts_new_action = any(user_input.lower().startswith(w) for w in explicit_action_starters)

        # If user explicitly starts a new action, switch to that intent
        if user_starts_new_action and new_intent != 'unknown':
            self.dialogue.clear_state()
            response_data = self._execute_intent(new_intent, resolved_entities)
            return response_data, new_intent, resolved_entities

        # Map state to intent for NLG (state names differ from intent names)
        state_to_nlg_intent = {
            'awaiting_weather_place': 'weather_query',
            'creating_appointment': 'create_appointment',
            'creating_multiple_appointments': 'create_appointment',
            'selecting_appointment_for_update': 'update_appointment',
            'selecting_appointment_for_delete': 'delete_appointment',
            'awaiting_update_details': 'update_appointment',
        }
        intent = state_to_nlg_intent.get(state, state)

        if state == 'awaiting_weather_place':
            place = resolved_entities.get('place')
            if place:
                weather_data = self.weather_client.get_weather(place)
                self.dialogue.store_api_result(weather_data)
                self.dialogue.clear_state()
                return weather_data, intent, resolved_entities
            else:
                self.dialogue.temp_context['last_prompt'] = "Which location?"
                return {'prompt': 'No place provided. Which location?'}, intent, resolved_entities

        elif state.startswith('creating_appointment'):
            # Smart entity accumulation - don't overwrite existing valid values with garbage
            for key, value in resolved_entities.items():
                if key == 'title':
                    # Only accept new title if:
                    # 1. We don't have a title yet, OR
                    # 2. User explicitly said "title is..." in their input
                    existing_title = self.dialogue.temp_context.get('title')
                    if existing_title:
                        # Check if user explicitly provided a new title
                        title_pattern = r'\b(?:title|call(?:ed)?|name(?:d)?)\s+(?:is|should\s+be|it)\b'
                        if re.search(title_pattern, user_input, re.IGNORECASE):
                            # User explicitly changing the title
                            self.dialogue.temp_context['title'] = value
                        # Otherwise keep existing title, don't overwrite
                    else:
                        # No existing title, accept this one
                        self.dialogue.temp_context['title'] = value
                else:
                    # For other entities (time, day, place), update normally
                    self.dialogue.temp_context[key] = value

            # If we're waiting for a title and no title was extracted, use the input as title
            # This handles cases like "the team meeting regarding natural language processing"
            if not self.dialogue.temp_context.get('title') and not resolved_entities.get('title'):
                # Check if input looks like a potential title (not an action or query)
                action_words = ['create', 'delete', 'remove', 'cancel', 'update', 'change', 'what', 'where', 'do i have', 'weather']
                if not any(user_input.lower().startswith(w) for w in action_words):
                    # Clean the input - strip trailing time/date phrases
                    clean_title = user_input.strip().rstrip('.')
                    # Remove "and time is ...", "and the time is ...", "at 3pm", etc.
                    clean_title = re.sub(r'\s+and\s+(?:the\s+)?(?:time|date)\s+(?:is|would\s+be|will\s+be|should\s+be)\s+.*$', '', clean_title, flags=re.IGNORECASE)
                    clean_title = re.sub(r'\s+at\s+\d{1,2}(?:[:.]\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)?.*$', '', clean_title, flags=re.IGNORECASE)
                    # Remove leading "title is" or "title would be" etc.
                    clean_title = re.sub(r'^(?:the\s+)?title\s+(?:is|should\s+be|would\s+be|will\s+be)\s+', '', clean_title, flags=re.IGNORECASE)
                    clean_title = clean_title.strip()
                    if clean_title and len(clean_title) > 1:
                        self.dialogue.temp_context['title'] = clean_title

            if state == 'creating_multiple_appointments':
                remaining = self.dialogue.temp_context.get('remaining', 0)
                original_count = self.dialogue.temp_context.get('original_count', 0)
                if remaining > 0:
                    result = self._create_single_appointment(self.dialogue.temp_context)
                    if result:
                        remaining -= 1
                        if remaining > 0:
                            # Reset context but keep remaining count and original count
                            self.dialogue.temp_context = {
                                'remaining': remaining,
                                'original_count': original_count,
                                'last_prompt': f"Details for next appointment ({remaining} left)?"
                            }
                            return {'prompt': self.dialogue.temp_context['last_prompt']}, intent, resolved_entities
                        else:
                            self.dialogue.clear_state()
                            return {'count': original_count}, intent, resolved_entities
                self.dialogue.clear_state()
                return {'error': 'Creation failed'}, intent, resolved_entities

            else:  # Single creation
                missing = self._get_missing_appointment_fields(self.dialogue.temp_context)
                if missing:
                    prompt = f"What's the {' and '.join(missing)}?"
                    self.dialogue.temp_context['last_prompt'] = prompt
                    return {'prompt': prompt}, intent, resolved_entities
                result = self._create_single_appointment(self.dialogue.temp_context)

                # Handle past time - prompt for new time instead of failing
                if result and result.get('past_time'):
                    # Clear the invalid time and prompt for a new one
                    self.dialogue.temp_context.pop('time', None)
                    prompt = "That time has already passed. Please provide a future time."
                    self.dialogue.temp_context['last_prompt'] = prompt
                    return {'prompt': prompt}, intent, resolved_entities

                # Handle conflict - prompt for new time
                if result and result.get('conflict'):
                    self.dialogue.temp_context.pop('time', None)
                    existing = result.get('existing', {})
                    existing_title = existing.get('title', 'another appointment')
                    prompt = f"There's already '{existing_title}' at that time. Please choose a different time."
                    self.dialogue.temp_context['last_prompt'] = prompt
                    return {'prompt': prompt}, intent, resolved_entities

                self.dialogue.clear_state()
                self.dialogue.store_api_result(result)
                return result, intent, resolved_entities

        elif state in ['selecting_appointment_for_update', 'selecting_appointment_for_delete']:
            is_delete = state.endswith('_for_delete')
            appointments = self.dialogue.temp_context.get('appointments', [])
            appointment_id = self._select_appointment_from_input(user_input, appointments, allow_batch=is_delete)
            if not appointment_id:
                prompt = "Couldn't identify appointment. Please say the number or title."
                self.dialogue.temp_context['last_prompt'] = prompt
                return {'error': prompt}, intent, resolved_entities

            if is_delete:
                # Handle batch delete (list of IDs) or single delete
                if isinstance(appointment_id, list):
                    count = 0
                    for aid in appointment_id:
                        if self.calendar_client.delete_appointment(aid):
                            count += 1
                    self.dialogue.clear_state()
                    return {'success': True, 'count': count}, intent, resolved_entities
                else:
                    success = self.calendar_client.delete_appointment(appointment_id)
                    self.dialogue.clear_state()
                    return {'success': success}, intent, resolved_entities
            else:
                # Try to apply pending entities from the original request (e.g., user said "change time of 2nd to 8pm")
                pending_entities = self.dialogue.temp_context.get('pending_entities', {})
                self.dialogue.set_state('awaiting_update_details', {'appointment_id': appointment_id})
                if pending_entities:
                    updates = self._parse_update_from_input('', pending_entities)
                    if updates:
                        result = self.calendar_client.update_appointment(appointment_id, **updates)
                        self.dialogue.clear_state()
                        self.dialogue.store_api_result(result)
                        return result, intent, resolved_entities
                return {'prompt': "What would you like to change? (e.g., time, title, location)"}, intent, resolved_entities

        elif state == 'awaiting_update_details':
            # Check if user is specifying which field to change (e.g., just "time", "title", "location")
            field_keywords = {'time': 'time', 'date': 'date', 'location': 'location',
                              'place': 'location', 'title': 'title', 'name': 'title'}
            user_stripped = user_input.strip().lower().rstrip('.')
            if user_stripped in field_keywords:
                field = field_keywords[user_stripped]
                self.dialogue.temp_context['field_to_change'] = field
                self.dialogue.set_state('awaiting_field_value', self.dialogue.temp_context)
                field_prompts = {
                    'time': "What time should it be changed to?",
                    'date': "What date should it be changed to?",
                    'location': "What location should it be changed to?",
                    'title': "What should the new title be?",
                }
                return {'prompt': field_prompts.get(field, "What's the new value?")}, intent, resolved_entities

            updates = self._parse_update_from_input(user_input)
            appointment_id = self.dialogue.temp_context.get('appointment_id')
            if updates and appointment_id:
                result = self.calendar_client.update_appointment(appointment_id, **updates)
                self.dialogue.clear_state()
                self.dialogue.store_api_result(result)
                return result, intent, resolved_entities
            else:
                prompt = "Please specify changes (e.g., 'time to 2 PM' or 'title to Meeting')"
                self.dialogue.temp_context['last_prompt'] = prompt
                return {'prompt': prompt}, intent, resolved_entities

        elif state == 'awaiting_field_value':
            field = self.dialogue.temp_context.get('field_to_change')
            appointment_id = self.dialogue.temp_context.get('appointment_id')
            updates = {}
            if field == 'time':
                nlu_result = self.nlu.understand(user_input)
                if nlu_result['entities'].get('time'):
                    current_apt = self.calendar_client.get_appointment(appointment_id)
                    if current_apt:
                        current_start = date_parser.parse(current_apt['start_time'])
                        updates['start_time'] = f"{current_start.date()}T{nlu_result['entities']['time']}"
                else:
                    # Try parsing the raw input as a time
                    time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', user_input.lower())
                    if time_match:
                        updates['time'] = self._parse_time_input(time_match.group(1))
            elif field == 'title':
                updates['title'] = user_input.strip()
            elif field == 'location':
                updates['location'] = user_input.strip()
            elif field == 'date':
                nlu_result = self.nlu.understand(user_input)
                if nlu_result['entities'].get('date'):
                    updates['date'] = nlu_result['entities']['date']

            if updates and appointment_id:
                result = self.calendar_client.update_appointment(appointment_id, **updates)
                self.dialogue.clear_state()
                self.dialogue.store_api_result(result)
                return result, intent, resolved_entities
            else:
                self.dialogue.clear_state()
                return {'prompt': f"Sorry, I couldn't understand the new {field}. Please try again."}, intent, resolved_entities

        self.dialogue.clear_state()
        return {'error': 'Unknown state'}, intent, resolved_entities

    def _execute_intent(self, intent, entities):
        """
        Execute the detected intent (non-interactive)

        Args:
            intent: Detected intent
            entities: Resolved entities

        Returns:
            dict/str: Response data or prompt dict if multi-turn needed
        """
        if intent == 'weather_query':
            return self._handle_weather_query(entities)

        elif intent == 'get_appointment':
            return self._handle_get_appointment(entities)

        elif intent == 'create_appointment':
            return self._handle_create_appointment(entities)

        elif intent == 'update_appointment':
            return self._handle_update_appointment(entities)

        elif intent == 'delete_appointment':
            return self._handle_delete_appointment(entities)

        return None  # Let NLG handle unknown intent with helpful message

    def _handle_weather_query(self, entities):
        """Handle weather information requests"""
        place = entities.get('place')
        if not place:
            self.dialogue.set_state('awaiting_weather_place')
            self.dialogue.temp_context['last_prompt'] = "Which location would you like to know about?"
            return {'prompt': self.dialogue.temp_context['last_prompt']}

        weather_data = self.weather_client.get_weather(place)
        self.dialogue.store_api_result(weather_data)
        return weather_data

    def _handle_get_appointment(self, entities):
        """Handle appointment retrieval requests"""
        # Handle 'next week' as date range
        if entities.get('next_week'):
            appointments = []
            now = datetime.now()
            current_weekday = now.weekday()
            days_to_next_monday = (7 - current_weekday) % 7 + 1 if current_weekday != 0 else 8  # Start next Monday
            start = now + timedelta(days=days_to_next_monday)
            for i in range(7):
                date = start + timedelta(days=i)
                appointments.extend(self.calendar_client.get_appointments_by_date(date))
            if appointments:
                self.dialogue.store_api_result(appointments)
            return appointments if appointments else None

        # Handle 'next appointment' query
        if entities.get('next'):
            appointment = self.calendar_client.get_next_appointment()
            if appointment:
                self.dialogue.store_api_result(appointment)
                self.dialogue.update_context('last_appointment_id', appointment.get('id'))
            return appointment

        # Handle multiple days (e.g., "today or tomorrow")
        days = entities.get('days')
        if days and len(days) > 1:
            all_appointments = []
            for day in days:
                if not re.match(r'^(am|pm)$', day.lower()):
                    target_date = self._day_to_date(day)
                    day_appointments = self.calendar_client.get_appointments_by_date(target_date)
                    if day_appointments:
                        all_appointments.extend(day_appointments)
            if all_appointments:
                self.dialogue.store_api_result(all_appointments)
            return all_appointments if all_appointments else None

        day = entities.get('day')
        if day and not re.match(r'^(am|pm)$', day.lower()):
            target_date = self._day_to_date(day)
            appointments = self.calendar_client.get_appointments_by_date(target_date)
            if appointments:
                self.dialogue.store_api_result(appointments)
                if len(appointments) == 1:
                    self.dialogue.update_context('last_appointment_id', appointments[0].get('id'))
            return appointments or None

        # Default: all appointments
        appointments = self.calendar_client.get_all_appointments()
        if appointments:
            self.dialogue.store_api_result(appointments)
        return appointments or None

    def _handle_create_appointment(self, entities):
        """Handle appointment creation setup"""
        # Check for multiple - get last user input from dialogue history
        last_turn = self.dialogue.get_last_turn()
        last_input = last_turn.get('user_input', '') if last_turn else ''
        count_match = re.search(r'(\d+)\s*(?:appointments|meetings)', last_input.lower())
        count = int(count_match.group(1)) if count_match else 1
        if not count_match:
            number_words = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
            for word, num in number_words.items():
                if word in last_input.lower() and ('appointment' in last_input.lower() or 'meeting' in last_input.lower()):
                    count = num
                    break

        if count > 1 and count <= 10:
            self.dialogue.set_state('creating_multiple_appointments', {'remaining': count, 'original_count': count})
            return {'prompt': f"Details for first appointment (of {count})? (e.g., date, title, time)"}

        # Single appointment
        missing = self._get_missing_appointment_fields(entities)
        if missing:
            self.dialogue.set_state('creating_appointment', entities)
            return {'prompt': f"What's the {' and '.join(missing)} for the appointment?"}
        result = self._create_single_appointment(entities)
        self.dialogue.store_api_result(result)
        self.dialogue.update_context('last_appointment_id', result.get('id') if result else None)
        return result

    def _create_single_appointment(self, entities):
        """Core creation logic (no prompts)"""
        title = entities.get('title')
        location = entities.get('location')
        day = entities.get('day')
        time_info = entities.get('time') or self._parse_time_input(entities.get('user_input', '')) or "09:00"  # Fallback parse

        # Normalize time to 24-hour format
        time_info = self._normalize_time(time_info)

        # Clean and format the title
        title = self._clean_title(title)

        if not title:
            return None

        if day and not re.match(r'^(am|pm)$', day.lower()):
            target_date = self._day_to_date(day)
        else:
            target_date = datetime.now() + timedelta(days=1)  # Default tomorrow

        date_info = target_date.strftime("%Y-%m-%d")
        start_time = f"{date_info}T{time_info}"
        try:
            start_datetime = date_parser.parse(start_time)
            end_datetime = start_datetime + timedelta(hours=1)
            end_time = end_datetime.strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            return None

        # Check if appointment is in the past
        now = datetime.now()
        if start_datetime < now:
            return {'past_time': True, 'requested_time': start_datetime}

        # Check for conflicts - no double booking at same time
        existing_appointments = self.calendar_client.get_appointments_by_date(target_date)
        for appt in existing_appointments:
            appt_start = appt.get('start_time', '')
            if 'T' in appt_start:
                try:
                    existing_start = date_parser.parse(appt_start)
                    existing_end = date_parser.parse(appt.get('end_time', appt_start))
                    # Check for overlap
                    if (start_datetime < existing_end and end_datetime > existing_start):
                        return {'conflict': True, 'existing': appt}
                except ValueError:
                    pass

        result = self.calendar_client.create_appointment(
            title=title,
            start_time=start_time,
            end_time=end_time,
            location=location
        )
        return result

    def _handle_update_appointment(self, entities):
        """Handle appointment update setup"""
        appointment_id = self._resolve_appointment_id(entities)
        if appointment_id:
            # Set temp_context first so _parse_update_from_input can access appointment_id
            self.dialogue.set_state('awaiting_update_details', {'appointment_id': appointment_id})
            updates = self._parse_update_from_input('', entities)  # Use entities if provided
            if updates:
                result = self.calendar_client.update_appointment(appointment_id, **updates)
                self.dialogue.clear_state()
                self.dialogue.store_api_result(result)
                return result
            else:
                return {'prompt': "What would you like to change? (e.g., time, title, location)"}

        # Need selection - get all appointments (ignore bad day values like "meeting 2")
        appointments = self._get_relevant_appointments(entities)
        if not appointments:
            # Fallback: try getting all appointments if day-based filter returned nothing
            appointments = self.calendar_client.get_all_appointments()
        if not appointments:
            return {'error': 'No appointments found'}

        # Check if user specified an ordinal (1st, 2nd, 3rd, etc.) to auto-select
        ordinal_index = self._extract_ordinal_index(entities)
        if ordinal_index is not None and 0 <= ordinal_index < len(appointments):
            appointment_id = appointments[ordinal_index].get('id')
            self.dialogue.set_state('awaiting_update_details', {'appointment_id': appointment_id})
            updates = self._parse_update_from_input('', entities)
            if updates:
                result = self.calendar_client.update_appointment(appointment_id, **updates)
                self.dialogue.clear_state()
                self.dialogue.store_api_result(result)
                return result
            return {'prompt': "What would you like to change for this appointment?"}

        if len(appointments) == 1:
            appointment_id = appointments[0].get('id')
            # Try to apply entities directly if user already specified what to change
            self.dialogue.set_state('awaiting_update_details', {'appointment_id': appointment_id})
            updates = self._parse_update_from_input('', entities)
            if updates:
                result = self.calendar_client.update_appointment(appointment_id, **updates)
                self.dialogue.clear_state()
                self.dialogue.store_api_result(result)
                return result
            return {'prompt': "What would you like to change for this appointment?"}
        else:
            self.dialogue.set_state('selecting_appointment_for_update', {'appointments': appointments, 'pending_entities': entities})
            return {'prompt': self._generate_appointment_list_prompt(appointments)}

    def _handle_delete_appointment(self, entities):
        """Handle appointment deletion setup"""
        appointment_id = self._resolve_appointment_id(entities)
        if appointment_id:
            success = self.calendar_client.delete_appointment(appointment_id)
            return {'success': success}

        appointments = self._get_relevant_appointments(entities)
        if not appointments:
            return {'error': 'No appointments found'}
        if len(appointments) == 1:
            appointment_id = appointments[0].get('id')
            success = self.calendar_client.delete_appointment(appointment_id)
            return {'success': success}
        else:
            self.dialogue.set_state('selecting_appointment_for_delete', {'appointments': appointments})
            return {'prompt': self._generate_appointment_list_prompt(appointments, for_delete=True)}

    # Helper methods
    def _get_missing_appointment_fields(self, entities):
        missing = []
        if not entities.get('title'):
            missing.append('title')
        if not entities.get('time'):
            missing.append('time')
        return missing

    def _resolve_appointment_id(self, entities):
        if entities.get('temporal_reference') or entities.get('referenced_appointment'):
            return self.dialogue.get_context('last_appointment_id')
        return None

    def _extract_ordinal_index(self, entities):
        """Extract ordinal number (1st, 2nd, 3rd, etc.) from entities to use as appointment index.
        Returns 0-based index or None."""
        # Check if the day entity contains an ordinal (e.g., "meeting 2" from "2nd meeting")
        day = entities.get('day', '')
        if day:
            # Match ordinals like "1st", "2nd", "3rd", "4th", or plain numbers in the day value
            ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)?', str(day))
            if ordinal_match:
                num = int(ordinal_match.group(1))
                if 1 <= num <= 20:  # Reasonable range for appointment indices
                    return num - 1  # Convert to 0-based index
        return None

    def _get_relevant_appointments(self, entities):
        day = entities.get('day')
        if day and not re.match(r'^(am|pm)$', day.lower()):
            target_date = self._day_to_date(day)
            return self.calendar_client.get_appointments_by_date(target_date)
        return self.calendar_client.get_all_appointments()

    def _select_appointment_from_input(self, user_input, appointments, allow_batch=False):
        user_lower = user_input.lower()

        # Handle batch selection for delete operations
        if allow_batch:
            if 'all' in user_lower or 'both' in user_lower or 'every' in user_lower:
                # Return list of all appointment IDs
                return [appt.get('id') for appt in appointments]

            # Handle "one and two" or "1 and 2" format
            numbers = re.findall(r'\b(\d+|one|two|three|four|five)\b', user_lower)
            if len(numbers) >= 2:
                word_to_num = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
                indices = []
                for n in numbers:
                    num = word_to_num.get(n, int(n) if n.isdigit() else None)
                    if num and 1 <= num <= len(appointments):
                        indices.append(num - 1)
                if indices:
                    return [appointments[i].get('id') for i in set(indices)]

        # Single selection by number
        number_match = re.search(r'\b(\d+|one|two|three|four|five)\b', user_lower)
        if number_match:
            num_str = number_match.group(1)
            word_to_num = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}
            choice = word_to_num.get(num_str, int(num_str) if num_str.isdigit() else None)
            if choice and 0 < choice <= len(appointments):
                return appointments[choice - 1].get('id')

        # Match by title
        for appt in appointments:
            if appt.get('title', '').lower() in user_lower or user_lower in appt.get('title', '').lower():
                return appt.get('id')
        return None

    def _parse_update_from_input(self, user_input, entities=None):
        updates = {}
        if entities is None:
            entities = {}

        # Valid fields for appointment updates
        valid_update_fields = {'title', 'location', 'start_time', 'end_time', 'description'}

        # Use entities
        if entities.get('title'):
            updates['title'] = entities['title']
        if entities.get('location'):
            updates['location'] = entities['location']
        if entities.get('time'):
            # Normalize time to 24h format before building start_time
            normalized_time = self._normalize_time(entities['time'])
            current_apt = self.calendar_client.get_appointment(self.dialogue.temp_context.get('appointment_id'))
            if current_apt:
                current_start = date_parser.parse(current_apt['start_time'])
                updates['start_time'] = f"{current_start.date()}T{normalized_time}"

        # Parse user_input
        if user_input:
            nlu_result = self.nlu.understand(user_input)
            # Only merge valid update fields from NLU result, not all entities
            nlu_entities = nlu_result['entities']
            if nlu_entities.get('title'):
                updates.setdefault('title', nlu_entities['title'])
            if nlu_entities.get('location'):
                updates.setdefault('location', nlu_entities['location'])
            if nlu_entities.get('time') and 'start_time' not in updates:
                normalized_time = self._normalize_time(nlu_entities['time'])
                current_apt = self.calendar_client.get_appointment(self.dialogue.temp_context.get('appointment_id'))
                if current_apt:
                    current_start = date_parser.parse(current_apt['start_time'])
                    updates['start_time'] = f"{current_start.date()}T{normalized_time}"

            # Fallback regex
            time_match = re.search(r'time\s*(?:to|at)?\s*(\d{1,2}(?::\d{2})?\s*(am|pm)?)', user_input.lower())
            if time_match and 'start_time' not in updates:
                normalized_time = self._parse_time_input(time_match.group(1))
                if normalized_time:
                    current_apt = self.calendar_client.get_appointment(self.dialogue.temp_context.get('appointment_id'))
                    if current_apt:
                        current_start = date_parser.parse(current_apt['start_time'])
                        updates['start_time'] = f"{current_start.date()}T{normalized_time}"

            title_match = re.search(r'title\s*(?:to)?\s*(.+)', user_input.lower())
            if title_match:
                updates['title'] = title_match.group(1).strip()

            location_match = re.search(r'location\s*(?:to|in)?\s*(.+)', user_input.lower())
            if location_match:
                updates['location'] = location_match.group(1).strip()

        # Filter out any non-update fields that might have leaked in
        return {k: v for k, v in updates.items() if k in valid_update_fields}

    def _generate_appointment_list_prompt(self, appointments, for_delete=False):
        prompt = f"You have {len(appointments)} appointments. Which one{' to delete' if for_delete else ''}?\n"
        for i, appt in enumerate(appointments, 1):
            title = appt.get('title', 'No title')
            start = appt.get('start_time', '')
            formatted_time = self._format_time(start)
            prompt += f"{i}. {title} at {formatted_time}\n"
        prompt += "Say the number or title."
        return prompt

    def _format_time(self, start_time):
        if 'T' in start_time:
            time_part = start_time.split('T')[1]
            # Handle both "16:00" and "4:00 p.m." formats
            if 'p' in time_part.lower() or 'a' in time_part.lower():
                # Already has AM/PM indicator - parse and normalize
                match = re.match(r'(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)?', time_part, re.IGNORECASE)
                if match:
                    hour = int(match.group(1))
                    minute = match.group(2)
                    period_str = match.group(3) or ''
                    if 'p' in period_str.lower() and hour != 12:
                        hour += 12
                    elif 'a' in period_str.lower() and hour == 12:
                        hour = 0
                    period = 'AM' if hour < 12 else 'PM'
                    hour = hour % 12 or 12
                    return f"{hour}:{minute} {period}"
            else:
                # 24-hour format
                time_part = time_part[:5]
                hour = int(time_part.split(':')[0])
                minute = time_part.split(':')[1]
                period = 'AM' if hour < 12 else 'PM'
                hour = hour % 12 or 12
                return f"{hour}:{minute} {period}"
        return start_time

    def _parse_time_input(self, text):
        """Parse time from user input"""
        text = text.lower().strip()
        try:
            parsed = date_parser.parse(text, fuzzy=True)
            return parsed.strftime("%H:%M")
        except ValueError:
            pass

        match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', text)
        if match:
            hour = int(match.group(1))
            minute = match.group(2) or '00'
            period = match.group(3)
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute}"
        return None

    def _normalize_time(self, time_str):
        """Convert time string to 24-hour format (HH:MM)"""
        if not time_str:
            return "09:00"

        time_str = time_str.lower().strip()

        # Already in 24-hour format (HH:MM)
        if re.match(r'^\d{2}:\d{2}$', time_str):
            return time_str

        # Handle "4:00 pm", "4:00 p.m.", "4 pm", "4pm" formats
        match = re.match(r'^(\d{1,2}):?(\d{2})?\s*(a\.?m\.?|p\.?m\.?)?$', time_str)
        if match:
            hour = int(match.group(1))
            minute = match.group(2) or '00'
            period = match.group(3)

            if period and 'p' in period and hour != 12:
                hour += 12
            elif period and 'a' in period and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute}"

        # Fallback - return as is or default
        return time_str if ':' in time_str else "09:00"

    def _clean_title(self, title):
        """
        Clean and format a messy title into smart title case

        Args:
            title: Raw title string from user input

        Returns:
            str: Cleaned, properly formatted title
        """
        if not title:
            return title

        # Strip whitespace and punctuation at ends
        title = title.strip().rstrip('.,!?')

        # Remove common filler phrases at the start
        # Also handle ASR mis-transcriptions like "time," for "title is"
        filler_starts = [
            r'^(?:the\s+)?(?:title\s+(?:is|should\s+be)\s+)',
            r'^(?:the\s+)?(?:time\s*,\s*)',  # "the time," is often mis-transcription of "title is"
            r'^(?:time\s+is\s+)',  # "time is" could be mis-transcribed "title is"
            r'^(?:it\'?s?\s+(?:called|named|titled)\s+)',
            r'^(?:call\s+it\s+)',
            r'^(?:name\s+it\s+)',
        ]
        for pattern in filler_starts:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)

        # Remove leading articles if they don't add meaning
        # Keep "The" if it's part of a proper name (e.g., "The Matrix Review")
        if title.lower().startswith('the ') and len(title.split()) > 2:
            # Check if it looks like a proper name (multiple capitals after "The")
            rest = title[4:]
            if not (rest[0].isupper() and any(c.isupper() for c in rest[1:])):
                title = title[4:]

        # Clean multiple spaces
        title = re.sub(r'\s+', ' ', title).strip()

        # Apply smart title case
        # Words that should stay lowercase (unless first word)
        lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor',
                          'on', 'at', 'to', 'by', 'of', 'in', 'with', 'as'}

        words = title.split()
        result = []
        for i, word in enumerate(words):
            # First word or words not in lowercase list get capitalized
            if i == 0 or word.lower() not in lowercase_words:
                # Capitalize first letter, keep rest as-is (for acronyms like "NLP")
                if word.isupper() and len(word) > 1:
                    result.append(word)  # Keep acronyms uppercase
                else:
                    result.append(word.capitalize())
            else:
                result.append(word.lower())

        return ' '.join(result)

    def _day_to_date(self, day):
        """Convert day name/reference to datetime object"""
        day_lower = day.lower()
        now = datetime.now()

        if day_lower == 'today':
            return now
        elif day_lower == 'tomorrow':
            return now + timedelta(days=1)
        elif 'day after tomorrow' in day_lower or 'after tomorrow' in day_lower:
            return now + timedelta(days=2)

        day_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        if day_lower in day_map:
            target_day = day_map[day_lower]
            current_day = now.weekday()
            days_ahead = (target_day - current_day + 7) % 7
            if days_ahead == 0:
                days_ahead = 7  # Next week if today
            return now + timedelta(days=days_ahead)

        try:
            return date_parser.parse(day)
        except ValueError:
            return now + timedelta(days=1)  # Default tomorrow

    def _listen(self):
        """Get user input (voice or text)"""
        if self.use_voice and self.asr:
            return self.asr.listen_from_microphone()
        else:
            try:
                return input("You: ").strip()
            except EOFError:
                return None

    def _speak(self, text):
        """Output response (voice or text)"""
        if self.use_voice and self.tts:
            self.tts.speak(text)
        else:
            print(f"Assistant: {text}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Voice Assistant for Weather and Calendar")
    parser.add_argument('--text', action='store_true', help='Use text I/O instead of voice')
    parser.add_argument('--calendar-id', type=str, default='nayem_marburg_2026',
                        help='Unique calendar ID for your team')
    parser.add_argument('--hybrid-nlu', action='store_true',
                        help='Use hybrid NLU with GLiNER for better entity extraction (requires: pip install gliner)')

    args = parser.parse_args()

    # Create and run assistant
    assistant = VoiceAssistant(
        calenderid=args.calendar_id,
        use_voice=not args.text,
        use_hybrid_nlu=args.hybrid_nlu
    )

    assistant.run()


if __name__ == "__main__":
    main()