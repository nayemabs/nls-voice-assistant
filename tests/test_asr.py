#!/usr/bin/env python3
"""
ASR Test Script for Voice Assistant
Tests the voice assistant with actual speech recognition
Can be used to record test results for evaluation
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import VoiceAssistant


def load_test_commands(filename=None):
    """Load test commands from the conversation file"""
    if filename is None:
        # Default to test_conversations.txt in the same directory as this script
        filename = os.path.join(os.path.dirname(__file__), "test_conversations.txt")
    commands = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines, comments, headers, and instructions
                if (line and
                    not line.startswith('=') and
                    not line.startswith('-') and
                    not line.startswith('[') and
                    not line.startswith('User:') and
                    not line.startswith('Instructions:') and
                    not line.startswith('Notes:') and
                    not line.startswith('Total') and
                    not line.startswith('SECTION') and
                    not line.startswith('CATEGORY') and
                    not line.startswith('END') and
                    len(line) > 3):
                    # Clean up the line
                    if line.startswith('User: '):
                        line = line[6:]
                    # Check if it looks like a command (not metadata)
                    if not any(line.startswith(x) for x in ['---', '...', 'For', 'The']):
                        commands.append(line)
    except FileNotFoundError:
        print(f"Warning: {filename} not found, using default commands")
        commands = get_default_commands()
    return commands


def get_default_commands():
    """Default test commands if file not found"""
    return [
        "What will the weather be like today in Marburg?",
        "What will the weather be on Friday in Frankfurt?",
        "Will it rain there on Saturday?",
        "Where is my next appointment?",
        "Add an appointment titled XYZ for the 12th of January.",
        "Delete the previously created appointment.",
        "Change the place for my appointment tomorrow.",
    ]


def test_with_voice(assistant, num_tests=None):
    """
    Run tests using voice input

    Args:
        assistant: VoiceAssistant instance with voice enabled
        num_tests: Number of tests to run (None for unlimited)
    """
    results = []
    test_count = 0

    print("\n" + "=" * 60)
    print("ASR VOICE TEST MODE")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Speak clearly into your microphone")
    print("2. Wait for 'Listening...' prompt before speaking")
    print("3. Say 'exit' or 'quit' to end testing")
    print("4. Results will be saved to asr_test_results.json")
    print("=" * 60 + "\n")

    assistant._speak("Voice testing mode started. I will record your commands and my responses.")

    while True:
        if num_tests and test_count >= num_tests:
            break

        test_count += 1
        print(f"\n--- Test {test_count} ---")

        # Get voice input
        user_input = assistant._listen()

        if not user_input:
            print("No speech detected. Try again.")
            assistant._speak("I didn't hear anything. Please try again.")
            test_count -= 1
            continue

        # Check for exit
        if user_input.lower() in ['exit', 'quit', 'stop', 'end']:
            assistant._speak("Ending voice test.")
            break

        # Process input
        response = assistant.process_input(user_input)

        # Record result
        result = {
            'test_number': test_count,
            'timestamp': datetime.now().isoformat(),
            'recognized_text': user_input,
            'response': response,
            'success': response is not None and len(response) > 0
        }
        results.append(result)

        # Speak response
        if response:
            assistant._speak(response)
        else:
            assistant._speak("I couldn't process that request.")

    return results


def test_with_text_verification(assistant, commands):
    """
    Run tests with text input but verify ASR transcription accuracy
    Useful for testing if commands from text match expected behavior

    Args:
        assistant: VoiceAssistant instance (can be text mode)
        commands: List of commands to test
    """
    results = []

    print("\n" + "=" * 60)
    print("TEXT-BASED ASR SIMULATION TEST")
    print("=" * 60)
    print(f"\nTesting {len(commands)} commands...")
    print("=" * 60 + "\n")

    for i, command in enumerate(commands, 1):
        print(f"\n--- Test {i}/{len(commands)} ---")
        print(f"Command: {command}")

        # Clear state
        assistant.dialogue.clear_state()

        try:
            response = assistant.process_input(command)
            success = response is not None and len(response) > 0

            result = {
                'test_number': i,
                'command': command,
                'response': response,
                'success': success
            }
            results.append(result)

            status = "PASS" if success else "FAIL"
            print(f"Status: [{status}]")
            print(f"Response: {response[:100] if response else 'None'}...")

        except Exception as e:
            results.append({
                'test_number': i,
                'command': command,
                'response': None,
                'success': False,
                'error': str(e)
            })
            print(f"Status: [FAIL - Error]")
            print(f"Error: {e}")

    return results


def save_results(results, filename="asr_test_results.json"):
    """Save test results to JSON file"""
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(results),
        'passed': sum(1 for r in results if r.get('success', False)),
        'failed': sum(1 for r in results if not r.get('success', False)),
        'results': results
    }

    with open(filename, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to {filename}")
    return summary


def print_summary(summary):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ({100 * summary['passed'] // max(1, summary['total_tests'])}%)")
    print(f"Failed: {summary['failed']} ({100 * summary['failed'] // max(1, summary['total_tests'])}%)")
    print("=" * 60)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="ASR Test Script for Voice Assistant")
    parser.add_argument('--mode', choices=['voice', 'text', 'both'], default='text',
                       help='Test mode: voice (use microphone), text (simulate), both')
    parser.add_argument('--num-tests', type=int, default=None,
                       help='Number of voice tests to run (voice mode only)')
    parser.add_argument('--output', type=str, default='asr_test_results.json',
                       help='Output file for results')
    parser.add_argument('--commands-file', type=str, default='test_conversations.txt',
                       help='File containing test commands')

    args = parser.parse_args()

    # Load test commands
    commands = load_test_commands(args.commands_file)
    print(f"Loaded {len(commands)} test commands")

    all_results = []

    if args.mode in ['text', 'both']:
        # Text mode testing
        print("\n" + "=" * 60)
        print("RUNNING TEXT-BASED TESTS")
        print("=" * 60)

        assistant = VoiceAssistant(calenderid="asr_test_001", use_voice=False)
        text_results = test_with_text_verification(assistant, commands)
        all_results.extend(text_results)

    if args.mode in ['voice', 'both']:
        # Voice mode testing
        print("\n" + "=" * 60)
        print("RUNNING VOICE-BASED TESTS")
        print("=" * 60)

        try:
            assistant = VoiceAssistant(calenderid="asr_test_001", use_voice=True)
            voice_results = test_with_voice(assistant, args.num_tests)
            all_results.extend(voice_results)
        except Exception as e:
            print(f"\nVoice testing failed: {e}")
            print("Make sure you have a microphone connected and required libraries installed.")

    # Save and summarize results
    if all_results:
        summary = save_results(all_results, args.output)
        print_summary(summary)
    else:
        print("No tests were run.")


if __name__ == "__main__":
    main()
