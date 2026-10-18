#!/usr/bin/env python3
"""
Batch Audio Testing Script
Tests the voice assistant using pre-recorded audio files
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.asr_fast import ASRModule
from modules.nlu import NLUModule


def load_expected_commands(commands_file):
    """Load expected commands from the test file"""
    commands = {}
    with open(commands_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Look for numbered commands like "1. What will the weather..."
            if line and line[0].isdigit():
                # Extract number and command
                parts = line.split('.', 1)
                if len(parts) == 2:
                    try:
                        num = int(parts[0].strip())
                        command = parts[1].strip()
                        commands[num] = command
                    except ValueError:
                        continue
    return commands


def find_audio_files(audio_dir):
    """Find all audio files in the directory"""
    audio_files = {}
    for ext in ['*.m4a', '*.mp3', '*.wav', '*.mp3.m4a']:
        for f in Path(audio_dir).glob(ext):
            # Extract number from filename
            name = f.stem
            # Handle "1.mp3" or just "1"
            name = name.replace('.mp3', '')
            try:
                num = int(name)
                audio_files[num] = str(f)
            except ValueError:
                continue
    return audio_files


def test_audio_files(audio_dir, commands_file, output_file=None, verbose=True):
    """
    Test all audio files and compare results

    Args:
        audio_dir: Directory containing audio files
        commands_file: Path to expected commands file
        output_file: Optional path to save results JSON
        verbose: Print progress
    """
    print("=" * 60)
    print("Voice Assistant Audio Batch Test")
    print("=" * 60)

    # Initialize modules
    print("\nInitializing ASR module...")
    asr = ASRModule(model_size="small")
    print("Initializing NLU module...")
    nlu = NLUModule()

    # Load expected commands and audio files
    expected = load_expected_commands(commands_file)
    audio_files = find_audio_files(audio_dir)

    print(f"\nFound {len(audio_files)} audio files")
    print(f"Found {len(expected)} expected commands")

    results = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(audio_files),
        'tests': [],
        'summary': {
            'passed': 0,
            'failed': 0,
            'intent_accuracy': 0,
            'transcription_issues': []
        }
    }

    # Process each audio file
    for num in sorted(audio_files.keys()):
        audio_path = audio_files[num]
        expected_cmd = expected.get(num, "Unknown")

        if verbose:
            print(f"\n--- Test {num} ---")
            print(f"Expected: {expected_cmd}")

        # Transcribe audio
        transcribed = asr.transcribe_file(audio_path)

        if verbose:
            print(f"Transcribed: {transcribed}")

        # Run through NLU
        if transcribed:
            nlu_result = nlu.understand(transcribed)
            intent = nlu_result['intent']
            entities = nlu_result['entities']
        else:
            intent = 'error'
            entities = {}

        if verbose:
            print(f"Intent: {intent}")
            print(f"Entities: {entities}")

        # Determine expected intent from command text
        expected_intent = _infer_expected_intent(expected_cmd)

        # Check if intent matches
        intent_match = (intent == expected_intent) if expected_intent else True

        test_result = {
            'test_num': num,
            'audio_file': os.path.basename(audio_path),
            'expected_command': expected_cmd,
            'transcribed': transcribed,
            'expected_intent': expected_intent,
            'detected_intent': intent,
            'entities': entities,
            'intent_match': intent_match,
            'passed': intent_match and transcribed is not None
        }

        results['tests'].append(test_result)

        if test_result['passed']:
            results['summary']['passed'] += 1
            if verbose:
                print("PASSED")
        else:
            results['summary']['failed'] += 1
            if verbose:
                print(f"FAILED - Expected intent: {expected_intent}")

    # Calculate accuracy
    total = len(results['tests'])
    if total > 0:
        results['summary']['intent_accuracy'] = (results['summary']['passed'] / total) * 100

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Accuracy: {results['summary']['intent_accuracy']:.1f}%")

    # Save results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_file}")

    return results


def _infer_expected_intent(command):
    """Infer expected intent from command text"""
    cmd_lower = command.lower()

    # Weather patterns
    if any(w in cmd_lower for w in ['weather', 'temperature', 'rain', 'snow', 'sunny', 'cloudy', 'warm', 'cold', 'forecast', 'outside']):
        return 'weather_query'

    # Delete appointment
    if any(w in cmd_lower for w in ['delete', 'remove', 'cancel', 'drop']):
        return 'delete_appointment'

    # Update appointment
    if any(w in cmd_lower for w in ['update', 'change', 'modify', 'edit', 'reschedule', 'move']):
        return 'update_appointment'

    # Create appointment
    if any(w in cmd_lower for w in ['add', 'create', 'schedule', 'book', 'set up', 'make', 'new']):
        return 'create_appointment'

    # Get appointment
    if any(w in cmd_lower for w in ['appointment', 'meeting', 'calendar', 'schedule', 'next', 'free', 'empty']):
        return 'get_appointment'

    return None


def test_single_audio(audio_path, verbose=True):
    """Test a single audio file"""
    print("Initializing ASR module...")
    asr = ASRModule(model_size="small")
    print("Initializing NLU module...")
    nlu = NLUModule()

    print(f"\nTesting: {audio_path}")

    transcribed = asr.transcribe_file(audio_path)
    print(f"Transcribed: {transcribed}")

    if transcribed:
        nlu_result = nlu.understand(transcribed)
        print(f"Intent: {nlu_result['intent']}")
        print(f"Entities: {nlu_result['entities']}")

    return transcribed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test voice assistant with audio files')
    parser.add_argument('--audio-dir', '-d',
                        default='data/Shibin',
                        help='Directory containing audio files')
    parser.add_argument('--commands-file', '-c',
                        default='tests/voice_commands_simple.txt',
                        help='Path to expected commands file')
    parser.add_argument('--output', '-o',
                        default='tests/audio_test_results.json',
                        help='Output file for results')
    parser.add_argument('--single', '-s',
                        help='Test a single audio file')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet mode (less output)')

    args = parser.parse_args()

    if args.single:
        test_single_audio(args.single, verbose=not args.quiet)
    else:
        test_audio_files(
            args.audio_dir,
            args.commands_file,
            args.output,
            verbose=not args.quiet
        )
