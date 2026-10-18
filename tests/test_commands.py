#!/usr/bin/env python3
"""
Test Script for Required Commands
Tests all required commands from the project specification
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import VoiceAssistant


def test_required_commands():
    """Test all required commands"""

    print("=" * 80)
    print("Testing Voice Assistant - Required Commands")
    print("=" * 80)
    print()

    # Create assistant in text mode for testing
    assistant = VoiceAssistant(calenderid="nayem_marburg_2026", use_voice=False)

    # List of required commands from specification
    test_commands = [
        "What will the weather be like today in Marburg?",
        "What will the weather be on Friday in Frankfurt?",
        "Will it rain there on Saturday?",
        "Where is my next appointment?",
        "Add an appointment titled XYZ for the 12th of January.",
        "Delete the previously created appointment.",
        "Change the place for my appointment tomorrow.",
    ]

    results = []

    for i, command in enumerate(test_commands, 1):
        print(f"\n{'=' * 80}")
        print(f"Test {i}/{len(test_commands)}: {command}")
        print('=' * 80)

        try:
            response = assistant.process_input(command)

            result = {
                'command': command,
                'success': response is not None and len(response) > 0,
                'response': response
            }
            results.append(result)

            print(f"\n✓ Test {i} completed")

        except Exception as e:
            print(f"\n✗ Test {i} failed with error: {e}")
            results.append({
                'command': command,
                'success': False,
                'response': None,
                'error': str(e)
            })

        print()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"\nPassed: {passed}/{total} ({100 * passed // total}%)")
    print()

    for i, result in enumerate(results, 1):
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        print(f"{i}. {status}: {result['command']}")

    print("\n" + "=" * 80)

    return results


if __name__ == "__main__":
    test_required_commands()
