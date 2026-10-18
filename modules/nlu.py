"""
Natural Language Understanding (NLU) Module
Handles intent detection and entity extraction
"""

import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser


class NLUModule:
    """Natural Language Understanding for intent classification and slot filling"""

    def __init__(self):
        """Initialize NLU module with intent patterns"""
        # Speech fillers/disfluencies to strip from user input
        # These are common hesitation sounds and filler words
        self.speech_fillers = {
            # Hesitation sounds
            'um', 'umm', 'ummm', 'uh', 'uhh', 'uhhh', 'ah', 'ahh', 'ahhh',
            'er', 'err', 'errr', 'eh', 'ehh', 'hm', 'hmm', 'hmmm',
            # Filler words
            'like', 'you know', 'i mean', 'so', 'well', 'basically',
            'actually', 'literally', 'right', 'okay so', 'um like',
            # False starts and repairs (handled by patterns below)
        }

        # Patterns for more complex filler removal
        self.filler_patterns = [
            r'\b(?:um+|uh+|ah+|er+|eh+|hm+)\b',  # Hesitation sounds
            r'\b(?:like|you know|i mean)\s*,?\s*',  # Filler phrases
            r'^(?:so|well|okay so|right so)\s+',  # Sentence starters
            r'\s+(?:so|well)\s*$',  # Sentence enders
        ]

        # Define intent patterns with regex - more flexible patterns
        # IMPORTANT: Order matters! Delete/Update checked BEFORE Create to avoid "created" matching "create"
        # Includes both English and German patterns for bilingual support
        self.intent_patterns = {
            'weather_query': [
                # Direct weather questions (English)
                r'(?:what|how).*weather',
                r'weather.*(?:in|at|for|today|tomorrow|like)',
                r'\bweather\b',  # Just the word "weather" alone
                r'weather\s*[?]',  # "Weather?"
                r'weather\s+(?:report|forecast)',  # "Weather report/forecast"
                # Condition queries (English)
                r'(?:will|is|does)\s+it\s+(?:rain|snow|sunny|cloudy|foggy|windy|misty|clear)',
                r'(?:is|will)\s+it\s+(?:hot|cold|warm|nice|going\s+to\s+be)',
                r'(?:is|will)\s+(?:it|there)\s+(?:be\s+)?(?:rain|sunny|cloudy|clear|storm|thunder|fog)',
                r'going\s+(?:to\s+)?(?:rain|snow|be\s+(?:nice|sunny|cloudy|warm|cold))',
                # Temperature queries (English)
                r'temperature',
                r'(?:what|how).*(?:hot|cold|warm|nice)',
                r'(?:is|how)\s+(?:it\s+)?(?:hot|cold|warm)',
                # Forecast and outlook (English)
                r'(?:what|how).*(?:outside|forecast|outlook)',
                r'(?:what|how).*(?:look|looking)\b',
                r"what'?s?\s+(?:it\s+)?like\s+(?:in|outside)",
                # Possessive day formats (Friday's weather, tomorrow's forecast)
                r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow)'?s?\s+(?:weather|forecast|outlook|temperature)",
                # "Is the sky clear?" pattern
                r'(?:is|are)\s+(?:the\s+)?(?:sky|skies)\s+(?:clear|cloudy|overcast)',
                # Am I free patterns (weather context)
                r'(?:going|am\s+i\s+going)\s+outside',
                # Weather conditions as keywords (more specific)
                r'\b(?:rain|snow|sunny|cloudy|storm|fog|wind|mist|thunder|shower|foggy|windy|misty|clear|overcast)(?:y|ing|s)?\b',
                # ===== GERMAN WEATHER PATTERNS =====
                r'\bwetter\b',  # "Wetter" (weather)
                r'(?:wie|was)\s+ist\s+(?:das\s+)?wetter',  # "Wie ist das Wetter" (How is the weather)
                r'wetter\s+(?:in|für|fur|morgen|heute)',  # "Wetter in/für/morgen/heute"
                r'\b(?:regen|regnet|schnee|schneit|sonnig|wolkig|kalt|warm|heiß|heiss)\b',  # German conditions
                r'(?:wird|ist)\s+es\s+(?:regnen|schneien|sonnig|warm|kalt)',  # "Wird es regnen"
                r'\btemperatur\b',  # "Temperatur"
                r'\bvorhersage\b',  # "Vorhersage" (forecast)
                r'\bdraußen\b|\bdraussen\b',  # "draußen" (outside)
            ],
            # DELETE must be checked BEFORE create (to avoid "created" matching "create")
            'delete_appointment': [
                r'\b(?:delete|delte|deleet|delet|remove|cancel|drop)\b.*(?:appointment|meeting|event)',
                # German delete patterns
                r'\b(?:löschen|loschen|entfernen|absagen|stornieren)\b.*(?:termin|besprechung|treffen)',
                r'\btermin\s+(?:löschen|loschen|absagen|entfernen)\b',
            ],
            'update_appointment': [
                r'\b(?:update|change|modify|edit|reschedule|move)\b.*(?:appointment|meeting|event)',
                r'\b(?:change|update)\b.*(?:time|date|location|place|title|name)',
                # German update patterns
                r'\b(?:ändern|andern|aktualisieren|verschieben)\b.*(?:termin|besprechung|treffen)',
                r'\btermin\s+(?:ändern|andern|verschieben)\b',
            ],
            # CREATE checked after delete/update - use word boundary to avoid "created" matching
            'create_appointment': [
                r'\b(?:add|create|schedule|make|set|book)\b.*(?:appointment|meeting|event)',
                r'\b(?:new|another)\b.*(?:appointment|meeting|event)',
                r'calendar.*appointment',
                # Polite request patterns
                r'(?:would|could|can)\s+you\s+(?:please\s+)?(?:mind\s+)?(?:add|create|schedule|book|make).*(?:appointment|meeting|event)',
                r'(?:i\s+)?(?:would|\'d)\s+like\s+to\s+(?:add|create|schedule|book|make).*(?:appointment|meeting|event)',
                # "adding an appointment" gerund form
                r'\badding\b.*(?:appointment|meeting|event)',
                # German create patterns
                r'\b(?:erstellen|hinzufügen|hinzufugen|anlegen|eintragen)\b.*(?:termin|besprechung|treffen)',
                r'\b(?:neuer?|einen?)\s+termin\b',  # "neuer Termin" or "einen Termin"
                r'\btermin\s+(?:erstellen|hinzufügen|hinzufugen|anlegen|eintragen)\b',
            ],
            # Query intent checked last (after action intents)
            'get_appointment': [
                r'(?:what|where|when|show|tell|list|check|view).*(?:appointment|meeting|event|calendar|schedule)',
                r'(?:my|the).*(?:appointment|meeting|event)',
                r'do\s+i\s+have.*(?:appointment|meeting|event)',
                # Calendar/schedule queries
                r"(?:what'?s?|show|check)\s+(?:on\s+)?(?:my\s+)?(?:calendar|schedule)",
                r'(?:my|the)\s+(?:calendar|schedule)',
                # "Coming up" patterns for next appointment queries
                r"(?:what'?s?|show)\s+coming\s+up",
                r'coming\s+up\s+next',
                r"(?:what'?s?|what\s+is)\s+(?:up\s+)?next",
                # "Free/busy" patterns
                r'(?:am\s+i|are\s+we)\s+(?:free|busy|available)',
                # This pattern is intentionally general - matches after create/update/delete are checked
                r'(?:appointment|meeting|event)',
                # German query patterns
                r'(?:was|wann|wo)\s+(?:ist|sind|habe)\s+(?:mein|meine)?\s*(?:termin|termine|besprechung)',
                r'\b(?:zeig|zeige|anzeigen)\b.*(?:termin|termine|kalender)',
                r'\bmeine?\s+(?:termin|termine|kalender|zeitplan)\b',
                r'\b(?:termin|termine|kalender|zeitplan)\b',  # Just German appointment/calendar words
                r'\bnächster?\s+termin\b|\bnachster?\s+termin\b',  # "nächster Termin"
            ],
            # ============================================================
            # Conversational/Social Intents (for natural dialogue flow)
            # ============================================================
            'greeting': [
                r'^(?:hi|hello|hey|howdy|good\s+(?:morning|afternoon|evening)|greetings)[\s!.,?]*$',
                r'^(?:hi|hello|hey)\s+(?:there|assistant|claude)[\s!.,?]*$',
                # German greetings
                r'^(?:hallo|guten\s+(?:tag|morgen|abend)|servus|moin)[\s!.,?]*$',
            ],
            'thanks': [
                r'^(?:thanks?(?:\s+you)?|thank\s+you(?:\s+(?:very\s+)?much)?|thx|cheers|appreciate\s+it)[\s!.,?]*$',
                r'^(?:thanks?|thank\s+you)\s+(?:a\s+lot|so\s+much)[\s!.,?]*$',
                # German thanks
                r'^(?:danke(?:\s+(?:schön|sehr))?|vielen\s+dank)[\s!.,?]*$',
            ],
            'acknowledgment': [
                r'^(?:ok(?:ay)?|alright|all\s+right|got\s+it|understood|i\s+see|sure|great|good|nice|perfect|cool|fine)[\s!.,?]*$',
                r'^(?:sounds?\s+good|that\'?s?\s+(?:good|great|fine|perfect))[\s!.,?]*$',
                r'^(?:yes|yeah|yep|yup|no|nope)[\s!.,?]*$',
                # German acknowledgments
                r'^(?:gut|alles\s+klar|verstanden|in\s+ordnung|ja|nein)[\s!.,?]*$',
            ],
            'goodbye': [
                r'^(?:bye|goodbye|good\s*bye|see\s+(?:you|ya)|later|take\s+care|have\s+a\s+(?:good|nice)\s+(?:day|one)|ciao)[\s!.,?]*$',
                r'^(?:bye\s+bye|bye\s+for\s+now)[\s!.,?]*$',
                # German goodbyes
                r'^(?:tschüss|tschuss|auf\s+wiedersehen|bis\s+(?:bald|später|spater))[\s!.,?]*$',
            ],
            'help': [
                r'^(?:help|what\s+can\s+you\s+do|how\s+(?:do\s+you|can\s+you)\s+help)[\s!.,?]*$',
                r'^(?:what\s+(?:are\s+)?(?:your\s+)?(?:capabilities|features|commands))[\s!.,?]*$',
                # German help
                r'^(?:hilfe|was\s+kannst\s+du)[\s!.,?]*$',
            ],
        }

        # Day patterns for temporal understanding
        # Note: "day after tomorrow" must be checked BEFORE "tomorrow" to avoid partial match
        # Note: "next week" and "this weekend" checked early (multi-word patterns)
        # Includes both English and German patterns
        self.day_patterns = {
            'day after tomorrow': r'\b(?:day\s+after\s+tomorrow|übermorgen|ubermorgen)\b',
            'next week': r'\b(?:next\s+week|nächste\s+woche|nachste\s+woche)\b',
            'this week': r'\b(?:this\s+week|diese\s+woche)\b',
            'weekend': r'\b(?:this\s+)?(?:weekend|wochenende)\b',
            'today': r'\b(?:today|heute)\b',
            'tomorrow': r'\b(?:tomorrow|morgen)\b',
            'monday': r'\b(?:monday|mon|montag)\b',
            'tuesday': r'\b(?:tuesday|tue|dienstag)\b',
            'wednesday': r'\b(?:wednesday|wed|mittwoch)\b',
            'thursday': r'\b(?:thursday|thu|thurs|donnerstag)\b',
            'friday': r'\b(?:friday|fri|freitag)\b',
            'saturday': r'\b(?:saturday|sat|samstag)\b',
            'sunday': r'\b(?:sunday|sun|sonntag)\b',
        }

        # Weather condition patterns
        self.weather_conditions = [
            'rain', 'rainy', 'snow', 'snowy', 'sunny', 'cloudy', 'clear',
            'storm', 'stormy', 'mist', 'misty', 'fog', 'foggy',
            'thunderstorm', 'thunder', 'shower', 'showers',
            'wind', 'windy', 'hot', 'cold', 'warm', 'nice', 'humid'
        ]

    def _clean_fillers(self, text):
        """
        Remove speech fillers and disfluencies from text

        Args:
            text: User input text

        Returns:
            str: Cleaned text with fillers removed
        """
        cleaned = text

        # Apply filler patterns
        for pattern in self.filler_patterns:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)

        # Remove repeated words (common speech repair: "I I want" -> "I want")
        cleaned = re.sub(r'\b(\w+)\s+\1\b', r'\1', cleaned, flags=re.IGNORECASE)

        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def understand(self, text):
        """
        Analyze text and extract intent and entities

        Args:
            text: User input text

        Returns:
            dict: {
                'intent': str,
                'entities': dict,
                'confidence': float
            }
        """
        # Clean speech fillers from input
        cleaned_text = self._clean_fillers(text)
        text_lower = cleaned_text.lower()

        # Detect intent
        intent = self._detect_intent(text_lower)

        # Extract entities based on intent (pass both original and lowercase for better extraction)
        # Use cleaned text for entity extraction
        entities = self._extract_entities(text_lower, intent, original_text=cleaned_text)

        return {
            'intent': intent,
            'entities': entities,
            'confidence': 0.8  # Simplified confidence score
        }

    def _detect_intent(self, text):
        """
        Detect user intent from text

        Args:
            text: Preprocessed user input

        Returns:
            str: Detected intent
        """
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent

        return 'unknown'

    def _extract_entities(self, text, intent, original_text=None):
        """
        Extract entities based on intent

        Args:
            text: User input text (lowercase)
            intent: Detected intent
            original_text: Original text with capitalization preserved

        Returns:
            dict: Extracted entities
        """
        entities = {}

        # Use original text if provided, otherwise use the lowercase version
        text_for_extraction = original_text if original_text else text

        # Extract location/place
        place = self._extract_place(text, text_for_extraction)
        if place:
            entities['place'] = place

        # Extract day/date - check for multiple days (e.g., "today or tomorrow")
        days = self._extract_all_days(text)
        if days:
            if len(days) == 1:
                entities['day'] = days[0]
            else:
                entities['days'] = days  # Multiple days
                entities['day'] = days[0]  # Also set first day for backwards compatibility

        # Extract weather condition
        condition = self._extract_weather_condition(text)
        if condition:
            entities['condition'] = condition

        # Extract appointment details
        if intent in ['create_appointment', 'update_appointment', 'delete_appointment']:
            # Extract title - but skip for update if text contains "change the title"
            # because "title" is referring to what to change, not the actual title
            if intent == 'update_appointment' and 'change' in text.lower() and 'title' in text.lower():
                # Don't extract title for "change the title" phrases
                pass
            else:
                title = self._extract_title(text)
                if title:
                    entities['title'] = title

            # Extract location for appointment (not needed for delete)
            if intent != 'delete_appointment':
                location = self._extract_appointment_location(text)
                if location:
                    entities['location'] = location

        # Also extract title if text contains "title is/should be" (for multi-turn answers)
        # Also handle "title for X is Y" pattern
        # Also handle ASR mis-transcriptions where "title" → "time"
        title_pattern_found = (
            re.search(r'\btitle\s+(?:for\s+.+\s+)?(?:is|should\s+be|would\s+be|will\s+be)\b', text, re.IGNORECASE) or
            re.search(r'^(?:the\s+)?time\s*,', text, re.IGNORECASE) or  # "the time," mis-transcription
            re.search(r'(?:the\s+)?time\s+(?:would|will|should)\s+be\b', text, re.IGNORECASE)  # "time would be X"
        )
        if not entities.get('title') and title_pattern_found:
            title = self._extract_title(text)
            if title:
                entities['title'] = title

        # Always try to extract date/time - needed for multi-turn dialogue
        # where user might just say "10 AM" or "tomorrow"
        date_time = self._extract_datetime(text)
        if date_time:
            entities.update(date_time)

        # Also try to extract title from simple inputs for multi-turn
        # (e.g., user says "Team Meeting" when asked for title)
        if intent == 'unknown' and not entities.get('title'):
            # If it's a short phrase without action words, treat as potential title
            if len(text.split()) <= 5 and not any(w in text.lower() for w in ['what', 'where', 'when', 'how', 'will', 'is', 'are', 'do', 'can']):
                # Check if it looks like a title (not just a time or day)
                if not date_time and not days:
                    potential_title = text.strip().rstrip('.')
                    # Filter out time-like phrases (common ASR mis-transcriptions)
                    time_like = re.search(r'\b(a\.?m\.?|p\.?m\.?|o\'?clock)\b', potential_title, re.IGNORECASE)
                    if potential_title and len(potential_title) > 2 and not time_like:
                        entities['title'] = potential_title

        # Extract title from "X time is Y" or "X at Y" patterns (multi-turn answers)
        # e.g., "meeting time is 4 p.m." -> title is "meeting"
        if not entities.get('title') and date_time:
            title_match = re.search(r'^(\w+(?:\s+\w+)?)\s+(?:time\s+is|at\s+\d)', text, re.IGNORECASE)
            if title_match:
                potential_title = title_match.group(1).strip()
                # Filter out common words that shouldn't be titles
                if potential_title.lower() not in ['the', 'a', 'an', 'my', 'your', 'its', 'this', 'that', 'and', 'or', 'but']:
                    entities['title'] = potential_title

        # Extract title from "X is the title" pattern (e.g., "meeting is the title")
        if not entities.get('title'):
            title_match = re.search(r'^(\w+(?:\s+\w+)?)\s+is\s+the\s+title', text, re.IGNORECASE)
            if title_match:
                entities['title'] = title_match.group(1).strip()

        # Handle short phrases as potential titles for multi-turn (e.g., "team meeting")
        # Only if intent is 'unknown' (user answering a question), no title extracted yet
        if intent == 'unknown' and not entities.get('title'):
            words = text.split()
            if 1 <= len(words) <= 4:
                # Check if it doesn't contain query/action words
                query_words = {'what', 'where', 'when', 'how', 'will', 'is', 'are', 'do', 'does', 'can', 'have', 'has', 'any', 'show', 'list', 'check', 'tell', 'give', 'get'}
                action_words = {'make', 'create', 'schedule', 'book', 'add', 'delete', 'remove', 'cancel', 'update', 'change', 'modify'}
                if not any(w.lower() in query_words for w in words) and not any(w.lower() in action_words for w in words):
                    # Clean the phrase
                    potential_title = text.strip().rstrip('.').rstrip('?')
                    # Skip if it looks like a question (has question mark or starts with question word)
                    if '?' in text or text.lower().startswith(('what', 'where', 'when', 'how', 'will', 'is', 'are', 'do', 'does', 'can', 'could', 'would')):
                        pass  # Skip - this is a question, not a title
                    # Skip if it looks like just a day/time
                    elif not date_time and not days:
                        # Also skip if it looks like a time phrase (common ASR mis-transcriptions)
                        time_like_patterns = [
                            r'\b(a\.?m\.?|p\.?m\.?)\b',  # Contains AM/PM
                            r'\bo\'?clock\b',  # o'clock
                            r'^\s*(to|too|for|won|one|ate|eight|six|ten|nine|five|three|seven|eleven|twelve)\s+(p\.?m\.?|a\.?m\.?)\s*$',  # Mis-transcribed times
                            r'^\s*\d+\s*$',  # Just a number
                            r'^\s*\d+\.\d+\s*$',  # Digit.digit (e.g., 6.15)
                        ]
                        is_time_like = any(re.search(p, potential_title, re.IGNORECASE) for p in time_like_patterns)
                        # Reserved field names that shouldn't be treated as titles
                        field_names = {'time', 'date', 'location', 'place', 'title', 'name',
                                       'description', 'notes', 'event', 'appointment', 'meeting'}
                        if not is_time_like and len(potential_title) > 2 and potential_title.lower() not in field_names:
                            entities['title'] = potential_title

        # Extract temporal references
        entities['temporal_reference'] = self._extract_temporal_reference(text)

        # Extract 'next' for appointment queries (e.g., "next appointment")
        if intent == 'get_appointment':
            if re.search(r'\bnext\s+week\b', text, re.IGNORECASE):
                entities['next_week'] = True
            elif re.search(r'\bnext\b', text, re.IGNORECASE):
                entities['next'] = True

        return entities

    def _extract_place(self, text_lower, text_original):
        """Extract place/location from text

        Args:
            text_lower: Lowercase version of the text
            text_original: Original text with preserved capitalization
        """
        # Known German cities for validation
        known_cities = {
            'marburg', 'frankfurt', 'berlin', 'munich', 'hamburg', 'cologne',
            'stuttgart', 'dresden', 'leipzig', 'dusseldorf', 'bonn', 'hannover',
            'hanover', 'bremen', 'essen', 'nuremberg', 'dortmund', 'duisburg',
            'bochum', 'wuppertal', 'bielefeld', 'munster', 'karlsruhe', 'mannheim',
            'koln', 'nurnberg', 'munchen', 'duesseldorf'
        }

        # Common words that are NOT places
        stopwords = {
            'there', 'it', 'the', 'a', 'an', 'my', 'your', 'his', 'her', 'their',
            'this', 'that', 'these', 'those', 'will', 'be', 'like', 'what',
            'when', 'where', 'who', 'how', 'why', 'would', 'could', 'should',
            'can', 'may', 'might', 'must', 'shall', 'will', 'today', 'tomorrow',
            'yesterday', 'now', 'then', 'here', 'appointment', 'meeting',
            'event', 'place', 'location', 'time', 'day', 'week', 'month',
            # Pronouns (important: 'me' should not be a place!)
            'me', 'us', 'them', 'him', 'her', 'it', 'i', 'you', 'we', 'they',
            # Days of week (to avoid extracting these as places)
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            # Common greetings and conversational words
            'hello', 'hi', 'hey', 'bye', 'goodbye', 'thanks', 'thank', 'please',
            'yes', 'no', 'yeah', 'okay', 'ok', 'sure', 'good', 'great', 'nice',
            'well', 'just', 'only', 'also', 'too', 'very', 'really', 'actually',
            # Weather-related words that aren't places
            'rain', 'snow', 'sunny', 'cloudy', 'warm', 'cold', 'hot', 'outside',
            'weather', 'forecast', 'temperature', 'clear', 'foggy', 'windy',
            # Common action words
            'check', 'list', 'show', 'tell', 'give', 'get', 'set', 'make', 'do',
            # Time-related words that aren't places
            'am', 'pm', 'noon', 'midnight', 'morning', 'afternoon', 'evening', 'night',
            # Common multi-turn response words that aren't places
            'group', 'team', 'meeting', 'appointment', 'event', 'call', 'session',
        }

        # First, check for known city names anywhere in text (highest priority)
        for city in known_cities:
            if city in text_lower:
                return city.title()

        # Pattern to extract place after prepositions
        # Look for capitalized words in original text after "in", "at", "for"
        pattern = r'\b(?:in|at|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        match = re.search(pattern, text_original)
        if match:
            place = match.group(1).strip()
            # Check if it's not a stopword and not followed by "of" (to avoid "12th of January")
            if place.lower() not in stopwords and not re.search(r'\b' + re.escape(place) + r'\s+of\b', text_original, re.IGNORECASE):
                return place

        # Fallback: Look for any single word after "in", "at", "for" in lowercase version
        # Avoid multi-word extractions that might include other entities
        pattern = r'\b(?:in|at|for)\s+(\w+)\b'
        match = re.search(pattern, text_lower)
        if match:
            place = match.group(1).strip()
            if place.lower() not in stopwords:
                # Skip if it looks like a time (e.g., "4pm", "10am")
                if not re.match(r'^\d+[ap]\.?m\.?$', place, re.IGNORECASE):
                    return place.title()  # Capitalize first letter

        # Last resort: If input is short (1-3 words) and contains a capitalized word,
        # treat it as a standalone place name (for multi-turn dialogue responses)
        words = text_original.split()
        if len(words) <= 3:
            for word in words:
                # Check if word starts with capital and is not a stopword
                clean_word = word.strip('.,!?')
                if clean_word and clean_word[0].isupper() and clean_word.lower() not in stopwords:
                    # Verify it's not a common non-place word or a time expression
                    if clean_word.lower() not in {'i', 'me', 'you', 'we', 'they', 'he', 'she', 'ok', 'yes', 'no'}:
                        # Skip if it looks like a time (e.g., "4pm", "10AM")
                        if re.match(r'^\d+[ap]\.?m\.?$', clean_word, re.IGNORECASE):
                            continue
                        return clean_word

        # Final fallback: If input is a single word, treat it as a potential place name
        # (handles ASR transcriptions that come through in lowercase)
        words_lower = text_lower.split()
        if len(words_lower) == 1:
            clean_word = words_lower[0].strip('.,!?')
            if clean_word and len(clean_word) >= 3 and clean_word not in stopwords:
                if clean_word not in {'i', 'me', 'you', 'we', 'they', 'he', 'she', 'ok', 'yes', 'no', 'and', 'but', 'the'}:
                    return clean_word.title()  # Capitalize and return

        return None

    def _extract_day(self, text):
        """Extract day from text"""
        for day, pattern in self.day_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return day

        # Try to extract date (e.g., "12th of January", "January 12")
        # Exclude AM/PM from matching as month names
        date_match = re.search(
            r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Z][a-z]+)',
            text,
            re.IGNORECASE
        )
        if date_match:
            potential_month = date_match.group(2).lower()
            # Don't match if the "month" is actually AM/PM or other time-related words
            if potential_month not in ['am', 'pm', 'noon', 'midnight', 'oclock', 'o\'clock']:
                return f"{date_match.group(2)} {date_match.group(1)}"

        return None

    def _extract_all_days(self, text):
        """Extract all days mentioned in text (for 'today or tomorrow' type queries)"""
        found_days = []

        # Check for "day after tomorrow" first to avoid double-counting
        if re.search(self.day_patterns['day after tomorrow'], text, re.IGNORECASE):
            found_days.append('day after tomorrow')
            # Remove "day after tomorrow" from text to avoid matching "tomorrow" again
            text = re.sub(r'\bday\s+after\s+tomorrow\b', '', text, flags=re.IGNORECASE)

        # Check for remaining day patterns
        for day, pattern in self.day_patterns.items():
            if day == 'day after tomorrow':
                continue  # Already checked
            if re.search(pattern, text, re.IGNORECASE):
                found_days.append(day)

        # Try to extract date (e.g., "12th of January", "January 12")
        date_match = re.search(
            r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?([A-Z][a-z]+)',
            text,
            re.IGNORECASE
        )
        if date_match:
            potential_month = date_match.group(2).lower()
            if potential_month not in ['am', 'pm', 'noon', 'midnight', 'oclock', 'o\'clock']:
                found_days.append(f"{date_match.group(2)} {date_match.group(1)}")

        return found_days if found_days else None

    def _extract_weather_condition(self, text):
        """Extract weather condition from text"""
        for condition in self.weather_conditions:
            if condition in text:
                return condition
        return None

    def _extract_title(self, text):
        """Extract appointment title from text"""
        # Look for "titled/called/named X" pattern - use greedy match up to keywords
        # Capture everything after titled/called/named until we hit for/on/at/the + day/date
        match = re.search(
            r'(?:titled|called|named)[,\s]+(.+?)(?:\s+for\s+(?:the\s+)?\d|\s+for\s+(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\s+on\s+|\s+at\s+\d|\.|\s*$)',
            text, re.IGNORECASE
        )
        if match:
            title = match.group(1).strip()
            # Remove trailing words and leading/trailing commas
            title = re.sub(r'^[,\s]+|[,\s]+$', '', title)
            title = re.sub(r'\s+(for|on|at|the|to|of)$', '', title, flags=re.IGNORECASE)
            if title and len(title) > 1:
                return title

        # Pattern for "the X appointment/meeting" (for delete/cancel commands)
        # e.g., "Cancel the Doctor appointment" → title = "Doctor"
        # Also matches "delete the Team Meeting" → title = "Team Meeting"
        match = re.search(
            r'\b(?:delete|remove|cancel|drop)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:appointment|meeting|event)?\b',
            text, re.IGNORECASE
        )
        if match:
            title = match.group(1).strip()
            # Filter out common words that aren't titles
            non_titles = {'my', 'the', 'a', 'an', 'this', 'that', 'next', 'last', 'previous', 'previously', 'created', 'previously created', 'by'}
            if title.lower() not in non_titles and 'previously' not in title.lower():
                return title

        # Look for quoted text
        match = re.search(r'["\']([^"\']+)["\']', text)
        if match:
            return match.group(1).strip()

        # Look for "the title is X" or "title should be X" or "title would be X"
        # Also handle "the title for X is Y" pattern
        # Stop at "and the time", "and time", "at [digit]", "for", period, or end
        match = re.search(r'(?:the\s+)?title\s+(?:for\s+.+?\s+)?(?:is|should\s+be|would\s+be|will\s+be)\s+(.+?)(?:\s+and\s+(?:the\s+)?(?:time|date)|\s+at\s+\d|\s+for\s+|\.|,\s*and\s*|$)', text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Clean up trailing words that shouldn't be part of the title
            title = re.sub(r'\s+(?:and|at|for|on|the|time|date)\s*$', '', title, flags=re.IGNORECASE)
            if title and len(title) > 1:
                return title

        # Handle "time," pattern (ASR mis-transcription of "title is")
        # e.g., "the time, team meeting" -> title is "team meeting"
        match = re.search(r'^(?:the\s+)?time\s*,\s*(.+?)(?:\s+and\s+(?:the\s+)?time|\s+at\s+\d|\s+for\s+|\.|$)', text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            if title and len(title) > 1:
                return title

        # Handle "time would be X" pattern (ASR mis-transcription of "title would be X")
        # e.g., "The time would be group meeting and the time would be 4 pm"
        # -> title is "group meeting"
        match = re.search(r'(?:the\s+)?time\s+(?:would|will|should)\s+be\s+(.+?)(?:\s+and\s+(?:the\s+)?time|\s+at\s+\d|\s+for\s+|\.|$)', text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Filter out time-related words that might be captured
            if title and len(title) > 1 and not re.match(r'^\d+\s*(?:am|pm|a\.m\.|p\.m\.)?$', title, re.IGNORECASE):
                return title

        # Handle "time is X" pattern (ASR mis-transcription of "title is X")
        # e.g., "The time is team meeting" -> title is "team meeting"
        match = re.search(r'(?:the\s+)?time\s+is\s+(.+?)(?:\s+and\s+(?:the\s+)?time|\s+at\s+\d|\s+for\s+|\.|$)', text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Filter out actual time values
            if title and len(title) > 1 and not re.match(r'^\d+\s*(?:am|pm|a\.m\.|p\.m\.)?$', title, re.IGNORECASE):
                # Also filter out pure time expressions like "4 pm"
                if not re.match(r'^\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?$', title, re.IGNORECASE):
                    return title

        # Fallback: Look for "X time is Y" or "X at Y" pattern where X is the title
        # e.g., "meeting time is 4 p.m." -> title is "meeting"
        match = re.search(r'^(\w+(?:\s+\w+)?)\s+(?:time\s+is|at\s+\d)', text, re.IGNORECASE)
        if match:
            potential_title = match.group(1).strip()
            # Filter out common non-title words
            if potential_title.lower() not in ['the', 'a', 'an', 'my', 'your', 'its', 'this', 'that']:
                return potential_title

        return None

    def _extract_appointment_location(self, text):
        """Extract location for appointment"""
        # Look for "in/at Room X" or "in/at Building X"
        match = re.search(r'(?:in|at)\s+(Room|Building)\s+(\w+)', text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}"

        return None

    def _extract_datetime(self, text):
        """Extract date and time information"""
        result = {}

        # Fix common ASR mis-transcriptions of numbers before processing
        text_fixed = text.lower()
        # "to PM" → "2 PM", "for PM" → "4 PM", etc.
        time_mistranscriptions = {
            r'\bto\s+(p\.?m\.?|a\.?m\.?)\b': '2 \\1',
            r'\btoo\s+(p\.?m\.?|a\.?m\.?)\b': '2 \\1',
            r'\bfor\s+(p\.?m\.?|a\.?m\.?)\b': '4 \\1',
            r'\bfour\s+(p\.?m\.?|a\.?m\.?)\b': '4 \\1',
            r'\bwon\s+(p\.?m\.?|a\.?m\.?)\b': '1 \\1',
            r'\bone\s+(p\.?m\.?|a\.?m\.?)\b': '1 \\1',
            r'\bate\s+(p\.?m\.?|a\.?m\.?)\b': '8 \\1',
            r'\beight\s+(p\.?m\.?|a\.?m\.?)\b': '8 \\1',
            r'\bsix\s+(p\.?m\.?|a\.?m\.?)\b': '6 \\1',
            r'\bten\s+(p\.?m\.?|a\.?m\.?)\b': '10 \\1',
            r'\bnine\s+(p\.?m\.?|a\.?m\.?)\b': '9 \\1',
            r'\bfive\s+(p\.?m\.?|a\.?m\.?)\b': '5 \\1',
            r'\bthree\s+(p\.?m\.?|a\.?m\.?)\b': '3 \\1',
            r'\bseven\s+(p\.?m\.?|a\.?m\.?)\b': '7 \\1',
            r'\beleven\s+(p\.?m\.?|a\.?m\.?)\b': '11 \\1',
            r'\btwelve\s+(p\.?m\.?|a\.?m\.?)\b': '12 \\1',
        }
        for pattern, replacement in time_mistranscriptions.items():
            text_fixed = re.sub(pattern, replacement, text_fixed, flags=re.IGNORECASE)

        # Normalize "9.pm" or "9.am" → "9 pm" / "9 am" (period as separator without minutes)
        text_fixed = re.sub(r'\b(\d{1,2})\.(a\.?m\.?|p\.?m\.?)\b', r'\1 \2', text_fixed)

        # Normalize period as time separator to colon (6.15 → 6:15, 10.30 → 10:30, 7.40pm → 7:40pm)
        # Only do this for patterns that look like times (digit.digit format)
        # Use lookahead instead of \b at end, since \b doesn't match between digit and letter (e.g., "40p" in "7.40pm")
        text_fixed = re.sub(r'\b(\d{1,2})\.(\d{2})(?=\b|[a-zA-Z])', r'\1:\2', text_fixed)

        # Extract date
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text_fixed)
            if match:
                try:
                    result['date'] = match.group(0)
                except:
                    pass

        # Also handle period-separated times before colon patterns (e.g., "6.15" → extract as 6:15)
        # This is a fallback in case the earlier normalization didn't work
        period_time_match = re.search(r'\b(\d{1,2})\.(\d{2})(?=\b|[a-zA-Z])', text)  # Search original text
        if period_time_match:
            hour = period_time_match.group(1)
            minutes = period_time_match.group(2)
            if int(minutes) < 60:  # Valid minutes
                result['time'] = f"{hour}:{minutes}"
                return result

        # Extract time - support multiple formats:
        # "10:30 AM", "10:30", "10 AM", "10AM", "4 p.m.", "noon", "midnight", "6 15" (spoken)
        # Also supports 24-hour format: "14:30", "1430", "18 00"
        # Also supports "at 10" or "at 10." without AM/PM
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)?',  # 10:30 AM, 14:30, 10:30 p.m.
            r'\b([01]?\d|2[0-3])(\d{2})\s*(?:hrs?|hours?)?\b',  # 1430, 0930, 1800 hours (military)
            r'(\d{1,2})\s*(a\.?m\.?|p\.?m\.?)',  # 10 AM, 10AM, 4 p.m., 4p.m.
            r'\b(\d{1,2})\s+(\d{2})\b',  # "6 15" or "10 30" (spoken without separator)
            r'\bat\s+(\d{1,2})(?:\.|\s|$)',  # "at 10" or "at 10." without AM/PM
            r'\b(noon|midday)\b',  # noon
            r'\b(midnight)\b',  # midnight
        ]

        for pattern in time_patterns:
            time_match = re.search(pattern, text_fixed, re.IGNORECASE)
            if time_match:
                matched = time_match.group(0)
                # Normalize time format
                if 'noon' in matched.lower() or 'midday' in matched.lower():
                    result['time'] = '12:00'
                elif 'midnight' in matched.lower():
                    result['time'] = '00:00'
                else:
                    # Convert various formats to standard time format
                    if ':' not in matched:
                        hour = time_match.group(1)
                        group2 = time_match.group(2) if len(time_match.groups()) > 1 else ''
                        # Check if second group is minutes (2 digits) or AM/PM
                        if group2 and group2.isdigit() and len(group2) == 2:
                            # "6 15" or "1430" format -> "6:15" or "14:30"
                            minutes = int(group2)
                            if minutes < 60:  # Valid minutes
                                result['time'] = f"{hour}:{group2}"
                            else:
                                result['time'] = f"{hour}:00"
                        elif group2:
                            # "10 AM" format -> "10:00 AM"
                            result['time'] = f"{hour}:00 {group2}".strip()
                        else:
                            result['time'] = f"{hour}:00"
                    else:
                        result['time'] = matched
                break

        return result

    def _extract_temporal_reference(self, text):
        """Detect references to previous context (e.g., 'there', 'previously', 'that')"""
        reference_patterns = [
            r'\bthere\b',
            r'\bprevious(?:ly)?\b',
            r'\bthat\s+(?:one|appointment|event)\b',
            r'\bit\b',
            r'\bthe\s+(?:last|previous)\b',
        ]

        for pattern in reference_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False


if __name__ == "__main__":
    # Test NLU module
    print("Testing NLU Module\n")

    nlu = NLUModule()

    # Test cases
    test_utterances = [
        "What will the weather be like today in Marburg?",
        "What will the weather be on Friday in Frankfurt?",
        "Will it rain there on Saturday?",
        "Where is my next appointment?",
        "Add an appointment titled XYZ for the 12th of January.",
        "Delete the previously created appointment.",
        "Change the place for my appointment tomorrow.",
    ]

    for utterance in test_utterances:
        print(f"Input: {utterance}")
        result = nlu.understand(utterance)
        print(f"Intent: {result['intent']}")
        print(f"Entities: {result['entities']}")
        print()
