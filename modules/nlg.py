"""
Natural Language Generation (NLG) Module
Generates natural language responses from structured data
"""

import random
from datetime import datetime
from dateutil import parser as date_parser


class NLGModule:
    """Generates natural language responses"""

    def __init__(self):
        """Initialize NLG module"""
        # Conversational fillers for more natural speech
        # Keep them short - TTS doesn't pause well on ellipses
        self.thinking_fillers = [
            "Okay, ",
            "Alright, ",
            "So, ",
        ]
        self.confirmation_fillers = [
            "Done. ",
            "Alright, ",
            "Okay, ",
            "Great, ",
        ]
        self.understanding_fillers = [
            "I see. ",
            "Okay, ",
        ]
        self.negative_fillers = [
            "Hmm, ",
            "Oh, ",
            "Well, ",
        ]

    def _get_filler(self, filler_type='thinking', probability=0.4):
        """
        Get a random conversational filler

        Args:
            filler_type: Type of filler ('thinking', 'confirmation', 'understanding', 'negative')
            probability: Probability of including a filler (0.0 to 1.0)

        Returns:
            str: A filler phrase or empty string
        """
        if random.random() > probability:
            return ""

        fillers = {
            'thinking': self.thinking_fillers,
            'confirmation': self.confirmation_fillers,
            'understanding': self.understanding_fillers,
            'negative': self.negative_fillers,
        }

        filler_list = fillers.get(filler_type, self.thinking_fillers)
        return random.choice(filler_list)

    def generate_response(self, intent, data, entities=None):
        """
        Generate natural language response

        Args:
            intent: The intent to respond to
            data: Data to include in response (API results, etc.)
            entities: Original entities from user input

        Returns:
            str: Generated response text
        """
        # Handle prompt/error responses from multi-turn dialogue (state machine)
        if isinstance(data, dict):
            if 'prompt' in data:
                # Add natural filler to prompts
                filler = self._get_filler('thinking', 0.5)
                return f"{filler}{data['prompt']}"
            if 'error' in data:
                # Add natural filler to error messages
                filler = self._get_filler('negative', 0.6)
                return f"{filler}{data['error']}"

        if intent == 'weather_query':
            return self._generate_weather_response(data, entities)
        elif intent == 'get_appointment':
            return self._generate_get_appointment_response(data)
        elif intent == 'create_appointment':
            return self._generate_create_appointment_response(data)
        elif intent == 'update_appointment':
            return self._generate_update_appointment_response(data)
        elif intent == 'delete_appointment':
            return self._generate_delete_appointment_response(data)
        # Conversational/Social intents
        elif intent == 'greeting':
            return self._generate_greeting_response()
        elif intent == 'thanks':
            return self._generate_thanks_response()
        elif intent == 'acknowledgment':
            return self._generate_acknowledgment_response()
        elif intent == 'goodbye':
            return self._generate_goodbye_response()
        elif intent == 'help':
            return self._generate_help_response()
        elif intent == 'unknown':
            filler = self._get_filler('negative', 0.7)
            return f"{filler}I didn't quite catch that. Try saying something like: 'What's the weather in Marburg?' or 'Create an appointment for tomorrow' or 'Do I have any meetings today?'"
        else:
            filler = self._get_filler('negative', 0.6)
            return f"{filler}I'm not sure how to help with that. I can assist with weather queries and calendar management."

    def _generate_weather_response(self, weather_data, entities):
        """Generate response for weather queries"""
        if not weather_data:
            place = entities.get('place', 'that location') if entities else 'that location'
            filler = self._get_filler('negative', 0.7)
            return f"{filler}I'm sorry, I couldn't retrieve weather information for {place}."

        place = weather_data.get('place', 'Unknown')
        filler = self._get_filler('thinking', 0.5)

        # Check if asking about specific condition
        if entities and entities.get('condition'):
            condition = entities.get('condition')
            day = entities.get('day', 'today')

            # Find the forecast for the day
            forecast = self._find_forecast_by_day(weather_data.get('forecast', []), day)

            if not forecast:
                return f"I couldn't find weather information for {day} in {place}."

            weather = forecast.get('weather', '').lower()

            # Check if condition matches
            day_phrase = self._format_day_phrase(day)
            condition_lower = condition.lower()

            # Skip invalid conditions that slipped through (defensive check)
            invalid_conditions = {'weather', 'forecast', 'temperature', 'outside', 'like'}
            if condition_lower in invalid_conditions:
                # Fall through to general weather response
                pass
            else:
                # Determine if condition is a verb (rain, snow) or adjective (sunny, cloudy)
                verb_conditions = {'rain', 'snow', 'storm', 'shower', 'thunder', 'hail', 'drizzle'}
                if condition_lower in verb_conditions:
                    # Verb form: "it will rain"
                    if condition_lower in weather:
                        return f"{filler}Yes, it looks like it will {condition} in {place} {day_phrase}. The weather will be {weather}."
                    else:
                        return f"{filler}No, it doesn't look like it will {condition} in {place} {day_phrase}. The weather will be {weather}."
                else:
                    # Adjective form: "it will be sunny"
                    if condition_lower in weather:
                        return f"{filler}Yes, it looks like it will be {condition} in {place} {day_phrase}. The weather will be {weather}."
                    else:
                        return f"{filler}No, it doesn't look like it will be {condition} in {place} {day_phrase}. The weather will be {weather}."

        # Check if asking about specific day
        if entities and entities.get('day'):
            day = entities.get('day')
            forecast = self._find_forecast_by_day(weather_data.get('forecast', []), day)

            if not forecast:
                return f"I couldn't find weather information for {day} in {place}."

            weather = forecast.get('weather')
            temp = forecast.get('temperature', {})
            min_temp = temp.get('min', 'N/A')
            max_temp = temp.get('max', 'N/A')

            # Format day naturally (avoid "on today")
            day_phrase = self._format_day_phrase(day)
            response = f"{filler}The weather in {place} {day_phrase} will be {weather}, "
            response += f"with temperatures between {min_temp} and {max_temp} degrees Celsius."

            return response

        # General forecast
        forecast = weather_data.get('forecast', [])
        if not forecast:
            return f"No forecast available for {place}."

        # Return today's forecast or first available
        today = forecast[0]
        weather = today.get('weather')
        temp = today.get('temperature', {})
        min_temp = temp.get('min', 'N/A')
        max_temp = temp.get('max', 'N/A')
        day = today.get('day', 'today')

        day_phrase = self._format_day_phrase(day)
        response = f"{filler}The weather in {place} {day_phrase} will be {weather}, "
        response += f"with temperatures between {min_temp} and {max_temp} degrees Celsius."

        return response

    def _find_forecast_by_day(self, forecast, day):
        """Find forecast entry for a specific day"""
        day_lower = day.lower()

        # Handle "today" - return first entry
        if day_lower == 'today':
            return forecast[0] if forecast else None

        # Handle "tomorrow" - return second entry
        if day_lower == 'tomorrow':
            return forecast[1] if len(forecast) > 1 else None

        # Search for matching day
        for entry in forecast:
            if entry.get('day', '').lower() == day_lower:
                return entry

        return None

    def _generate_get_appointment_response(self, appointment_data):
        """Generate response for appointment queries"""
        if not appointment_data:
            filler = self._get_filler('thinking', 0.6)
            return f"{filler}You don't have any appointments scheduled."

        if isinstance(appointment_data, list):
            # Multiple appointments
            if not appointment_data:
                filler = self._get_filler('thinking', 0.6)
                return f"{filler}You don't have any appointments scheduled."

            filler = self._get_filler('thinking', 0.5)
            count = len(appointment_data)
            response = f"{filler}You have {count} appointment"
            response += "s" if count > 1 else ""
            response += ". "

            # List first few
            for i, apt in enumerate(appointment_data[:3], 1):
                title = apt.get('title', 'Untitled')
                location = apt.get('location')
                start_time = self._format_datetime(apt.get('start_time'))

                if location:
                    response += f"{i}. {title} at {location} on {start_time}. "
                else:
                    response += f"{i}. {title} on {start_time}. "

            if count > 3:
                response += f"And {count - 3} more."

            return response
        else:
            # Single appointment
            filler = self._get_filler('understanding', 0.5)
            title = appointment_data.get('title', 'Untitled')
            location = appointment_data.get('location', 'no specified location')
            start_time = self._format_datetime(appointment_data.get('start_time'))
            end_time = self._format_datetime(appointment_data.get('end_time'))

            response = f"{filler}Your appointment '{title}' is at {location}, "
            response += f"from {start_time} to {end_time}."

            return response

    def _generate_create_appointment_response(self, result):
        """Generate response for appointment creation"""
        if not result:
            filler = self._get_filler('negative', 0.7)
            return f"{filler}I'm sorry, I couldn't create the appointment. Please try again."

        # Check for scheduling conflict
        if result.get('conflict'):
            existing = result.get('existing', {})
            existing_title = existing.get('title', 'another appointment')
            filler = self._get_filler('negative', 0.8)
            return f"{filler}Sorry, there's already an appointment '{existing_title}' at that time. Please choose a different time."

        # Check if requested time is in the past
        if result.get('past_time'):
            requested = result.get('requested_time')
            if requested:
                time_str = requested.strftime("%I:%M %p on %A")
                filler = self._get_filler('negative', 0.8)
                return f"{filler}Sorry, I can't create an appointment for {time_str} because that time has already passed. Please choose a future time."
            else:
                filler = self._get_filler('negative', 0.8)
                return f"{filler}Sorry, I can't create appointments in the past. Please choose a future time."

        filler = self._get_filler('confirmation', 0.7)
        title = result.get('title', 'your appointment')
        return f"{filler}I've successfully created the appointment '{title}'."

    def _generate_update_appointment_response(self, result):
        """Generate response for appointment updates"""
        if not result:
            filler = self._get_filler('negative', 0.7)
            return f"{filler}I'm sorry, I couldn't update the appointment."

        filler = self._get_filler('confirmation', 0.7)
        return f"{filler}I've successfully updated the appointment."

    def _generate_delete_appointment_response(self, result):
        """Generate response for appointment deletion"""
        # Handle dict response from handler
        if isinstance(result, dict):
            success = result.get('success', False)
            count = result.get('count')
        else:
            success = result
            count = None

        if success:
            filler = self._get_filler('confirmation', 0.7)
            if count and count > 1:
                return f"{filler}I've successfully deleted {count} appointments."
            return f"{filler}I've successfully deleted the appointment."
        else:
            filler = self._get_filler('negative', 0.7)
            return f"{filler}I'm sorry, I couldn't delete the appointment."

    # ============================================================
    # Conversational/Social Response Methods
    # ============================================================

    def _generate_greeting_response(self):
        """Generate response for greetings"""
        responses = [
            "Hello! How can I help you today?",
            "Hi there! I can help you with weather information or manage your calendar.",
            "Hey! What would you like to know?",
            "Hello! Feel free to ask about the weather or your appointments.",
        ]
        return random.choice(responses)

    def _generate_thanks_response(self):
        """Generate response for thanks"""
        responses = [
            "You're welcome!",
            "Happy to help!",
            "No problem!",
            "Glad I could assist!",
            "Anytime!",
        ]
        return random.choice(responses)

    def _generate_acknowledgment_response(self):
        """Generate response for acknowledgments like 'ok', 'got it'"""
        responses = [
            "Is there anything else I can help you with?",
            "Let me know if you need anything else.",
            "Feel free to ask another question.",
            "Anything else you'd like to know?",
        ]
        return random.choice(responses)

    def _generate_goodbye_response(self):
        """Generate response for goodbyes"""
        responses = [
            "Goodbye! Have a great day!",
            "See you later!",
            "Take care!",
            "Bye! Feel free to come back anytime.",
        ]
        return random.choice(responses)

    def _generate_help_response(self):
        """Generate response for help requests"""
        return ("I can help you with two main things: "
                "First, weather information - just ask 'What's the weather in Berlin?' or 'Will it rain tomorrow?'. "
                "Second, calendar management - you can say 'Add an appointment', 'What are my appointments today?', "
                "or 'Delete my meeting'.")

    def _format_day_phrase(self, day):
        """Format day for natural speech (avoid 'on today')"""
        if not day:
            return ""
        day_lower = day.lower().strip()
        # Handle words that don't need "on" prefix
        if day_lower == 'today':
            return "today"
        elif day_lower == 'tomorrow':
            return "tomorrow"
        elif day_lower == 'day after tomorrow' or 'day after tomorrow' in day_lower:
            return "the day after tomorrow"
        elif day_lower in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            return f"on {day.capitalize()}"
        else:
            # For specific dates, use "on"
            return f"on {day}"

    def _format_datetime(self, dt_string):
        """Format datetime string for natural output"""
        if not dt_string:
            return "an unspecified time"

        try:
            dt = date_parser.parse(dt_string)
            return dt.strftime("%A, %B %d at %I:%M %p")
        except:
            return dt_string

    def generate_error_response(self, error_type):
        """Generate error response"""
        filler = self._get_filler('negative', 0.7)
        error_messages = {
            'no_input': f"{filler}I didn't hear anything. Could you please repeat that?",
            'api_error': f"{filler}I'm having trouble connecting to the service. Please try again later.",
            'missing_info': f"{filler}I need more information to help you with that.",
            'not_found': f"{filler}I couldn't find what you're looking for.",
        }

        return error_messages.get(error_type, f"{filler}I'm sorry, something went wrong.")

    def generate_clarification_request(self, missing_entity):
        """Generate clarification request for missing information"""
        filler = self._get_filler('thinking', 0.6)
        clarifications = {
            'place': f"{filler}Which location would you like to know about?",
            'day': f"{filler}Which day are you asking about?",
            'title': f"{filler}What would you like to title the appointment?",
            'time': f"{filler}What time should the appointment be?",
            'date': f"{filler}What date should the appointment be on?",
        }

        return clarifications.get(
            missing_entity,
            f"{filler}Could you please provide the {missing_entity}?"
        )


if __name__ == "__main__":
    # Test NLG module
    print("Testing NLG Module\n")

    nlg = NLGModule()

    # Test weather response
    print("Test 1: Weather query")
    weather_data = {
        "place": "Marburg",
        "forecast": [
            {
                "day": "thursday",
                "temperature": {"min": 7, "max": 15},
                "weather": "few clouds"
            },
            {
                "day": "friday",
                "temperature": {"min": 6, "max": 14},
                "weather": "rain"
            }
        ]
    }
    response = nlg.generate_response('weather_query', weather_data, {'place': 'Marburg'})
    print(response)
    print()

    # Test appointment response
    print("Test 2: Get appointment")
    appointment = {
        "id": 1,
        "title": "Team Meeting",
        "location": "Room 12",
        "start_time": "2025-11-03T09:00",
        "end_time": "2025-11-03T10:00"
    }
    response = nlg.generate_response('get_appointment', appointment)
    print(response)
    print()

    # Test condition check
    print("Test 3: Condition check")
    response = nlg.generate_response(
        'weather_query',
        weather_data,
        {'place': 'Marburg', 'day': 'friday', 'condition': 'rain'}
    )
    print(response)
