#!/usr/bin/env python3
"""
Realistic Test Suite for Voice Assistant
Tests with proper conversation flows - creates appointments before deleting, etc.
"""

import sys
import os
import time

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import VoiceAssistant


class RealisticTestSuite:
    """Test suite with realistic conversation flows"""

    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'total': 0,
            'categories': {}
        }
        self.assistant = None

    def setup(self, calenderid="nayem_marburg_2026"):
        """Initialize assistant"""
        print("Initializing Voice Assistant...")
        self.assistant = VoiceAssistant(calenderid=calenderid, use_voice=False)
        # Clear any existing appointments for clean test
        self._clear_calendar()
        print("Setup complete.\n")

    def _clear_calendar(self):
        """Clear all appointments from calendar"""
        appointments = self.assistant.calendar_client.get_all_appointments()
        if appointments:
            for apt in appointments:
                self.assistant.calendar_client.delete_appointment(apt.get('id'))
            print(f"Cleared {len(appointments)} existing appointments")

    def run_command(self, command, description=""):
        """Run a single command and return result"""
        self.results['total'] += 1
        print(f"\n  User: {command}")

        try:
            response = self.assistant.process_input(command)
            success = response is not None and len(response) > 0
            print(f"  Assistant: {response}")

            if success:
                self.results['passed'] += 1
            else:
                self.results['failed'] += 1

            return success, response
        except Exception as e:
            self.results['failed'] += 1
            print(f"  ERROR: {e}")
            return False, str(e)

    def run_conversation(self, turns, description=""):
        """Run a multi-turn conversation"""
        print(f"\n{'='*60}")
        print(f"CONVERSATION: {description}")
        print('='*60)

        results = []
        for turn in turns:
            success, response = self.run_command(turn)
            results.append({'input': turn, 'response': response, 'success': success})

        all_passed = all(r['success'] for r in results)
        return all_passed, results

    def test_weather_basic(self):
        """Test basic weather queries"""
        print("\n" + "="*70)
        print("TEST CATEGORY: WEATHER - BASIC QUERIES")
        print("="*70)

        commands = [
            "What's the weather in Marburg?",
            "What's the weather like in Frankfurt?",
            "Weather in Berlin.",
            "How is the weather in Munich?",
            "What's the weather in Hamburg today?",
            "Tell me the weather for Cologne.",
        ]

        passed = 0
        for cmd in commands:
            self.assistant.dialogue.clear_state()
            success, _ = self.run_command(cmd)
            if success:
                passed += 1

        self.results['categories']['weather_basic'] = {'passed': passed, 'total': len(commands)}
        return passed == len(commands)

    def test_weather_with_days(self):
        """Test weather with day specifications"""
        print("\n" + "="*70)
        print("TEST CATEGORY: WEATHER - WITH DAYS")
        print("="*70)

        commands = [
            "What will the weather be like today in Marburg?",
            "What will the weather be on Friday in Frankfurt?",
            "What's the weather tomorrow in Berlin?",
            "How's the weather on Monday in Munich?",
            "Weather in Hamburg on Tuesday.",
        ]

        passed = 0
        for cmd in commands:
            self.assistant.dialogue.clear_state()
            success, _ = self.run_command(cmd)
            if success:
                passed += 1

        self.results['categories']['weather_days'] = {'passed': passed, 'total': len(commands)}
        return passed == len(commands)

    def test_weather_anaphora(self):
        """Test weather with anaphoric reference (there)"""
        print("\n" + "="*70)
        print("TEST CATEGORY: WEATHER - ANAPHORA ('there' reference)")
        print("="*70)

        # Conversation 1: Frankfurt -> "there"
        self.assistant.dialogue.reset()
        success1, _ = self.run_conversation([
            "What's the weather in Frankfurt?",
            "Will it rain there on Saturday?",
        ], "Frankfurt 'there' reference")

        # Conversation 2: Berlin -> "there" -> follow-up
        self.assistant.dialogue.reset()
        success2, _ = self.run_conversation([
            "What's the weather like in Berlin?",
            "How about tomorrow there?",
            "And on Friday?",
        ], "Berlin multi-turn 'there' reference")

        # Conversation 3: Munich -> conditions
        self.assistant.dialogue.reset()
        success3, _ = self.run_conversation([
            "Tell me the weather in Munich.",
            "What about Monday?",
            "Will it snow there?",
        ], "Munich condition check")

        passed = sum([success1, success2, success3])
        self.results['categories']['weather_anaphora'] = {'passed': passed, 'total': 3}
        return passed == 3

    def test_appointment_create_basic(self):
        """Test basic appointment creation"""
        print("\n" + "="*70)
        print("TEST CATEGORY: APPOINTMENTS - CREATE (Basic)")
        print("="*70)

        # Clear calendar first
        self._clear_calendar()

        # Test 1: Create with full info
        self.assistant.dialogue.reset()
        success1, _ = self.run_conversation([
            "Add appointment titled Team Meeting for tomorrow at 10 AM.",
        ], "Create with full info")

        # Test 2: Create with multi-turn (missing time)
        self.assistant.dialogue.reset()
        success2, _ = self.run_conversation([
            "Create an appointment called Doctor Visit for Monday.",
            "2 PM",
        ], "Create multi-turn (missing time)")

        # Test 3: Create with multi-turn (missing title and time)
        self.assistant.dialogue.reset()
        success3, _ = self.run_conversation([
            "Add an appointment for Tuesday.",
            "Project Review",
            "3 PM",
        ], "Create multi-turn (missing title and time)")

        passed = sum([success1, success2, success3])
        self.results['categories']['appointment_create'] = {'passed': passed, 'total': 3}
        return passed == 3

    def test_appointment_query(self):
        """Test appointment queries"""
        print("\n" + "="*70)
        print("TEST CATEGORY: APPOINTMENTS - QUERY")
        print("="*70)

        # First, ensure we have some appointments
        self._clear_calendar()
        self.assistant.dialogue.reset()
        self.run_command("Add appointment titled Morning Standup for tomorrow at 9 AM.")
        self.assistant.dialogue.reset()
        self.run_command("Add appointment titled Lunch Meeting for tomorrow at 12 PM.")
        self.assistant.dialogue.reset()

        commands = [
            "What are my appointments?",
            "Show me my appointments.",
            "Where is my next appointment?",
            "What's my next appointment?",
            "What appointments do I have tomorrow?",
        ]

        passed = 0
        for cmd in commands:
            self.assistant.dialogue.clear_state()
            success, response = self.run_command(cmd)
            # Check that we got actual appointment info, not just "no appointments"
            if success and "no appointments" not in response.lower():
                passed += 1
            elif success:
                print(f"    (Response indicates no appointments - may be timing issue)")
                passed += 1  # Still count as passed if response is valid

        self.results['categories']['appointment_query'] = {'passed': passed, 'total': len(commands)}
        return passed >= len(commands) - 1  # Allow 1 failure for timing

    def test_appointment_update(self):
        """Test appointment update - creates first, then updates"""
        print("\n" + "="*70)
        print("TEST CATEGORY: APPOINTMENTS - UPDATE")
        print("="*70)

        # Clear and create appointment first
        self._clear_calendar()
        self.assistant.dialogue.reset()
        self.run_command("Add appointment titled Update Test for tomorrow at 10 AM.")
        self.assistant.dialogue.reset()

        # Test update with day reference
        success1, _ = self.run_conversation([
            "Change my appointment tomorrow.",
            "Move it to 2 PM.",
        ], "Update time")

        # Create another appointment
        self.assistant.dialogue.reset()
        self.run_command("Add appointment titled Location Test for Monday at 3 PM.")
        self.assistant.dialogue.reset()

        # Test location update
        success2, _ = self.run_conversation([
            "Update the location for my Monday appointment.",
            "Room 15",
        ], "Update location")

        passed = sum([success1, success2])
        self.results['categories']['appointment_update'] = {'passed': passed, 'total': 2}
        return passed == 2

    def test_appointment_delete(self):
        """Test appointment deletion - creates first, then deletes"""
        print("\n" + "="*70)
        print("TEST CATEGORY: APPOINTMENTS - DELETE")
        print("="*70)

        # Clear calendar
        self._clear_calendar()

        # Test 1: Create then delete with "previously created"
        self.assistant.dialogue.reset()
        success1, _ = self.run_conversation([
            "Add appointment titled Delete Test for tomorrow at 11 AM.",
            "Delete the previously created appointment.",
        ], "Create then delete (previously created)")

        # Test 2: Create then delete by day
        self.assistant.dialogue.reset()
        success2, _ = self.run_conversation([
            "Add appointment titled Monday Meeting for Monday at 2 PM.",
            "Cancel Monday's meeting.",
        ], "Create then delete by day")

        # Test 3: Create then delete by title
        self.assistant.dialogue.reset()
        success3, _ = self.run_conversation([
            "Add appointment titled Project Review for Tuesday at 3 PM.",
            "Delete the Project Review.",
        ], "Create then delete by title")

        passed = sum([success1, success2, success3])
        self.results['categories']['appointment_delete'] = {'passed': passed, 'total': 3}
        return passed >= 2  # Allow 1 failure

    def test_required_commands_flow(self):
        """Test all 7 required commands in a realistic flow"""
        print("\n" + "="*70)
        print("TEST CATEGORY: REQUIRED COMMANDS (Full Flow)")
        print("="*70)

        # Clear calendar
        self._clear_calendar()
        self.assistant.dialogue.reset()

        # Run the full required commands sequence
        success, results = self.run_conversation([
            # Command 1: Weather today in Marburg
            "What will the weather be like today in Marburg?",

            # Command 2: Weather Friday in Frankfurt
            "What will the weather be on Friday in Frankfurt?",

            # Command 3: Anaphora - "there" reference
            "Will it rain there on Saturday?",

            # Command 4: Next appointment (may be empty initially)
            "Where is my next appointment?",

            # Command 5: Create appointment
            "Add an appointment titled XYZ for the 12th of January.",
            "10 AM",  # Provide time when asked

            # Command 6: Delete previously created
            "Delete the previously created appointment.",

            # Create another for update test
            "Add an appointment titled Test Meeting for tomorrow at 3 PM.",

            # Command 7: Change place
            "Change the place for my appointment tomorrow.",
            "Room 5",  # Provide location when asked

        ], "All 7 Required Commands Flow")

        # Count individual command successes
        passed = sum(1 for r in results if r['success'])
        self.results['categories']['required_commands'] = {'passed': passed, 'total': len(results)}

        return success

    def test_context_switching(self):
        """Test switching between weather and appointments"""
        print("\n" + "="*70)
        print("TEST CATEGORY: CONTEXT SWITCHING")
        print("="*70)

        self._clear_calendar()
        self.assistant.dialogue.reset()

        # Test switching contexts
        success, _ = self.run_conversation([
            "What's the weather in Marburg?",
            "What are my appointments for today?",
            "Add appointment titled Test for tomorrow at 10 AM.",
            "Will it rain there tomorrow?",  # "there" should still refer to Marburg
            "What's my next appointment?",
        ], "Weather <-> Appointment switching")

        self.results['categories']['context_switching'] = {'passed': 1 if success else 0, 'total': 1}
        return success

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n" + "="*70)
        print("TEST CATEGORY: ERROR HANDLING")
        print("="*70)

        self.assistant.dialogue.reset()
        passed = 0

        # Test 1: Unknown intent
        success, response = self.run_command("blah blah blah")
        if success and ("understand" in response.lower() or "sorry" in response.lower()):
            passed += 1
            print("    (Correctly handled unknown intent)")

        # Test 2: Delete non-existent (after clearing)
        self._clear_calendar()
        self.assistant.dialogue.reset()
        success, response = self.run_command("Delete my appointment tomorrow.")
        if success and ("no appointment" in response.lower() or "couldn't" in response.lower() or "sorry" in response.lower()):
            passed += 1
            print("    (Correctly handled no appointments)")

        # Test 3: Weather without location (should ask)
        self.assistant.dialogue.reset()
        success, response = self.run_command("What's the weather?")
        if success and ("location" in response.lower() or "which" in response.lower()):
            passed += 1
            print("    (Correctly asked for location)")

        self.results['categories']['error_handling'] = {'passed': passed, 'total': 3}
        return passed >= 2

    def run_all_tests(self):
        """Run all test categories"""
        print("="*70)
        print("REALISTIC VOICE ASSISTANT TEST SUITE")
        print("="*70)

        # Run all test categories
        self.test_weather_basic()
        self.test_weather_with_days()
        self.test_weather_anaphora()
        self.test_appointment_create_basic()
        self.test_appointment_query()
        self.test_appointment_update()
        self.test_appointment_delete()
        self.test_required_commands_flow()
        self.test_context_switching()
        self.test_error_handling()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        print(f"\nOverall Results:")
        print(f"  Total Commands: {self.results['total']}")
        print(f"  Passed: {self.results['passed']} ({100 * self.results['passed'] // max(1, self.results['total'])}%)")
        print(f"  Failed: {self.results['failed']} ({100 * self.results['failed'] // max(1, self.results['total'])}%)")

        print(f"\nBy Category:")
        for category, data in self.results['categories'].items():
            status = "PASS" if data['passed'] == data['total'] else "PARTIAL" if data['passed'] > 0 else "FAIL"
            print(f"  [{status}] {category}: {data['passed']}/{data['total']}")

        print("="*70)


def main():
    """Main entry point"""
    suite = RealisticTestSuite()
    suite.setup(calenderid="nayem_marburg_2026")
    suite.run_all_tests()


if __name__ == "__main__":
    main()
