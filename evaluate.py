#!/usr/bin/env python3
"""
Voice Assistant Evaluation Script
Implements state-of-the-art evaluation metrics for SLU (Spoken Language Understanding)

Metrics:
- ASR: Word Error Rate (WER), Character Error Rate (CER)
- Intent Classification: Accuracy, Precision, Recall, F1 (per-class and macro)
- Slot/Entity Extraction: Slot F1, Entity-level Precision/Recall
- End-to-End: Semantic Error Rate, Sentence Accuracy
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.asr_fast import ASRModule
from modules.nlu import NLUModule
from modules.nlg import NLGModule

# Try to import hybrid NLU
HYBRID_AVAILABLE = False
try:
    from modules.nlu_hybrid import HybridNLUModule, get_nlu_module
    HYBRID_AVAILABLE = True
except ImportError:
    pass


# ===================== EVALUATION METRICS =====================

def word_error_rate(reference: str, hypothesis: str) -> Tuple[float, Dict]:
    """
    Calculate Word Error Rate (WER) using dynamic programming

    WER = (S + D + I) / N
    Where S=substitutions, D=deletions, I=insertions, N=words in reference

    Returns:
        Tuple of (WER, details dict)
    """
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    # Dynamic programming matrix
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

    # Initialize
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    # Fill matrix
    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    # Backtrack to count S, D, I
    i, j = len(ref_words), len(hyp_words)
    s, d_count, ins = 0, 0, 0

    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_words[i - 1] == hyp_words[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + 1:
            s += 1
            i -= 1
            j -= 1
        elif j > 0 and d[i][j] == d[i][j - 1] + 1:
            ins += 1
            j -= 1
        else:
            d_count += 1
            i -= 1

    n = len(ref_words)
    wer = (s + d_count + ins) / n if n > 0 else 0.0

    return wer, {
        'substitutions': s,
        'deletions': d_count,
        'insertions': ins,
        'reference_words': n,
        'hypothesis_words': len(hyp_words)
    }


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Calculate Character Error Rate (CER)"""
    ref_chars = list(reference.lower())
    hyp_chars = list(hypothesis.lower())

    # Same DP as WER but on characters
    d = [[0] * (len(hyp_chars) + 1) for _ in range(len(ref_chars) + 1)]

    for i in range(len(ref_chars) + 1):
        d[i][0] = i
    for j in range(len(hyp_chars) + 1):
        d[0][j] = j

    for i in range(1, len(ref_chars) + 1):
        for j in range(1, len(hyp_chars) + 1):
            if ref_chars[i - 1] == hyp_chars[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(d[i - 1][j - 1], d[i][j - 1], d[i - 1][j]) + 1

    n = len(ref_chars)
    return d[len(ref_chars)][len(hyp_chars)] / n if n > 0 else 0.0


def calculate_intent_metrics(y_true: List[str], y_pred: List[str]) -> Dict:
    """
    Calculate intent classification metrics

    Returns:
        Dict with accuracy, per-class precision/recall/f1, and macro averages
    """
    # Get all unique labels
    labels = sorted(set(y_true) | set(y_pred))

    # Accuracy
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / len(y_true) if y_true else 0.0

    # Per-class metrics
    per_class = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        per_class[label] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': sum(1 for t in y_true if t == label)
        }

    # Macro averages
    macro_precision = sum(m['precision'] for m in per_class.values()) / len(per_class) if per_class else 0.0
    macro_recall = sum(m['recall'] for m in per_class.values()) / len(per_class) if per_class else 0.0
    macro_f1 = sum(m['f1'] for m in per_class.values()) / len(per_class) if per_class else 0.0

    # Confusion matrix
    confusion = defaultdict(lambda: defaultdict(int))
    for t, p in zip(y_true, y_pred):
        confusion[t][p] += 1

    return {
        'accuracy': accuracy,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'per_class': per_class,
        'confusion_matrix': {k: dict(v) for k, v in confusion.items()}
    }


