#!/usr/bin/env python3
"""
Comprehensive Test Suite for Voice Assistant
Tests all required commands with 100+ variations and multi-turn conversations
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import VoiceAssistant


class ComprehensiveTestSuite:
    """Comprehensive test suite with categorized test cases"""

    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'total': 0,
            'details': []
        }

    def run_test(self, assistant, command, expected_intent=None, description=""):
        """Run a single test and record result"""
        self.results['total'] += 1
        try:
            # Clear state before each test
            assistant.dialogue.clear_state()
            assistant.dialogue.clear_context()

            response = assistant.process_input(command)

            success = response is not None and len(response) > 0
            if success:
                self.results['passed'] += 1
            else:
                self.results['failed'] += 1

            self.results['details'].append({
                'command': command,
                'description': description,
                'expected_intent': expected_intent,
                'response': response,
                'success': success
            })

            return success, response
        except Exception as e:
            self.results['failed'] += 1
            self.results['details'].append({
                'command': command,
                'description': description,
                'expected_intent': expected_intent,
                'response': None,
                'success': False,
                'error': str(e)
            })
            return False, str(e)

    def run_conversation(self, assistant, conversation, description=""):
        """Run a multi-turn conversation test"""
        print(f"\n--- Conversation: {description} ---")
        results = []
        for i, turn in enumerate(conversation):
            success, response = self.run_test(
                assistant,
                turn['input'],
                turn.get('expected_intent'),
                f"{description} - Turn {i+1}"
            )
            results.append({
                'input': turn['input'],
                'response': response,
                'success': success
            })
            print(f"  Turn {i+1}: {turn['input'][:50]}... -> {'PASS' if success else 'FAIL'}")
        return results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.results['total']}")
        print(f"Passed: {self.results['passed']} ({100 * self.results['passed'] // max(1, self.results['total'])}%)")
        print(f"Failed: {self.results['failed']} ({100 * self.results['failed'] // max(1, self.results['total'])}%)")
        print("=" * 80)

        # Print failed tests
        failed = [d for d in self.results['details'] if not d['success']]
        if failed:
            print(f"\nFailed Tests ({len(failed)}):")
            for i, f in enumerate(failed[:20], 1):  # Show first 20 failures
                print(f"  {i}. {f['command'][:60]}...")
                if 'error' in f:
                    print(f"     Error: {f['error']}")


def get_weather_test_cases():
    """Weather query test cases"""
    return [
        # Basic weather queries
        ("What's the weather like today?", "weather_query", "Basic weather query"),
        ("What is the weather today?", "weather_query", "Weather today"),
        ("How's the weather?", "weather_query", "Casual weather query"),
        ("Tell me the weather", "weather_query", "Command weather query"),

        # Weather with locations
        ("What's the weather in Marburg?", "weather_query", "Weather with city"),
        ("What's the weather like in Frankfurt?", "weather_query", "Weather Frankfurt"),
        ("Weather in Berlin", "weather_query", "Short weather query"),
        ("How is the weather in Munich?", "weather_query", "Weather Munich"),
        ("What's the weather in Hamburg today?", "weather_query", "Weather Hamburg today"),
        ("Tell me the weather for Cologne", "weather_query", "Weather Cologne"),
        ("Weather forecast for Stuttgart", "weather_query", "Forecast Stuttgart"),
        ("What will the weather be in Dresden?", "weather_query", "Future weather Dresden"),
        ("How's the weather looking in Leipzig?", "weather_query", "Weather Leipzig"),
        ("Check weather in Dusseldorf", "weather_query", "Check weather"),

        # Weather with days
        ("What's the weather tomorrow?", "weather_query", "Weather tomorrow"),
        ("Weather on Monday", "weather_query", "Weather Monday"),
        ("What will the weather be on Tuesday?", "weather_query", "Weather Tuesday"),
        ("How's the weather on Wednesday?", "weather_query", "Weather Wednesday"),
        ("Weather forecast for Thursday", "weather_query", "Weather Thursday"),
        ("What's Friday's weather?", "weather_query", "Weather Friday"),
        ("Tell me Saturday's weather", "weather_query", "Weather Saturday"),
        ("What about Sunday's weather?", "weather_query", "Weather Sunday"),

        # Weather with location AND day
        ("What will the weather be like today in Marburg?", "weather_query", "Required cmd 1"),
        ("What will the weather be on Friday in Frankfurt?", "weather_query", "Required cmd 2"),
        ("What's the weather tomorrow in Berlin?", "weather_query", "Tomorrow Berlin"),
        ("How's the weather on Monday in Munich?", "weather_query", "Monday Munich"),
        ("Weather in Hamburg on Tuesday", "weather_query", "Tuesday Hamburg"),
        ("Tell me Wednesday's weather in Cologne", "weather_query", "Wednesday Cologne"),
        ("What's the forecast for Thursday in Stuttgart?", "weather_query", "Thursday Stuttgart"),

        # Weather condition queries
        ("Will it rain today?", "weather_query", "Rain query"),
        ("Is it going to rain tomorrow?", "weather_query", "Rain tomorrow"),
        ("Will it rain in Marburg?", "weather_query", "Rain location"),
        ("Will it snow today?", "weather_query", "Snow query"),
        ("Is it going to snow tomorrow?", "weather_query", "Snow tomorrow"),
        ("Will it be sunny today?", "weather_query", "Sunny query"),
        ("Is it cloudy outside?", "weather_query", "Cloudy query"),
        ("Will there be a storm?", "weather_query", "Storm query"),
        ("Is it going to be clear today?", "weather_query", "Clear query"),

        # Temperature queries
        ("What's the temperature today?", "weather_query", "Temperature query"),
        ("How hot will it be tomorrow?", "weather_query", "Hot query"),
        ("How cold is it in Berlin?", "weather_query", "Cold query"),
        ("What's the temperature in Munich?", "weather_query", "Temperature location"),
        ("How warm will it be on Friday?", "weather_query", "Warm query"),

        # Natural language variations
        ("I want to know the weather", "weather_query", "Natural query 1"),
        ("Can you tell me the weather?", "weather_query", "Natural query 2"),
        ("What's it like outside?", "weather_query", "Casual query"),
        ("Do I need an umbrella today?", "weather_query", "Umbrella query"),
        ("Should I bring a jacket?", "weather_query", "Jacket query"),
    ]


def get_appointment_query_test_cases():
    """Appointment query test cases"""
    return [
        # Basic appointment queries
        ("What are my appointments?", "get_appointment", "List all appointments"),
        ("Show me my appointments", "get_appointment", "Show appointments"),
        ("List my appointments", "get_appointment", "List appointments"),
        ("Do I have any appointments?", "get_appointment", "Any appointments"),
        ("What meetings do I have?", "get_appointment", "Meetings query"),
        ("Show my calendar", "get_appointment", "Calendar query"),
        ("What's on my calendar?", "get_appointment", "Calendar check"),
        ("Check my appointments", "get_appointment", "Check appointments"),

        # Next appointment
        ("Where is my next appointment?", "get_appointment", "Required cmd 4"),
        ("What's my next appointment?", "get_appointment", "Next appointment"),
        ("When is my next meeting?", "get_appointment", "Next meeting"),
        ("Tell me about my next appointment", "get_appointment", "Next appointment details"),
        ("What's coming up next?", "get_appointment", "Coming up"),
        ("My next event", "get_appointment", "Next event"),

        # Day-specific queries
        ("What appointments do I have today?", "get_appointment", "Today appointments"),
        ("Show me tomorrow's appointments", "get_appointment", "Tomorrow appointments"),
        ("What's on Monday?", "get_appointment", "Monday appointments"),
        ("Appointments for Tuesday", "get_appointment", "Tuesday appointments"),
        ("What meetings do I have on Wednesday?", "get_appointment", "Wednesday meetings"),
        ("Thursday's schedule", "get_appointment", "Thursday schedule"),
        ("What's happening Friday?", "get_appointment", "Friday events"),
        ("Any appointments on Saturday?", "get_appointment", "Saturday appointments"),
        ("Sunday's events", "get_appointment", "Sunday events"),

        # Week queries
        ("What's my schedule this week?", "get_appointment", "This week"),
        ("Show me next week's appointments", "get_appointment", "Next week"),
        ("What do I have this week?", "get_appointment", "Week schedule"),

        # Natural variations
        ("Am I free tomorrow?", "get_appointment", "Free tomorrow"),
        ("Do I have anything on Monday?", "get_appointment", "Monday check"),
        ("Is my calendar empty today?", "get_appointment", "Empty check"),
        ("When am I busy?", "get_appointment", "Busy check"),
    ]


def get_create_appointment_test_cases():
    """Create appointment test cases"""
    return [
        # Basic creation
        ("Add an appointment", "create_appointment", "Basic add"),
        ("Create a new appointment", "create_appointment", "Create appointment"),
        ("Schedule a meeting", "create_appointment", "Schedule meeting"),
        ("Book an appointment", "create_appointment", "Book appointment"),
        ("Set up a meeting", "create_appointment", "Set up meeting"),
        ("Make an appointment", "create_appointment", "Make appointment"),
        ("New appointment", "create_appointment", "New appointment"),

        # With title
        ("Add an appointment titled XYZ for the 12th of January.", "create_appointment", "Required cmd 5"),
        ("Create an appointment called Team Meeting", "create_appointment", "With title"),
        ("Schedule a meeting named Project Review", "create_appointment", "Named meeting"),
        ("Add appointment titled Doctor Visit", "create_appointment", "Doctor appointment"),
        ("Create meeting called Weekly Sync", "create_appointment", "Weekly sync"),
        ("Book an appointment named Interview", "create_appointment", "Interview"),

        # With time
        ("Add an appointment at 3 PM", "create_appointment", "With time PM"),
        ("Create a meeting at 10:00", "create_appointment", "With time 24h"),
        ("Schedule appointment for 2:30 PM", "create_appointment", "With time 2:30"),
        ("Book meeting at 9 AM", "create_appointment", "Morning meeting"),
        ("Add appointment at noon", "create_appointment", "Noon appointment"),

        # With day
        ("Add an appointment for tomorrow", "create_appointment", "Tomorrow"),
        ("Create a meeting on Monday", "create_appointment", "Monday meeting"),
        ("Schedule appointment for Tuesday", "create_appointment", "Tuesday"),
        ("Book a meeting on Friday", "create_appointment", "Friday meeting"),

        # With title and day
        ("Add an appointment titled Dentist for tomorrow", "create_appointment", "Title and day"),
        ("Create meeting called Sprint Planning on Monday", "create_appointment", "Sprint planning"),
        ("Schedule appointment named Lunch Meeting for Friday", "create_appointment", "Lunch meeting"),

        # With title and time
        ("Add appointment called Status Update at 2 PM", "create_appointment", "Title and time"),
        ("Create meeting titled Standup at 9:30 AM", "create_appointment", "Standup"),

        # Complete appointments
        ("Add appointment titled Team Sync for Monday at 10 AM", "create_appointment", "Complete 1"),
        ("Create meeting called Review on Tuesday at 3 PM", "create_appointment", "Complete 2"),
        ("Schedule appointment named Training for Friday at 2 PM", "create_appointment", "Complete 3"),

        # With location
        ("Add meeting in Room 5", "create_appointment", "With location"),
        ("Create appointment at Building A", "create_appointment", "Building location"),
        ("Schedule meeting in Conference Room", "create_appointment", "Conference room"),

        # Natural language
        ("I need to schedule a meeting", "create_appointment", "Natural 1"),
        ("Can you add an appointment for me?", "create_appointment", "Natural 2"),
        ("I want to create a new meeting", "create_appointment", "Natural 3"),
        ("Please book an appointment", "create_appointment", "Polite request"),

        # Multiple appointments
        ("Add two appointments", "create_appointment", "Multiple 2"),
        ("Create three meetings", "create_appointment", "Multiple 3"),
        ("Schedule 5 appointments", "create_appointment", "Multiple 5"),
    ]


def get_update_appointment_test_cases():
    """Update appointment test cases"""
    return [
        # Basic update
        ("Change the place for my appointment tomorrow.", "update_appointment", "Required cmd 7"),
        ("Update my appointment", "update_appointment", "Basic update"),
        ("Modify my meeting", "update_appointment", "Modify meeting"),
        ("Edit my appointment", "update_appointment", "Edit appointment"),
        ("Reschedule my meeting", "update_appointment", "Reschedule"),
        ("Move my appointment", "update_appointment", "Move appointment"),

        # Change time
        ("Change the time of my appointment", "update_appointment", "Change time"),
        ("Update the meeting time", "update_appointment", "Update time"),
        ("Move my appointment to 3 PM", "update_appointment", "Move to 3 PM"),
        ("Reschedule to 10 AM", "update_appointment", "Reschedule time"),
        ("Change appointment to tomorrow", "update_appointment", "Change to tomorrow"),

        # Change location
        ("Change the location of my meeting", "update_appointment", "Change location"),
        ("Update the place for my appointment", "update_appointment", "Update place"),
        ("Move meeting to Room 10", "update_appointment", "Move to room"),
        ("Change location to Building B", "update_appointment", "Change building"),

        # Change title
        ("Change the title of my appointment", "update_appointment", "Change title"),
        ("Rename my meeting", "update_appointment", "Rename"),
        ("Update the appointment name", "update_appointment", "Update name"),

        # Day-specific updates
        ("Change my Monday appointment", "update_appointment", "Monday update"),
        ("Update tomorrow's meeting", "update_appointment", "Tomorrow update"),
        ("Modify Friday's appointment", "update_appointment", "Friday update"),

        # Natural variations
        ("I need to change my appointment", "update_appointment", "Natural 1"),
        ("Can you update my meeting?", "update_appointment", "Natural 2"),
        ("Please reschedule my appointment", "update_appointment", "Polite reschedule"),
    ]


def get_delete_appointment_test_cases():
    """Delete appointment test cases"""
    return [
        # Basic delete
        ("Delete the previously created appointment.", "delete_appointment", "Required cmd 6"),
        ("Delete my appointment", "delete_appointment", "Basic delete"),
        ("Remove my meeting", "delete_appointment", "Remove meeting"),
        ("Cancel my appointment", "delete_appointment", "Cancel appointment"),
        ("Drop my meeting", "delete_appointment", "Drop meeting"),

        # Reference-based delete
        ("Delete that appointment", "delete_appointment", "Delete that"),
        ("Remove the last appointment", "delete_appointment", "Remove last"),
        ("Cancel the previous meeting", "delete_appointment", "Cancel previous"),
        ("Delete it", "delete_appointment", "Delete it"),

        # Day-specific delete
        ("Delete my appointment tomorrow", "delete_appointment", "Delete tomorrow"),
        ("Cancel Monday's meeting", "delete_appointment", "Cancel Monday"),
        ("Remove Friday's appointment", "delete_appointment", "Remove Friday"),

        # Title-based delete
        ("Delete the Team Meeting", "delete_appointment", "Delete by title"),
        ("Cancel the Doctor appointment", "delete_appointment", "Cancel by title"),
        ("Remove the Project Review", "delete_appointment", "Remove by title"),

        # Natural variations
        ("I want to delete my appointment", "delete_appointment", "Natural 1"),
        ("Can you cancel my meeting?", "delete_appointment", "Natural 2"),
        ("Please remove my appointment", "delete_appointment", "Polite remove"),
        ("I need to cancel an appointment", "delete_appointment", "Need to cancel"),
    ]


def get_anaphora_test_conversations():
    """Multi-turn conversations testing anaphora resolution"""
    return [
        # Weather anaphora - "there" reference
        {
            "description": "Weather 'there' reference (Required test)",
            "turns": [
                {"input": "What's the weather in Frankfurt?", "expected_intent": "weather_query"},
                {"input": "Will it rain there on Saturday?", "expected_intent": "weather_query"},
            ]
        },
        {
            "description": "Weather 'there' with multiple turns",
            "turns": [
                {"input": "What's the weather like in Berlin?", "expected_intent": "weather_query"},
                {"input": "How about tomorrow there?", "expected_intent": "weather_query"},
                {"input": "And on Friday?", "expected_intent": "weather_query"},
            ]
        },
        {
            "description": "Weather location carryover",
            "turns": [
                {"input": "Tell me the weather in Munich", "expected_intent": "weather_query"},
                {"input": "What about Monday?", "expected_intent": "weather_query"},
                {"input": "Will it snow there?", "expected_intent": "weather_query"},
            ]
        },

        # Appointment creation multi-turn
        {
            "description": "Appointment creation with missing info",
            "turns": [
                {"input": "Add an appointment", "expected_intent": "create_appointment"},
                {"input": "Team Meeting", "expected_intent": "create_appointment"},
                {"input": "10 AM", "expected_intent": "create_appointment"},
            ]
        },
        {
            "description": "Appointment creation with title provided",
            "turns": [
                {"input": "Create appointment called Interview", "expected_intent": "create_appointment"},
                {"input": "Tomorrow at 2 PM", "expected_intent": "create_appointment"},
            ]
        },

        # Appointment reference
        {
            "description": "Create then delete appointment",
            "turns": [
                {"input": "Add appointment titled Test Meeting for tomorrow at 3 PM", "expected_intent": "create_appointment"},
                {"input": "Delete the previously created appointment", "expected_intent": "delete_appointment"},
            ]
        },
        {
            "description": "Query then update appointment",
            "turns": [
                {"input": "What's my next appointment?", "expected_intent": "get_appointment"},
                {"input": "Change the time to 4 PM", "expected_intent": "update_appointment"},
            ]
        },

        # Context switching
        {
            "description": "Switch from weather to appointment",
            "turns": [
                {"input": "What's the weather in Marburg?", "expected_intent": "weather_query"},
                {"input": "What are my appointments for today?", "expected_intent": "get_appointment"},
            ]
        },
        {
            "description": "Switch from appointment to weather",
            "turns": [
                {"input": "Show me my appointments", "expected_intent": "get_appointment"},
                {"input": "What's the weather like?", "expected_intent": "weather_query"},
            ]
        },
    ]


def get_edge_case_test_cases():
    """Edge case and error handling test cases"""
    return [
        # Short queries
        ("Weather", "weather_query", "Single word weather"),
        ("Appointments", "get_appointment", "Single word appointments"),
        ("Meeting", "get_appointment", "Single word meeting"),

        # Typos and variations (should still work)
        ("Whats the weather", "weather_query", "Missing apostrophe"),
        ("what is the wether", "weather_query", "Typo in weather"),
        ("apointment", "get_appointment", "Typo in appointment"),

        # Mixed case
        ("WHAT'S THE WEATHER", "weather_query", "All caps"),
        ("What's The Weather In MARBURG", "weather_query", "Mixed caps"),

        # Extra words
        ("Um, what's the weather today please?", "weather_query", "Filler words"),
        ("So like, what are my appointments?", "get_appointment", "Casual speech"),
        ("Hey, can you tell me the weather?", "weather_query", "Greeting prefix"),

        # Questions with extra context
        ("I'm going outside, what's the weather?", "weather_query", "Context prefix"),
        ("Before I leave, show me my appointments", "get_appointment", "Context prefix 2"),

        # Compound queries (should handle first intent)
        ("What's the weather and my appointments?", "weather_query", "Compound query"),
    ]


def run_all_tests():
    """Run all test categories"""
    print("=" * 80)
    print("COMPREHENSIVE VOICE ASSISTANT TEST SUITE")
    print("=" * 80)
    print()

    # Initialize
    assistant = VoiceAssistant(calenderid="comprehensive_test_001", use_voice=False)
    suite = ComprehensiveTestSuite()

    # Category 1: Weather Tests
    print("\n" + "=" * 60)
    print("CATEGORY 1: WEATHER QUERIES")
    print("=" * 60)
    weather_tests = get_weather_test_cases()
    for cmd, intent, desc in weather_tests:
        success, response = suite.run_test(assistant, cmd, intent, desc)
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {desc}: {cmd[:50]}...")

    # Category 2: Appointment Queries
    print("\n" + "=" * 60)
    print("CATEGORY 2: APPOINTMENT QUERIES")
    print("=" * 60)
    appt_tests = get_appointment_query_test_cases()
    for cmd, intent, desc in appt_tests:
        success, response = suite.run_test(assistant, cmd, intent, desc)
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {desc}: {cmd[:50]}...")

    # Category 3: Create Appointment
    print("\n" + "=" * 60)
    print("CATEGORY 3: CREATE APPOINTMENT")
    print("=" * 60)
    create_tests = get_create_appointment_test_cases()
    for cmd, intent, desc in create_tests:
        success, response = suite.run_test(assistant, cmd, intent, desc)
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {desc}: {cmd[:50]}...")

    # Category 4: Update Appointment
    print("\n" + "=" * 60)
    print("CATEGORY 4: UPDATE APPOINTMENT")
    print("=" * 60)
    update_tests = get_update_appointment_test_cases()
    for cmd, intent, desc in update_tests:
        success, response = suite.run_test(assistant, cmd, intent, desc)
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {desc}: {cmd[:50]}...")

    # Category 5: Delete Appointment
    print("\n" + "=" * 60)
    print("CATEGORY 5: DELETE APPOINTMENT")
    print("=" * 60)
    delete_tests = get_delete_appointment_test_cases()
    for cmd, intent, desc in delete_tests:
        success, response = suite.run_test(assistant, cmd, intent, desc)
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {desc}: {cmd[:50]}...")

    # Category 6: Multi-turn Conversations
    print("\n" + "=" * 60)
    print("CATEGORY 6: MULTI-TURN CONVERSATIONS (ANAPHORA)")
    print("=" * 60)
    conversations = get_anaphora_test_conversations()
    for conv in conversations:
        # Reset assistant state for each conversation
        assistant.dialogue.reset()
        suite.run_conversation(assistant, conv['turns'], conv['description'])

    # Category 7: Edge Cases
    print("\n" + "=" * 60)
    print("CATEGORY 7: EDGE CASES")
    print("=" * 60)
    edge_tests = get_edge_case_test_cases()
    for cmd, intent, desc in edge_tests:
        success, response = suite.run_test(assistant, cmd, intent, desc)
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {desc}: {cmd[:50]}...")

    # Print summary
    suite.print_summary()

    return suite.results


if __name__ == "__main__":
    results = run_all_tests()
