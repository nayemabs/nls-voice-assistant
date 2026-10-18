"""
Dialogue Management Module
Handles conversation history and context tracking
"""

from datetime import datetime
import json


class DialogueManager:
    """Manages conversation state and context"""

    def __init__(self, max_history=10):
        """
        Initialize dialogue manager

        Args:
            max_history: Maximum number of turns to keep in history
        """
        self.conversation_history = []
        self.context = {}
        self.max_history = max_history
        self.last_intent = None
        self.last_entities = {}
        self.last_api_result = None
        self.current_state = None  # New: For multi-turn states
        self.temp_context = {}  # New: Temporary data for multi-turn (e.g., partial entities)
        self.last_weather_place = None  # Persist last weather location for anaphora

    def add_turn(self, user_input, intent, entities, response):
        """
        Add a conversation turn to history

        Args:
            user_input: User's input text
            intent: Detected intent
            entities: Extracted entities
            response: System response
        """
        turn = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'intent': intent,
            'entities': entities,
            'response': response
        }

        self.conversation_history.append(turn)

        # Keep only last N turns
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)

        # Update context
        self.last_intent = intent
        self.last_entities = entities

        # Persist weather place for anaphora resolution across turns
        if intent == 'weather_query' and entities.get('place'):
            self.last_weather_place = entities['place']

    def get_last_turn(self):
        """
        Get the last conversation turn

        Returns:
            dict: Last turn or None
        """
        if self.conversation_history:
            return self.conversation_history[-1]
        return None

    def get_history(self, n=None):
        """
        Get conversation history

        Args:
            n: Number of recent turns to retrieve (None for all)

        Returns:
            list: Conversation history
        """
        if n is None:
            return self.conversation_history
        return self.conversation_history[-n:]

    def resolve_reference(self, current_entities):
        """
        Resolve anaphoric references using context

        Args:
            current_entities: Entities from current utterance

        Returns:
            dict: Resolved entities with context
        """
        resolved = current_entities.copy()

        # If temporal reference detected and location not specified
        if current_entities.get('temporal_reference'):
            # Use location from last turn if available
            if 'place' not in resolved and 'place' in self.last_entities:
                resolved['place'] = self.last_entities['place']
                resolved['resolved_place'] = True

            # If referring to previous appointment
            if self.last_intent in ['create_appointment', 'get_appointment', 'update_appointment']:
                # Carry over appointment context
                if self.last_api_result:
                    resolved['referenced_appointment'] = self.last_api_result

        # If no place specified but we have a saved weather place (for "there" references)
        # Use the persisted weather place which survives across unrelated turns
        if 'place' not in resolved and self.last_weather_place:
            # Only do this when there's an explicit anaphoric reference (e.g., "there")
            if current_entities.get('temporal_reference'):
                resolved['place'] = self.last_weather_place
                resolved['resolved_place'] = True

        return resolved

    def update_context(self, key, value):
        """
        Update dialogue context

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value

    def get_context(self, key, default=None):
        """
        Get value from dialogue context

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Context value
        """
        return self.context.get(key, default)

    def store_api_result(self, result):
        """
        Store last API result for reference

        Args:
            result: API result (appointment, weather data, etc.)
        """
        self.last_api_result = result

    def get_last_appointment_id(self):
        """
        Get ID of last created/retrieved appointment

        Returns:
            int/str: Appointment ID or None
        """
        if self.last_api_result and isinstance(self.last_api_result, dict):
            return self.last_api_result.get('id')
        return None

    def clear_context(self):
        """Clear dialogue context"""
        self.context = {}
        self.last_intent = None
        self.last_entities = {}
        self.last_api_result = None

    def reset(self):
        """Reset dialogue manager completely"""
        self.conversation_history = []
        self.clear_context()

    def export_history(self, filepath):
        """
        Export conversation history to JSON file

        Args:
            filepath: Path to save file
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.conversation_history, f, indent=2)
            print(f"History exported to {filepath}")
        except Exception as e:
            print(f"Error exporting history: {e}")

    def get_summary(self):
        """
        Get a summary of the conversation

        Returns:
            dict: Conversation summary
        """
        summary = {
            'total_turns': len(self.conversation_history),
            'intent_distribution': {},
            'start_time': None,
            'end_time': None
        }

        if self.conversation_history:
            summary['start_time'] = self.conversation_history[0]['timestamp']
            summary['end_time'] = self.conversation_history[-1]['timestamp']

            # Count intents
            for turn in self.conversation_history:
                intent = turn.get('intent', 'unknown')
                summary['intent_distribution'][intent] = \
                    summary['intent_distribution'].get(intent, 0) + 1

        return summary

    # New methods for state
    def set_state(self, state, context_data=None):
        self.current_state = state
        self.temp_context = context_data or {}

    def get_state(self):
        return self.current_state

    def clear_state(self):
        self.current_state = None
        self.temp_context = {}

    def store_last_appointment_id(self, appt_id):
        self.update_context('last_appointment_id', appt_id)


if __name__ == "__main__":
    # Test Dialogue Manager
    print("Testing Dialogue Manager\n")

    dm = DialogueManager()

    # Simulate conversation
    print("Turn 1:")
    dm.add_turn(
        "What's the weather in Frankfurt?",
        "weather_query",
        {"place": "Frankfurt"},
        "The weather in Frankfurt is sunny."
    )

    print("Turn 2:")
    entities = {"day": "tomorrow", "temporal_reference": True}
    resolved = dm.resolve_reference(entities)
    print(f"Original entities: {entities}")
    print(f"Resolved entities: {resolved}")

    dm.add_turn(
        "Will it rain there tomorrow?",
        "weather_query",
        resolved,
        "No, it will not rain in Frankfurt tomorrow."
    )

    print("\nConversation Summary:")
    print(dm.get_summary())

    print("\nFull History:")
    for i, turn in enumerate(dm.get_history(), 1):
        print(f"{i}. User: {turn['user_input']}")
        print(f"   System: {turn['response']}")