def format_confusion_matrix(confusion_matrix: Dict, labels: List[str]) -> str:
    """
    Format confusion matrix as a readable text table

    Args:
        confusion_matrix: Dict of {true_label: {predicted_label: count}}
        labels: List of all labels in order

    Returns:
        Formatted string representation of confusion matrix
    """
    # Abbreviate labels for display
    abbrev = {
        'create_appointment': 'create',
        'delete_appointment': 'delete',
        'get_appointment': 'get',
        'update_appointment': 'update',
        'weather_query': 'weather',
        'unknown': 'unk'
    }

    # Get abbreviated labels
    short_labels = [abbrev.get(l, l[:6]) for l in labels]

    # Calculate column width
    max_label_len = max(len(l) for l in short_labels) + 1
    cell_width = max(4, max_label_len)

    lines = []

    # Header row
    header = " " * (cell_width + 2) + "│ " + " ".join(f"{l:^{cell_width}}" for l in short_labels) + " │"
    separator = "─" * (cell_width + 2) + "┼" + "─" * (len(short_labels) * (cell_width + 1) + 1) + "┤"

    lines.append("   Confusion Matrix (rows=true, cols=predicted)")
    lines.append("   " + "─" * (len(header) - 3))
    lines.append("   " + header)
    lines.append("   " + separator)

    # Data rows
    for i, true_label in enumerate(labels):
        row_data = []
        for pred_label in labels:
            count = confusion_matrix.get(true_label, {}).get(pred_label, 0)
            row_data.append(f"{count:^{cell_width}}")

        row = f"{short_labels[i]:>{cell_width}} │ " + " ".join(row_data) + " │"
        lines.append("   " + row)

    lines.append("   " + "─" * (len(header) - 3))

    return "\n".join(lines)


def calculate_task_success_by_intent(results: List[Dict]) -> Dict:
    """
    Calculate task success rate broken down by intent

    A task is successful if both intent and all slots are correct.

    Returns:
        Dict with per-intent success rates and overall rate
    """
    intent_success = defaultdict(lambda: {'success': 0, 'total': 0})

    for r in results:
        expected_intent = r['expected_intent']
        intent_success[expected_intent]['total'] += 1

        if r['intent_correct'] and r['slots_correct']:
            intent_success[expected_intent]['success'] += 1

    # Calculate rates
    per_intent = {}
    for intent, counts in intent_success.items():
        rate = counts['success'] / counts['total'] if counts['total'] > 0 else 0.0
        per_intent[intent] = {
            'success_rate': rate,
            'success_count': counts['success'],
            'total_count': counts['total']
        }

    # Overall
    total_success = sum(c['success'] for c in intent_success.values())
    total_count = sum(c['total'] for c in intent_success.values())
    overall_rate = total_success / total_count if total_count > 0 else 0.0

    return {
        'overall': overall_rate,
        'per_intent': per_intent
    }


def calculate_slot_f1(expected_entities: Dict, predicted_entities: Dict) -> Dict:
    """
    Calculate slot/entity extraction F1 score

    Uses normalized matching for slot values (handles format variations)
    """
    # Normalize entity comparison
    def normalize(v):
        if v is None:
            return ''
        return str(v).lower().strip()

    def normalize_time(t):
        """Normalize time to standard format for comparison"""
        if not t:
            return ''
        t = t.lower().strip()
        # Remove extra spaces
        t = re.sub(r'\s+', ' ', t)
        # Normalize "9 am" to "9:00 am", "3 pm" to "3:00 pm"
        match = re.match(r'^(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)$', t)
        if match:
            hour = match.group(1)
            ampm = match.group(2).replace('.', '')
            return f"{hour}:00 {ampm}"
        # Normalize "9:00am" to "9:00 am"
        match = re.match(r'^(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)$', t)
        if match:
            hour = match.group(1)
            mins = match.group(2)
            ampm = match.group(3).replace('.', '')
            return f"{hour}:{mins} {ampm}"
        return t

    def normalize_day(d):
        """Normalize day/date to standard format for comparison"""
        if not d:
            return ''
        d = d.lower().strip()
        # Normalize "12th of january" to "january 12"
        match = re.match(r'^(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(\w+)$', d)
        if match:
            day_num = match.group(1)
            month = match.group(2)
            return f"{month} {day_num}"
        return d

    def normalize_slot(slot_name, value):
        """Apply slot-specific normalization"""
        v = normalize(value)
        if slot_name == 'time':
            return normalize_time(v)
        elif slot_name == 'day':
            return normalize_day(v)
        return v

    # Get all slot types
    all_slots = set(expected_entities.keys()) | set(predicted_entities.keys())
    # Exclude meta-slots and context-helper slots from comparison
    # These are useful for the system but not core slots for evaluation
    excluded_slots = {
        'temporal_reference', 'resolved_place',  # Meta-slots
        'condition', 'next', 'next_week',  # Context helpers
    }
    all_slots = {s for s in all_slots if s not in excluded_slots}

    tp = fp = fn = 0
    slot_details = {}

    for slot in all_slots:
        expected_val = normalize_slot(slot, expected_entities.get(slot, ''))
        predicted_val = normalize_slot(slot, predicted_entities.get(slot, ''))

        if expected_val and predicted_val:
            if expected_val == predicted_val:
                tp += 1
                slot_details[slot] = 'correct'
            else:
                fp += 1
                fn += 1
                slot_details[slot] = f'mismatch: expected="{expected_val}", got="{predicted_val}"'
        elif expected_val and not predicted_val:
            fn += 1
            slot_details[slot] = f'missed: expected="{expected_val}"'
        elif predicted_val and not expected_val:
            fp += 1
            slot_details[slot] = f'spurious: got="{predicted_val}"'

    # Handle edge case: if there are no slots to compare (both empty after filtering),
    # that's a perfect match
    if tp == 0 and fp == 0 and fn == 0:
        return {
            'precision': 1.0,
            'recall': 1.0,
            'f1': 1.0,
            'details': slot_details
        }

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'details': slot_details
    }


