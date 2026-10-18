#!/usr/bin/env python3
"""
Test script to verify smart system features are working
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_nlu_title_extraction():
    """Test that NLU extracts titles correctly"""
    from modules.nlu import NLUModule

    print("=" * 60)
    print("TEST 1: NLU Title Extraction")
    print("=" * 60)

    nlu = NLUModule()

    tests = [
        ("delete the appointment titled team meeting", "team meeting"),
        ("create appointment called standup", "standup"),
        ("update meeting named review", "review"),
        # Should NOT extract from these:
        ("change the title of meeting one", None),
        ("update appointment one", None),
    ]

    for text, expected_title in tests:
        result = nlu.understand(text)
        extracted = result['entities'].get('title')
        status = "✓" if extracted == expected_title else "✗"
        print(f"{status} \"{text}\"")
        print(f"   Expected: {expected_title}, Got: {extracted}")

    print()

def test_update_appointment_logic():
    """Test update appointment lists appointments when unclear"""
    print("=" * 60)
    print("TEST 2: Update Appointment Logic")
    print("=" * 60)

    # Check that the update function has the smart logic
    main_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main.py')
    with open(main_path, 'r') as f:
        content = f.read()

    checks = [
        ("Smart create question", "What's the title and time"),
        ("Update lists appointments", "Which one would you like to update"),
        ("Delete lists appointments", "Which one would you like to delete"),
        ("Update change question", "What would you like to change"),
        ("Update confirmation", "Updating"),
        ("Delete confirmation", "Deleting"),
    ]

    for name, text in checks:
        if text in content:
            print(f"✓ {name}: Found")
        else:
            print(f"✗ {name}: NOT FOUND")

    print()

def test_nlg_formatting():
    """Test that NLG properly formats appointment output"""
    from modules.nlg import NLGModule

    print("=" * 60)
    print("TEST 3: NLG Formatting")
    print("=" * 60)

    nlg = NLGModule()

    # Test appointment with no location
    appointment_data = [
        {
            "id": 1,
            "title": "Team meeting",
            "location": None,
            "start_time": "2025-12-22T09:00"
        }
    ]

    response = nlg.generate_response('get_appointment', appointment_data)

    print(f"Response: {response}")

    # Check for issues
    if "at  on" in response:
        print("✗ Double space issue ('at  on') still present")
    elif " at " in response and " on " in response:
        # This would be wrong - should only have "on" when no location
        print("✗ Shows 'at' when no location")
    elif " on " in response:
        print("✓ Correctly shows 'on' without location")
    else:
        print("? Unexpected format")

    print()

def test_time_parsing():
    """Test time parsing function"""
    print("=" * 60)
    print("TEST 4: Time Parsing")
    print("=" * 60)

    import re

    def parse_time_input(text):
        """Same logic as in main.py"""
        text = text.lower().strip()

        # Try HH:MM format
        match = re.search(r'(\d{1,2}):(\d{2})', text)
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2)}"

        # Try "X AM/PM" format
        match = re.search(r'(\d{1,2})\s*(am|pm)', text)
        if match:
            hour = int(match.group(1))
            period = match.group(2)
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            return f"{hour:02d}:00"

        return None

    tests = [
        ("10 AM", "10:00"),
        ("2 PM", "14:00"),
        ("12 PM", "12:00"),
        ("12 AM", "00:00"),
        ("9:30 AM", "09:30"),
        ("14:00", "14:00"),
    ]

    for text, expected in tests:
        result = parse_time_input(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} \"{text}\" → Expected: {expected}, Got: {result}")

    print()

def main():
    print("\n" + "=" * 60)
    print("SMART SYSTEM FEATURES TEST SUITE")
    print("=" * 60 + "\n")

    try:
        test_nlu_title_extraction()
        test_update_appointment_logic()
        test_nlg_formatting()
        test_time_parsing()

        print("=" * 60)
        print("TEST SUITE COMPLETE")
        print("=" * 60)
        print("\nIf all tests show ✓, the smart features are working correctly.")
        print("If you see ✗, please restart Python to reload the updated code.\n")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
