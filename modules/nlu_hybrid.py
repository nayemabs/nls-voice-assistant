"""
Hybrid NLU Module with GLiNER Entity Extraction

This module combines:
1. Regex-based intent detection (fast, reliable)
2. GLiNER for zero-shot entity extraction (ML-based, generalizes well)
3. Fallback to regex patterns when GLiNER unavailable

GLiNER is a small, efficient model that extracts entities based on
labels you provide - no training data needed.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Silence tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Import the base NLU module for fallback
from modules.nlu import NLUModule

# Try to import GLiNER and related libraries
GLINER_AVAILABLE = False
SPACY_AVAILABLE = False
RAPIDFUZZ_AVAILABLE = False

try:
    from gliner import GLiNER
    GLINER_AVAILABLE = True
except ImportError:
    print("GLiNER not available. Install with: pip install gliner")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    print("spaCy not available. Install with: pip install spacy")

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    print("RapidFuzz not available. Install with: pip install rapidfuzz")


class HybridNLUModule(NLUModule):
    """
    Hybrid NLU that combines regex intent detection with GLiNER entity extraction.

    Falls back to regex-based entity extraction if GLiNER is not available.
    """

    def __init__(self, use_gliner: bool = True, gliner_model: str = "urchade/gliner_medium-v2.1"):
        """
        Initialize the hybrid NLU module.

        Args:
            use_gliner: Whether to use GLiNER for entity extraction
            gliner_model: GLiNER model to use (default: medium model for better accuracy)
                         Options: gliner_small-v2.1 (fast), gliner_medium-v2.1 (balanced),
                                  gliner_large-v2.1 (best quality, slower)
        """
        # Initialize base NLU (regex patterns)
        super().__init__()

        self.use_gliner = use_gliner and GLINER_AVAILABLE
        self.gliner_model = None
        self.spacy_nlp = None

        # Known entities for fuzzy matching (includes German spellings)
        self.known_cities = {
            # English names
            'marburg', 'frankfurt', 'berlin', 'munich', 'hamburg', 'cologne',
            'stuttgart', 'dresden', 'leipzig', 'dusseldorf', 'bonn', 'hannover',
            'hanover', 'bremen', 'essen', 'nuremberg', 'dortmund', 'duisburg',
            'bochum', 'wuppertal', 'bielefeld', 'munster', 'karlsruhe', 'mannheim',
            # German spellings
            'münchen', 'munchen', 'köln', 'koln', 'düsseldorf', 'nürnberg', 'nurnberg',
            # More German cities
            'giessen', 'gießen', 'kassel', 'darmstadt', 'wiesbaden', 'mainz',
            'heidelberg', 'freiburg', 'augsburg', 'würzburg', 'wurzburg',
            'aachen', 'kiel', 'rostock', 'potsdam', 'chemnitz', 'halle'
        }

        # Map German city names to English equivalents for normalization
        self.german_city_map = {
            'münchen': 'Munich', 'munchen': 'Munich',
            'köln': 'Cologne', 'koln': 'Cologne',
            'düsseldorf': 'Dusseldorf',
            'nürnberg': 'Nuremberg', 'nurnberg': 'Nuremberg',
            'gießen': 'Giessen', 'giessen': 'Giessen',
            'würzburg': 'Wurzburg', 'wurzburg': 'Wurzburg',
        }

        # Entity labels for GLiNER
        self.entity_labels = {
            'weather_query': ['city', 'location', 'day', 'date', 'weather_condition'],
            'create_appointment': ['meeting_title', 'time', 'day', 'date', 'location', 'room'],
            'update_appointment': ['meeting_title', 'time', 'day', 'date', 'location', 'room'],
            'delete_appointment': ['meeting_title', 'day', 'date'],
            'get_appointment': ['day', 'date'],
            # Conversational intents don't need entity extraction
            'greeting': [],
            'thanks': [],
            'acknowledgment': [],
            'goodbye': [],
            'help': [],
        }

        # Load models
        if self.use_gliner:
            self._load_gliner(gliner_model)

        if SPACY_AVAILABLE:
            self._load_spacy()

    def _load_gliner(self, model_name: str):
        """Load GLiNER model"""
        try:
            print(f"Loading GLiNER model ({model_name})...")
            self.gliner_model = GLiNER.from_pretrained(model_name)
            print("GLiNER loaded successfully")
        except Exception as e:
            print(f"Failed to load GLiNER: {e}")
            self.use_gliner = False

    def _load_spacy(self):
        """Load spaCy model for text processing"""
        try:
            self.spacy_nlp = spacy.load("en_core_web_sm")
            print("spaCy loaded successfully")
        except Exception as e:
            print(f"spaCy model not found: {e}")
            print("Install with: python -m spacy download en_core_web_sm")

    def understand(self, text: str) -> Dict:
        """
        Analyze text and extract intent and entities.

        Uses regex for intent detection and GLiNER for entity extraction.
        Falls back to regex entities if GLiNER unavailable.
        Implements joint intent-slot learning by using intent to guide entity extraction.

        Args:
            text: User input text

        Returns:
            dict: {'intent': str, 'entities': dict, 'confidence': float}
        """
        # Clean speech fillers
        cleaned_text = self._clean_fillers(text)
        text_lower = cleaned_text.lower()

        # Detect intent using regex (fast and reliable)
        intent = self._detect_intent(text_lower)

        # Extract entities
        if self.use_gliner and self.gliner_model:
            entities = self._extract_entities_gliner(cleaned_text, intent)
        else:
            # Fallback to regex-based extraction
            entities = self._extract_entities(text_lower, intent, original_text=cleaned_text)

        # Apply intent-guided entity validation (joint intent-slot interaction)
        entities = self._validate_entities_by_intent(entities, intent, text_lower)

        # Post-process entities (fuzzy matching for places, etc.)
        entities = self._post_process_entities(entities, text_lower)

        # Calculate confidence based on entity extraction quality
        confidence = self._calculate_confidence(intent, entities)

        return {
            'intent': intent,
            'entities': entities,
            'confidence': confidence
        }

    def _validate_entities_by_intent(self, entities: Dict, intent: str, text_lower: str) -> Dict:
        """
        Validate and adjust entities based on detected intent.
        Implements joint intent-slot interaction for better predictions.

        Args:
            entities: Extracted entities
            intent: Detected intent
            text_lower: Lowercase input text

        Returns:
            Validated and adjusted entities
        """
        validated = entities.copy()

        if intent == 'weather_query':
            # For weather queries, ensure place is valid and condition is meaningful
            if 'condition' in validated:
                condition_lower = validated['condition'].lower()
                # Remove generic weather words that aren't conditions
                invalid_conditions = {'weather', 'like', 'be', 'forecast', 'outside', 'temperature'}
                if condition_lower in invalid_conditions:
                    del validated['condition']
                # Check if condition is actually a city (GLiNER CPU misclassification fix)
                elif condition_lower in self.known_cities:
                    # Move condition to place
                    if 'place' not in validated:
                        validated['place'] = self._normalize_place(validated['condition']) or validated['condition'].title()
                    del validated['condition']

            # If no place extracted but text contains "there", it's a reference
            if 'place' not in validated and 'there' in text_lower:
                validated['temporal_reference'] = True

        elif intent in ['create_appointment', 'update_appointment']:
            # For appointment creation/update, validate title isn't spurious
            if 'title' in validated:
                title_lower = validated['title'].lower()
                spurious = {'meeting', 'appointment', 'event', 'the', 'a', 'an', 'my'}
                if title_lower in spurious:
                    del validated['title']
                # Remove titles that are just time references
                if re.match(r'^\d+\s*(am|pm|a\.m\.|p\.m\.)?$', title_lower):
                    del validated['title']

        elif intent == 'delete_appointment':
            # For delete, check for "previously created" reference
            if 'previously' in text_lower or 'last' in text_lower:
                validated['previous_reference'] = True

        elif intent == 'get_appointment':
            # For queries, check for "next" appointment request
            if 'next' in text_lower:
                validated['next'] = True

        return validated

    def _calculate_confidence(self, intent: str, entities: Dict) -> float:
        """
        Calculate confidence score based on intent and entity extraction quality.

        Args:
            intent: Detected intent
            entities: Extracted entities

        Returns:
            Confidence score between 0 and 1
        """
        base_confidence = 0.85 if self.use_gliner else 0.75

        # Boost confidence if we have expected entities for the intent
        expected_entities = {
            'weather_query': ['place', 'day'],
            'create_appointment': ['title', 'time', 'day'],
            'update_appointment': ['title', 'time', 'day', 'location'],
            'delete_appointment': ['title', 'day'],
            'get_appointment': ['day'],
            # Conversational intents don't need entities - high confidence by default
            'greeting': [],
            'thanks': [],
            'acknowledgment': [],
            'goodbye': [],
            'help': [],
        }

        if intent in expected_entities:
            expected = expected_entities[intent]
            found = sum(1 for e in expected if e in entities)
            entity_ratio = found / len(expected) if expected else 0
            # Boost confidence based on entity coverage
            confidence = base_confidence + (0.1 * entity_ratio)
        else:
            confidence = base_confidence

        # Cap at 0.95 to avoid overconfidence
        return min(confidence, 0.95)

    def understand_nbest(self, hypotheses: List[Tuple[str, float]]) -> Dict:
        """
        Process N-best ASR hypotheses and return the best NLU interpretation.
        This reduces ASR error propagation by selecting the hypothesis that
        produces the most coherent NLU output.

        Args:
            hypotheses: List of (text, asr_confidence) tuples from ASR

        Returns:
            Best NLU result with combined ASR+NLU confidence
        """
        if not hypotheses:
            return {'intent': 'unknown', 'entities': {}, 'confidence': 0.0}

        best_result = None
        best_score = -1

        for text, asr_confidence in hypotheses:
            # Get NLU interpretation for this hypothesis
            result = self.understand(text)

            # Calculate combined score
            nlu_confidence = result['confidence']
            intent = result['intent']
            entities = result['entities']

            # Score based on:
            # 1. ASR confidence
            # 2. NLU confidence
            # 3. Intent validity (known intent > unknown)
            # 4. Entity coverage
            intent_bonus = 0.1 if intent != 'unknown' else 0
            entity_bonus = 0.05 * min(len(entities), 3)  # Max 0.15 bonus for entities

            combined_score = (asr_confidence * 0.4) + (nlu_confidence * 0.4) + intent_bonus + entity_bonus

            if combined_score > best_score:
                best_score = combined_score
                best_result = result
                best_result['asr_confidence'] = asr_confidence
                best_result['combined_confidence'] = combined_score
                best_result['selected_text'] = text

        return best_result

    def _extract_entities_gliner(self, text: str, intent: str) -> Dict:
        """
        Extract entities using GLiNER zero-shot NER.

        Args:
            text: Input text
            intent: Detected intent

        Returns:
            dict: Extracted entities
        """
        entities = {}

        # Get labels for this intent
        labels = self.entity_labels.get(intent, ['city', 'location', 'time', 'day', 'date'])

        try:
            # Run GLiNER prediction with optimized threshold
            # Lower threshold (0.25) to catch more entities, then filter by confidence
            predictions = self.gliner_model.predict_entities(text, labels, threshold=0.25)

            # Sort predictions by confidence for better entity selection
            predictions = sorted(predictions, key=lambda x: x.get('score', 0), reverse=True)

            # Track entity confidence for potential multi-hypothesis selection
            entity_candidates = {}

            # Map GLiNER predictions to our entity schema
            for pred in predictions:
                label = pred['label']
                value = pred['text'].strip()
                confidence = pred.get('score', 0.5)

                if label in ['city', 'location']:
                    # Validate and normalize place names
                    normalized = self._normalize_place(value)
                    if normalized:
                        # Only update if higher confidence or not yet set
                        if 'place' not in entities or confidence > entity_candidates.get('place_conf', 0):
                            entities['place'] = normalized
                            entity_candidates['place_conf'] = confidence

                elif label == 'meeting_title':
                    # Clean up title - remove trailing time/date phrases that GLiNER might capture
                    cleaned_title = self._clean_title(value)
                    if cleaned_title:
                        # Prefer higher confidence titles
                        if 'title' not in entities or confidence > entity_candidates.get('title_conf', 0):
                            entities['title'] = cleaned_title
                            entity_candidates['title_conf'] = confidence

                elif label == 'time':
                    # Parse time expressions
                    parsed_time = self._parse_time_expression(value)
                    if parsed_time:
                        if 'time' not in entities or confidence > entity_candidates.get('time_conf', 0):
                            entities['time'] = parsed_time
                            entity_candidates['time_conf'] = confidence

                elif label in ['day', 'date']:
                    # Normalize day/date
                    normalized_day = self._normalize_day(value)
                    if normalized_day:
                        if 'day' not in entities or confidence > entity_candidates.get('day_conf', 0):
                            entities['day'] = normalized_day
                            entity_candidates['day_conf'] = confidence

                elif label == 'room':
                    if 'location' not in entities or confidence > entity_candidates.get('loc_conf', 0):
                        entities['location'] = value
                        entity_candidates['loc_conf'] = confidence

                elif label == 'weather_condition':
                    # Filter out "weather" itself - it's not a condition
                    condition = value.lower().strip()
                    invalid_words = {'weather', 'forecast', 'temperature', 'outside', 'like', 'be'}
                    # Check if any invalid word is IN the condition (not just exact match)
                    is_invalid = any(invalid in condition for invalid in invalid_words)

                    # CRITICAL: Check if condition is actually a city name (GLiNER CPU misclassification)
                    # This prevents cities like "marburg", "frankfurt" from being labeled as conditions
                    is_city = condition in self.known_cities or any(
                        city in condition for city in self.known_cities
                    )

                    if not is_invalid and not is_city and condition:
                        if 'condition' not in entities or confidence > entity_candidates.get('cond_conf', 0):
                            entities['condition'] = condition
                            entity_candidates['cond_conf'] = confidence

                        # If it was a city misclassified as condition, extract it as place instead
                    if is_city and 'place' not in entities:
                        normalized = self._normalize_place(value)
                        if normalized:
                            entities['place'] = normalized
                            entity_candidates['place_conf'] = confidence

        except Exception as e:
            print(f"GLiNER extraction error: {e}")
            # Fall back to regex
            return self._extract_entities(text.lower(), intent, original_text=text)

        # Always extract datetime using regex (more reliable for time parsing)
        date_time = self._extract_datetime(text.lower())
        if date_time:
            if 'time' not in entities and date_time.get('time'):
                entities['time'] = date_time['time']
            if 'day' not in entities and date_time.get('date'):
                entities['day'] = date_time['date']

        # Extract day using regex if not found
        if 'day' not in entities:
            day = self._extract_day(text.lower())
            if day:
                entities['day'] = day

        # Fallback: extract title using regex if GLiNER didn't find it
        # This is important for patterns like "named X", "called X" that GLiNER may miss
        if 'title' not in entities and intent in ['create_appointment', 'update_appointment', 'delete_appointment', 'unknown']:
            title = self._extract_title(text)
            if title:
                # Filter out spurious titles
                spurious_titles = {
                    'meeting', 'appointment', 'event', 'my', 'the', 'a', 'an',
                    'book meeting', 'by', 'previously', 'previously created', 'created'
                }
                action_prefixes = ('create ', 'add ', 'schedule ', 'book ', 'make ', 'set ',
                                   'delete ', 'remove ', 'cancel ', 'update ', 'change ', 'modify ')
                if title.lower() not in spurious_titles and not title.lower().startswith(action_prefixes):
                    entities['title'] = title
                    # If location was extracted but it's the same as title, remove it
                    # (GLiNER sometimes misclassifies titles as locations)
                    if entities.get('location', '').lower() == title.lower():
                        del entities['location']

        # Filter out spurious titles that GLiNER might have extracted
        if entities.get('title'):
            title_lower = entities['title'].lower().strip()
            spurious_titles = {
                'meeting', 'appointment', 'event', 'my', 'the', 'a', 'an',
                'book meeting', 'by', 'previously', 'previously created', 'created'
            }
            # Also filter titles that start with action verbs (e.g., "create an appointment")
            action_prefixes = ('create ', 'add ', 'schedule ', 'book ', 'make ', 'set ',
                               'delete ', 'remove ', 'cancel ', 'update ', 'change ', 'modify ')
            if title_lower in spurious_titles or title_lower.startswith(action_prefixes):
                del entities['title']

        # Add temporal reference
        entities['temporal_reference'] = self._extract_temporal_reference(text.lower())

        return entities

    def _normalize_place(self, place: str) -> Optional[str]:
        """
        Normalize and validate place names using fuzzy matching.
        Handles both English and German city names.

        Args:
            place: Raw place string

        Returns:
            Normalized place name or None
        """
        if not place:
            return None

        place_lower = place.lower().strip()

        # Filter out invalid place names that are clearly not cities
        invalid_places = {
            'the', 'a', 'an', 'in', 'at', 'on', 'for', 'to', 'my', 'your',
            'me', 'you', 'it', 'this', 'that', 'today', 'tomorrow', 'there',
            'here', 'weather', 'forecast', 'appointment', 'meeting', 'time',
            'date', 'day', 'week', 'month', 'year', 'morning', 'afternoon',
            'evening', 'night', 'noon', 'midnight', 'will', 'what', 'when',
            'where', 'how', 'who', 'why', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'done',
            'morgan',  # Common ASR error for "tomorrow" in German contexts
            # Keywords that GLiNER might misclassify as locations
            'titled', 'called', 'named', 'scheduled', 'created', 'added',
        }
        if place_lower in invalid_places:
            return None

        # Check German→English mapping first
        if place_lower in self.german_city_map:
            return self.german_city_map[place_lower]

        # Direct match
        if place_lower in self.known_cities:
            return place_lower.title()

        # Fuzzy matching with multiple scorers for robustness
        if RAPIDFUZZ_AVAILABLE:
            # Try exact ratio first
            match = process.extractOne(
                place_lower,
                self.known_cities,
                scorer=fuzz.ratio,
                score_cutoff=75  # Lowered for more matches
            )
            if match:
                matched_city = match[0]
                # Apply German→English mapping if needed
                if matched_city in self.german_city_map:
                    return self.german_city_map[matched_city]
                return matched_city.title()

            # Try partial ratio for substring matches
            match = process.extractOne(
                place_lower,
                self.known_cities,
                scorer=fuzz.partial_ratio,
                score_cutoff=85
            )
            if match:
                matched_city = match[0]
                if matched_city in self.german_city_map:
                    return self.german_city_map[matched_city]
                return matched_city.title()

        # If it looks like a valid place name (not a common word)
        if len(place) > 2 and not any(c.isdigit() for c in place):
            # Check it's not a day of the week
            days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
            if place_lower not in days:
                return place.title()

        return None

    def _normalize_day(self, day_str: str) -> Optional[str]:
        """
        Normalize day expressions to standard format.
        Handles both English and German day names.

        Args:
            day_str: Raw day string

        Returns:
            Normalized day string (in English)
        """
        day_lower = day_str.lower().strip()

        # Standard days (English and German)
        days = {
            # English
            'today': 'today',
            'tomorrow': 'tomorrow',
            'monday': 'monday', 'mon': 'monday',
            'tuesday': 'tuesday', 'tue': 'tuesday', 'tues': 'tuesday',
            'wednesday': 'wednesday', 'wed': 'wednesday',
            'thursday': 'thursday', 'thu': 'thursday', 'thurs': 'thursday',
            'friday': 'friday', 'fri': 'friday',
            'saturday': 'saturday', 'sat': 'saturday',
            'sunday': 'sunday', 'sun': 'sunday',
            # German day names → English
            'heute': 'today',
            'morgen': 'tomorrow',
            'übermorgen': 'day after tomorrow', 'ubermorgen': 'day after tomorrow',
            'montag': 'monday',
            'dienstag': 'tuesday',
            'mittwoch': 'wednesday',
            'donnerstag': 'thursday',
            'freitag': 'friday',
            'samstag': 'saturday',
            'sonntag': 'sunday',
            'wochenende': 'weekend',
        }

        if day_lower in days:
            return days[day_lower]

        # Check for date expressions (English months)
        if any(month in day_lower for month in ['january', 'february', 'march', 'april',
                                                  'may', 'june', 'july', 'august',
                                                  'september', 'october', 'november', 'december']):
            return day_str.lower()

        # Check for German months
        german_months = {
            'januar': 'january', 'februar': 'february', 'märz': 'march', 'marz': 'march',
            'april': 'april', 'mai': 'may', 'juni': 'june', 'juli': 'july',
            'august': 'august', 'september': 'september', 'oktober': 'october',
            'november': 'november', 'dezember': 'december'
        }
        for de_month, en_month in german_months.items():
            if de_month in day_lower:
                return day_str.lower().replace(de_month, en_month)

        return None

    def _parse_time_expression(self, time_str: str) -> Optional[str]:
        """
        Parse time expressions to standard format.

        Args:
            time_str: Raw time string

        Returns:
            Standardized time string (e.g., "10:00 am")
        """
        time_lower = time_str.lower().strip()

        # Handle special times
        if 'noon' in time_lower or 'midday' in time_lower:
            return '12:00'
        if 'midnight' in time_lower:
            return '00:00'

        # Normalize period to colon for time separator (2.30 → 2:30)
        time_normalized = re.sub(r'(\d{1,2})\.(\d{2})', r'\1:\2', time_lower)

        # Parse "X am/pm" or "X:XX am/pm" or "X.XX am/pm"
        match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?', time_normalized)
        if match:
            hour = match.group(1)
            minutes = match.group(2) or '00'
            ampm = match.group(3) or ''
            ampm = ampm.replace('.', '')

            return f"{hour}:{minutes} {ampm}".strip()

        return None

    def _clean_title(self, title: str) -> Optional[str]:
        """
        Clean up extracted title by removing time/date phrases that GLiNER might capture.

        Args:
            title: Raw title string from GLiNER

        Returns:
            Cleaned title or None if invalid
        """
        if not title:
            return None

        cleaned = title.strip()

        # Remove trailing time/date phrases
        # "Team Meeting and the time is 3.30 a.m." → "Team Meeting"
        patterns_to_remove = [
            r'\s+and\s+(?:the\s+)?(?:time|date)\s+(?:is|would\s+be|will\s+be|should\s+be)\s+.*$',
            r'\s+at\s+\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)?.*$',
            r'\s+for\s+(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?(?:\s+of\s+\w+)?.*$',
            r'\s+on\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow).*$',
            r'\s+(?:time|date)\s+(?:is|would\s+be)\s+.*$',
        ]

        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Remove trailing words that shouldn't be in titles
        cleaned = re.sub(r'\s+(?:and|at|for|on|the|time|date|is)\s*$', '', cleaned, flags=re.IGNORECASE)

        # Clean up any remaining punctuation at the end
        cleaned = cleaned.strip().rstrip('.,;:')

        # Filter out invalid titles
        invalid_titles = {
            'meeting', 'appointment', 'event', 'my', 'the', 'a', 'an',
            'time', 'date', 'title', 'it', 'this', 'that'
        }
        if cleaned.lower() in invalid_titles:
            return None

        return cleaned if cleaned and len(cleaned) > 1 else None

    def _post_process_entities(self, entities: Dict, text_lower: str) -> Dict:
        """
        Post-process entities for consistency and additional extractions.

        Args:
            entities: Extracted entities
            text_lower: Lowercase input text

        Returns:
            Post-processed entities
        """
        # Extract 'next' for appointment queries
        if 'next' in text_lower and 'appointment' in text_lower:
            entities['next'] = True

        # Handle "there" reference
        if 'there' in text_lower:
            entities['temporal_reference'] = True

        return entities


# Factory function to get the best available NLU
def get_nlu_module(prefer_hybrid: bool = True) -> NLUModule:
    """
    Get the best available NLU module.

    Args:
        prefer_hybrid: Whether to prefer hybrid (GLiNER) NLU

    Returns:
        NLU module instance
    """
    if prefer_hybrid and GLINER_AVAILABLE:
        try:
            return HybridNLUModule(use_gliner=True)
        except Exception as e:
            print(f"Failed to initialize HybridNLU: {e}")

    # Fallback to regex-based NLU
    return NLUModule()


if __name__ == "__main__":
    # Test the hybrid NLU
    print("Testing Hybrid NLU Module\n")
    print("=" * 60)

    # Try to use hybrid, fallback to regex
    nlu = get_nlu_module(prefer_hybrid=True)

    test_cases = [
        "What's the weather in Marburg tomorrow?",
        "Add an appointment titled Team Meeting for Monday at 3 PM",
        "The time would be group meeting and the time would be 4 pm",
        "Delete my appointment tomorrow",
        "Will it rain in Frankfurt on Friday?",
        "Schedule a meeting called Sprint Planning for Tuesday at 10 AM",
        "What are my appointments today?",
    ]

    for text in test_cases:
        print(f"\nInput: {text}")
        result = nlu.understand(text)
        print(f"  Intent: {result['intent']}")
        print(f"  Entities: {result['entities']}")
        print(f"  Confidence: {result['confidence']}")