def semantic_error_rate(results: List[Dict]) -> float:
    """
    Calculate Semantic Error Rate (SER)

    A sentence has a semantic error if:
    - Intent is wrong, OR
    - Any slot is wrong

    SER = sentences_with_errors / total_sentences
    """
    errors = 0
    for r in results:
        if not r.get('intent_correct', False):
            errors += 1
        elif not r.get('slots_correct', True):
            errors += 1

    return errors / len(results) if results else 0.0


# ===================== EXPECTED ANNOTATIONS =====================

def get_expected_intent(command: str) -> str:
    """Infer expected intent from command text"""
    cmd_lower = command.lower()

    if any(w in cmd_lower for w in ['weather', 'temperature', 'rain', 'snow', 'sunny',
                                      'cloudy', 'warm', 'cold', 'forecast', 'outside',
                                      'foggy', 'thunder', 'windy', 'misty', 'showers', 'clear']):
        return 'weather_query'

    if any(w in cmd_lower for w in ['delete', 'remove', 'cancel', 'drop']):
        return 'delete_appointment'

    if any(w in cmd_lower for w in ['update', 'change', 'modify', 'edit', 'reschedule', 'move']):
        return 'update_appointment'

    if any(w in cmd_lower for w in ['add', 'create', 'schedule', 'book', 'set up', 'make', 'new']):
        return 'create_appointment'

    if any(w in cmd_lower for w in ['appointment', 'meeting', 'calendar', 'schedule', 'next', 'free', 'empty']):
        return 'get_appointment'

    return 'unknown'


def get_expected_entities(command: str, intent: str) -> Dict:
    """Extract expected entities from command text"""
    entities = {}
    cmd_lower = command.lower()

    # Known German cities for place extraction
    german_cities = [
        'marburg', 'frankfurt', 'berlin', 'munich', 'hamburg', 'cologne',
        'stuttgart', 'dresden', 'leipzig', 'dusseldorf', 'bonn', 'hannover',
        'hanover', 'bremen', 'essen', 'nuremberg', 'dortmund', 'duisburg',
        'bochum', 'wuppertal', 'bielefeld', 'munster', 'karlsruhe', 'mannheim'
    ]

    # Extract place - multiple patterns
    place = None

    # Pattern 1: "in <city>" (most common)
    place_match = re.search(r'\bin\s+([A-Za-z]+)(?:\s+(?:today|tomorrow|on|this|next)|[?.,]|$)', command, re.IGNORECASE)
    if place_match:
        place = place_match.group(1)

    # Pattern 2: "for <city>" (e.g., "Tell me the weather for Cologne")
    if not place:
        place_match = re.search(r'\bfor\s+([A-Za-z]+)(?:\s+(?:today|tomorrow|on)|[?.,]|$)', command, re.IGNORECASE)
        if place_match and place_match.group(1).lower() not in ['the', 'my', 'tomorrow', 'today', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            place = place_match.group(1)

    # Pattern 3: Direct city name in weather context
    if not place and intent == 'weather_query':
        for city in german_cities:
            if city in cmd_lower:
                place = city.title()
                break

    if place and place.lower() in german_cities:
        entities['place'] = place.title()

    # Extract day
    days = ['today', 'tomorrow', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for day in days:
        if day in cmd_lower:
            entities['day'] = day
            break

    if 'day after tomorrow' in cmd_lower:
        entities['day'] = 'day after tomorrow'

    # Extract weekend/week references
    if 'this weekend' in cmd_lower:
        entities['day'] = 'weekend'
    elif 'next week' in cmd_lower:
        entities['day'] = 'next week'

    # Extract specific dates (e.g., "12th of January", "January 12")
    # Format to match NLU output: "month day"
    date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Za-z]+)', command, re.IGNORECASE)
    if date_match:
        month = date_match.group(2).lower()
        day_num = date_match.group(1)
        # Check if it's a valid month (not AM/PM or other words)
        valid_months = ['january', 'february', 'march', 'april', 'may', 'june',
                        'july', 'august', 'september', 'october', 'november', 'december']
        if month in valid_months:
            entities['day'] = f"{month} {day_num}"

    # Extract time - multiple patterns
    # Pattern: "at 3 PM", "at 10:00", "at 2:30 PM"
    time_match = re.search(r'at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', cmd_lower, re.IGNORECASE)
    if time_match:
        entities['time'] = time_match.group(1).strip()
    else:
        # Pattern: "for 2:30 PM" (alternate phrasing)
        time_match = re.search(r'for\s+(\d{1,2}:\d{2}\s*(?:am|pm)?)', cmd_lower, re.IGNORECASE)
        if time_match:
            entities['time'] = time_match.group(1).strip()

    # Extract title (for appointments) - multiple patterns
    title = None

    # Pattern 1: "titled <title>" - stop at "for the <date>" or "for <day>" or time markers
    title_match = re.search(r'titled\s+(.+?)(?:\s+for\s+(?:the\s+)?\d|\s+for\s+(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\s+on\s+|\s+at\s+\d|[.,]|$)', command, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    # Pattern 2: "called <title>" - stop at "for the <date>" or "for <day>" or time markers
    if not title:
        title_match = re.search(r'called\s+(.+?)(?:\s+for\s+(?:the\s+)?\d|\s+for\s+(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\s+on\s+|\s+at\s+\d|[.,]|$)', command, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()

    # Pattern 3: "named <title>" - stop at "for the <date>" or "for <day>" or time markers
    if not title:
        title_match = re.search(r'named\s+(.+?)(?:\s+for\s+(?:the\s+)?\d|\s+for\s+(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\s+on\s+|\s+at\s+\d|[.,]|$)', command, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()

    # Pattern 4: "the <title> appointment/meeting" (for delete/cancel)
    # Only match actual titles like "Team Meeting", not descriptions like "previously created"
    if not title and intent in ['delete_appointment', 'update_appointment']:
        title_match = re.search(r'the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:appointment|meeting)', command)
        if title_match:
            candidate = title_match.group(1).strip()
            # Exclude common descriptive words
            if candidate.lower() not in ['last', 'previous', 'previously', 'next', 'my', 'that', 'this', 'created']:
                title = candidate

    if title:
        entities['title'] = title

    return entities


# ===================== MAIN EVALUATION =====================

def load_commands(commands_file: str) -> Dict[int, str]:
    """Load expected commands from file"""
    commands = {}
    with open(commands_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and line[0].isdigit():
                parts = line.split('.', 1)
                if len(parts) == 2:
                    try:
                        num = int(parts[0].strip())
                        command = parts[1].strip()
                        commands[num] = command
                    except ValueError:
                        continue
    return commands


def find_audio_files(audio_dir: str) -> Dict[int, str]:
    """Find audio files in directory"""
    audio_files = {}
    for ext in ['*.m4a', '*.mp3', '*.wav', '*.mp3.m4a']:
        for f in Path(audio_dir).glob(ext):
            name = f.stem.replace('.mp3', '')
            try:
                num = int(name)
                audio_files[num] = str(f)
            except ValueError:
                continue
    return audio_files


def evaluate(audio_dir: str, commands_file: str, output_dir: str = 'tests/evaluation', use_hybrid: bool = False):
    """
    Run full evaluation pipeline

    Args:
        audio_dir: Directory with audio files
        commands_file: Path to expected commands
        output_dir: Directory to save evaluation results
        use_hybrid: Whether to use hybrid GLiNER NLU (default: False for regex NLU)
    """
    nlu_mode = "HYBRID (GLiNER)" if use_hybrid else "REGEX"
    print("=" * 70)
    print(f"VOICE ASSISTANT EVALUATION - {nlu_mode} NLU")
    print("State-of-the-Art SLU Metrics")
    print("=" * 70)

    # Initialize
    print("\nInitializing modules...")
    asr = ASRModule(model_size="small")

    if use_hybrid and HYBRID_AVAILABLE:
        print("Using HYBRID NLU (GLiNER + regex)")
        nlu = HybridNLUModule(use_gliner=True)
    else:
        if use_hybrid and not HYBRID_AVAILABLE:
            print("WARNING: Hybrid NLU not available, falling back to regex")
        print("Using REGEX NLU")
        nlu = NLUModule()

    # Initialize NLG for latency measurement
    nlg = NLGModule()

    # Load data
    commands = load_commands(commands_file)
    audio_files = find_audio_files(audio_dir)

    print(f"Found {len(audio_files)} audio files")
    print(f"Found {len(commands)} expected commands")

    # Prepare output directory
    os.makedirs(output_dir, exist_ok=True)

    # Evaluation storage
    results = []
    asr_results = []
    y_true_intent = []
    y_pred_intent = []

    # Latency tracking
    asr_latencies = []
    nlu_latencies = []
    nlg_latencies = []
    total_latencies = []

    # Process each file
    print("\nProcessing audio files...")
    for num in sorted(audio_files.keys()):
        if num not in commands:
            continue

        audio_path = audio_files[num]
        expected_cmd = commands[num]
        expected_intent = get_expected_intent(expected_cmd)
        expected_entities = get_expected_entities(expected_cmd, expected_intent)

        print(f"  Processing {num}...", end=' ', flush=True)

        # ASR with timing
        start_total = time.perf_counter()
        start_asr = time.perf_counter()
        transcribed = asr.transcribe_file(audio_path)
        asr_time = time.perf_counter() - start_asr

        if not transcribed:
            transcribed = ""

        asr_latencies.append(asr_time)

        # Calculate ASR metrics
        wer, wer_details = word_error_rate(expected_cmd, transcribed)
        cer = character_error_rate(expected_cmd, transcribed)

        asr_results.append({
            'id': num,
            'reference': expected_cmd,
            'hypothesis': transcribed,
            'wer': wer,
            'cer': cer,
            'wer_details': wer_details
        })

        # NLU with timing
        start_nlu = time.perf_counter()
        if transcribed:
            nlu_result = nlu.understand(transcribed)
            predicted_intent = nlu_result['intent']
            predicted_entities = nlu_result['entities']
        else:
            predicted_intent = 'error'
            predicted_entities = {}
        nlu_time = time.perf_counter() - start_nlu

        nlu_latencies.append(nlu_time)

        # NLG with timing (measures template processing latency)
        start_nlg = time.perf_counter()
        _ = nlg.generate_response(predicted_intent, None, predicted_entities)
        nlg_time = time.perf_counter() - start_nlg

        nlg_latencies.append(nlg_time)

        total_time = time.perf_counter() - start_total
        total_latencies.append(total_time)

        # Store for metrics
        y_true_intent.append(expected_intent)
        y_pred_intent.append(predicted_intent)

        # Calculate slot metrics
        slot_metrics = calculate_slot_f1(expected_entities, predicted_entities)

        intent_correct = (expected_intent == predicted_intent)
        slots_correct = (slot_metrics['f1'] == 1.0)

        result = {
            'id': num,
            'audio_file': os.path.basename(audio_path),
            'reference': expected_cmd,
            'transcription': transcribed,
            'expected_intent': expected_intent,
            'predicted_intent': predicted_intent,
            'intent_correct': intent_correct,
            'expected_entities': expected_entities,
            'predicted_entities': {k: v for k, v in predicted_entities.items()
                                   if k not in ['temporal_reference', 'resolved_place']},
            'slot_f1': slot_metrics['f1'],
            'slots_correct': slots_correct,
            'wer': wer,
            'cer': cer,
            'latency': {
                'asr_ms': asr_time * 1000,
                'nlu_ms': nlu_time * 1000,
                'nlg_ms': nlg_time * 1000,
                'total_ms': total_time * 1000
            }
        }
        results.append(result)

        status = "" if intent_correct else ""
        print(status)

    # ===================== CALCULATE OVERALL METRICS =====================
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)

    # ASR Metrics
    avg_wer = sum(r['wer'] for r in asr_results) / len(asr_results) if asr_results else 0
    avg_cer = sum(r['cer'] for r in asr_results) / len(asr_results) if asr_results else 0

    print("\n1. ASR PERFORMANCE")
    print("-" * 40)
    print(f"   Word Error Rate (WER):      {avg_wer:.2%}")
    print(f"   Character Error Rate (CER): {avg_cer:.2%}")

    # Intent Metrics
    intent_metrics = calculate_intent_metrics(y_true_intent, y_pred_intent)

    print("\n2. INTENT CLASSIFICATION")
    print("-" * 40)
    print(f"   Accuracy:        {intent_metrics['accuracy']:.2%}")
    print(f"   Macro Precision: {intent_metrics['macro_precision']:.2%}")
    print(f"   Macro Recall:    {intent_metrics['macro_recall']:.2%}")
    print(f"   Macro F1:        {intent_metrics['macro_f1']:.2%}")

    print("\n   Per-Class Performance:")
    for intent, metrics in intent_metrics['per_class'].items():
        print(f"     {intent:25s} P={metrics['precision']:.2f} R={metrics['recall']:.2f} F1={metrics['f1']:.2f} (n={metrics['support']})")

    # Slot Metrics
    all_slot_f1 = [r['slot_f1'] for r in results]
    avg_slot_f1 = sum(all_slot_f1) / len(all_slot_f1) if all_slot_f1 else 0

    print("\n3. SLOT/ENTITY EXTRACTION")
    print("-" * 40)
    print(f"   Average Slot F1: {avg_slot_f1:.2%}")

    # End-to-End Metrics
    ser = semantic_error_rate(results)
    sentence_acc = sum(1 for r in results if r['intent_correct'] and r['slots_correct']) / len(results) if results else 0

    print("\n4. END-TO-END PERFORMANCE")
    print("-" * 40)
    print(f"   Semantic Error Rate (SER): {ser:.2%}")
    print(f"   Sentence Accuracy:         {sentence_acc:.2%}")

    # Latency Metrics
    avg_asr_latency = sum(asr_latencies) / len(asr_latencies) * 1000 if asr_latencies else 0
    avg_nlu_latency = sum(nlu_latencies) / len(nlu_latencies) * 1000 if nlu_latencies else 0
    avg_nlg_latency = sum(nlg_latencies) / len(nlg_latencies) * 1000 if nlg_latencies else 0
    avg_total_latency = sum(total_latencies) / len(total_latencies) * 1000 if total_latencies else 0
    min_total_latency = min(total_latencies) * 1000 if total_latencies else 0
    max_total_latency = max(total_latencies) * 1000 if total_latencies else 0

    print("\n5. LATENCY METRICS")
    print("-" * 40)
    print(f"   Avg ASR Latency:     {avg_asr_latency:.0f} ms")
    print(f"   Avg NLU Latency:     {avg_nlu_latency:.0f} ms")
    print(f"   Avg NLG Latency:     {avg_nlg_latency:.2f} ms")
    print(f"   Avg Total Latency:   {avg_total_latency:.0f} ms")
    print(f"   Min/Max Total:       {min_total_latency:.0f} ms / {max_total_latency:.0f} ms")

    # Confusion Matrix
    labels = sorted(set(y_true_intent) | set(y_pred_intent))
    confusion_matrix_str = format_confusion_matrix(intent_metrics['confusion_matrix'], labels)

    print("\n6. INTENT CONFUSION MATRIX")
    print("-" * 40)
    print(confusion_matrix_str)

    # Task Success Rate by Intent
    task_success = calculate_task_success_by_intent(results)

    print("\n7. TASK SUCCESS RATE")
    print("-" * 40)
    print(f"   Overall Success Rate: {task_success['overall']:.2%}")
    print("\n   Per-Intent Success Rates:")
    for intent, stats in sorted(task_success['per_intent'].items()):
        print(f"     {intent:25s} {stats['success_rate']:.2%} ({stats['success_count']}/{stats['total_count']})")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Prepare latency stats for report
    latency_stats = {
        'asr': {
            'avg_ms': avg_asr_latency,
            'min_ms': min(asr_latencies) * 1000 if asr_latencies else 0,
            'max_ms': max(asr_latencies) * 1000 if asr_latencies else 0
        },
        'nlu': {
            'avg_ms': avg_nlu_latency,
            'min_ms': min(nlu_latencies) * 1000 if nlu_latencies else 0,
            'max_ms': max(nlu_latencies) * 1000 if nlu_latencies else 0
        },
        'nlg': {
            'avg_ms': avg_nlg_latency,
            'min_ms': min(nlg_latencies) * 1000 if nlg_latencies else 0,
            'max_ms': max(nlg_latencies) * 1000 if nlg_latencies else 0
        },
        'total': {
            'avg_ms': avg_total_latency,
            'min_ms': min_total_latency,
            'max_ms': max_total_latency
        }
    }

    report = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'audio_dir': audio_dir,
            'commands_file': commands_file,
            'total_samples': len(results),
            'nlu_mode': 'hybrid' if use_hybrid else 'regex'
        },
        'metrics': {
            'asr': {
                'wer': avg_wer,
                'cer': avg_cer
            },
            'intent_classification': intent_metrics,
            'slot_extraction': {
                'average_f1': avg_slot_f1
            },
            'end_to_end': {
                'semantic_error_rate': ser,
                'sentence_accuracy': sentence_acc
            },
            'latency': latency_stats,
            'task_success': task_success
        },
        'detailed_results': results
    }

    # Save JSON report
    json_path = os.path.join(output_dir, f'evaluation_report_{timestamp}.json')
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nDetailed report saved: {json_path}")

    # Generate markdown report
    md_path = os.path.join(output_dir, f'evaluation_report_{timestamp}.md')
    generate_markdown_report(report, md_path)
    print(f"Markdown report saved: {md_path}")

    return report


def generate_markdown_report(report: Dict, output_path: str):
    """Generate a formatted markdown report"""
    metrics = report['metrics']

    md = f"""# Voice Assistant Evaluation Report

**Generated:** {report['metadata']['timestamp']}
**Total Samples:** {report['metadata']['total_samples']}

---

## 1. ASR Performance

| Metric | Value |
|--------|-------|
| Word Error Rate (WER) | {metrics['asr']['wer']:.2%} |
| Character Error Rate (CER) | {metrics['asr']['cer']:.2%} |

---

## 2. Intent Classification

| Metric | Value |
|--------|-------|
| Accuracy | {metrics['intent_classification']['accuracy']:.2%} |
| Macro Precision | {metrics['intent_classification']['macro_precision']:.2%} |
| Macro Recall | {metrics['intent_classification']['macro_recall']:.2%} |
| Macro F1 | {metrics['intent_classification']['macro_f1']:.2%} |

### Per-Class Performance

| Intent | Precision | Recall | F1 | Support |
|--------|-----------|--------|-----|---------|
"""

    for intent, m in metrics['intent_classification']['per_class'].items():
        md += f"| {intent} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} | {m['support']} |\n"

    md += f"""
---

## 3. Slot/Entity Extraction

| Metric | Value |
|--------|-------|
| Average Slot F1 | {metrics['slot_extraction']['average_f1']:.2%} |

---

## 4. End-to-End Performance

| Metric | Value |
|--------|-------|
| Semantic Error Rate (SER) | {metrics['end_to_end']['semantic_error_rate']:.2%} |
| Sentence Accuracy | {metrics['end_to_end']['sentence_accuracy']:.2%} |

---

## 5. Latency Metrics

| Component | Avg (ms) | Min (ms) | Max (ms) |
|-----------|----------|----------|----------|
| ASR | {metrics['latency']['asr']['avg_ms']:.0f} | {metrics['latency']['asr']['min_ms']:.0f} | {metrics['latency']['asr']['max_ms']:.0f} |
| NLU | {metrics['latency']['nlu']['avg_ms']:.0f} | {metrics['latency']['nlu']['min_ms']:.0f} | {metrics['latency']['nlu']['max_ms']:.0f} |
| NLG | {metrics['latency']['nlg']['avg_ms']:.2f} | {metrics['latency']['nlg']['min_ms']:.2f} | {metrics['latency']['nlg']['max_ms']:.2f} |
| Total | {metrics['latency']['total']['avg_ms']:.0f} | {metrics['latency']['total']['min_ms']:.0f} | {metrics['latency']['total']['max_ms']:.0f} |

---

## 6. Confusion Matrix

```
"""

    # Generate confusion matrix for markdown
    labels = sorted(metrics['intent_classification']['confusion_matrix'].keys())
    cm = metrics['intent_classification']['confusion_matrix']

    # Abbreviations
    abbrev = {
        'create_appointment': 'create',
        'delete_appointment': 'delete',
        'get_appointment': 'get',
        'update_appointment': 'update',
        'weather_query': 'weather',
        'unknown': 'unk'
    }

    short_labels = [abbrev.get(l, l[:6]) for l in labels]
    cell_width = max(6, max(len(l) for l in short_labels))

    # Header
    md += " " * (cell_width + 1) + " ".join(f"{l:^{cell_width}}" for l in short_labels) + "\n"

    # Data rows
    for i, true_label in enumerate(labels):
        row_data = []
        for pred_label in labels:
            count = cm.get(true_label, {}).get(pred_label, 0)
            row_data.append(f"{count:^{cell_width}}")
        md += f"{short_labels[i]:>{cell_width}} " + " ".join(row_data) + "\n"

    md += """```

*Rows = True Labels, Columns = Predicted Labels*

---

## 7. Task Success Rate

**Overall Success Rate:** """

    md += f"{metrics['task_success']['overall']:.2%}\n\n"
    md += "### Per-Intent Success Rates\n\n"
    md += "| Intent | Success Rate | Successful | Total |\n"
    md += "|--------|--------------|------------|-------|\n"

    for intent, stats in sorted(metrics['task_success']['per_intent'].items()):
        md += f"| {intent} | {stats['success_rate']:.2%} | {stats['success_count']} | {stats['total_count']} |\n"

    md += """
---

## Methodology

This evaluation uses state-of-the-art metrics for Spoken Language Understanding (SLU):

1. **ASR Metrics:**
   - **WER (Word Error Rate):** Measures transcription accuracy at word level
   - **CER (Character Error Rate):** Measures transcription accuracy at character level

2. **Intent Classification:**
   - Standard classification metrics (Precision, Recall, F1)
   - Macro-averaged across all intent classes

3. **Slot/Entity Extraction:**
   - **Slot F1:** Measures entity extraction accuracy with exact match

4. **End-to-End Metrics:**
   - **SER (Semantic Error Rate):** Percentage of utterances with any semantic error
   - **Sentence Accuracy:** Percentage of utterances with both correct intent AND all slots correct

5. **Latency Metrics:**
   - **ASR Latency:** Time to transcribe audio to text
   - **NLU Latency:** Time to parse intent and entities from text
   - **NLG Latency:** Time to generate natural language response
   - **Total Latency:** End-to-end processing time per utterance

6. **Confusion Matrix:**
   - Shows distribution of predictions vs. true labels
   - Helps identify systematic classification errors

7. **Task Success Rate:**
   - Measures whether the user's task would be completed correctly
   - Requires both correct intent AND all slots correct
   - Broken down by intent type for detailed analysis

---

*Report generated by Voice Assistant Evaluation System*
"""

    with open(output_path, 'w') as f:
        f.write(md)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Evaluate voice assistant')
    parser.add_argument('--audio-dir', '-d', default='data/Shibin',
                        help='Directory containing audio files')
    parser.add_argument('--commands-file', '-c', default='tests/voice_commands_simple.txt',
                        help='Path to expected commands file')
    parser.add_argument('--output-dir', '-o', default='tests/evaluation',
                        help='Output directory for reports')
    parser.add_argument('--hybrid', action='store_true',
                        help='Use hybrid NLU with GLiNER (default: use regex NLU)')

    args = parser.parse_args()

    evaluate(args.audio_dir, args.commands_file, args.output_dir, use_hybrid=args.hybrid)
