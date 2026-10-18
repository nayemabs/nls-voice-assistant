"""
Automatic Speech Recognition (ASR) Module - Faster Version
Uses faster-whisper for 4x speed improvement with same accuracy

Device Support:
- CUDA: NVIDIA GPUs (fastest)
- MPS: Apple Silicon (macOS only, native)
- CPU: Universal fallback
"""

import speech_recognition as sr
import numpy as np
import subprocess
import tempfile
import os
import re
from faster_whisper import WhisperModel


# Known ASR corrections for German cities and common misrecognitions
# Maps common ASR errors to correct spellings
ASR_CORRECTIONS = {
    # Marburg variations
    'my book': 'Marburg',
    'my berg': 'Marburg',
    'marberg': 'Marburg',
    'mar book': 'Marburg',
    'marbuk': 'Marburg',
    'my burg': 'Marburg',
    # Frankfurt variations
    'frank furt': 'Frankfurt',
    'frankford': 'Frankfurt',
    'frank ford': 'Frankfurt',
    # Munich variations
    'munick': 'Munich',
    'munic': 'Munich',
    'münchen': 'Munich',
    # Hamburg variations
    'ham burg': 'Hamburg',
    'hamberg': 'Hamburg',
    # Cologne variations
    'colon': 'Cologne',
    'koln': 'Cologne',
    'köln': 'Cologne',
    # Stuttgart variations
    'stutgart': 'Stuttgart',
    'stut gart': 'Stuttgart',
    # Dresden variations
    'drezden': 'Dresden',
    # Leipzig variations
    'leipsig': 'Leipzig',
    'lipsig': 'Leipzig',
    # Dusseldorf variations
    'duseldorf': 'Dusseldorf',
    'dussel dorf': 'Dusseldorf',
    'düsseldorf': 'Dusseldorf',
    # Hannover variations
    'hanover': 'Hannover',
    'hano ver': 'Hannover',
    # Nuremberg variations
    'nuremburg': 'Nuremberg',
    'nurnberg': 'Nuremberg',
    'nürnberg': 'Nuremberg',

    # ========== GERMAN WORD TRANSLATIONS ==========
    # Weather-related German words
    'wetter': 'weather',
    'regen': 'rain',
    'regnet': 'rain',
    'schnee': 'snow',
    'sonnig': 'sunny',
    'sonne': 'sunny',
    'wolkig': 'cloudy',
    'wolken': 'clouds',
    'kalt': 'cold',
    'warm': 'warm',
    'heiß': 'hot',
    'heiss': 'hot',
    'temperatur': 'temperature',
    'vorhersage': 'forecast',
    'draußen': 'outside',
    'draussen': 'outside',

    # Day names (German → English)
    'montag': 'Monday',
    'dienstag': 'Tuesday',
    'mittwoch': 'Wednesday',
    'donnerstag': 'Thursday',
    'freitag': 'Friday',
    'samstag': 'Saturday',
    'sonntag': 'Sunday',
    'heute': 'today',
    'morgen': 'tomorrow',
    'gestern': 'yesterday',
    'wochenende': 'weekend',
    'nächste woche': 'next week',
    'nachste woche': 'next week',

    # Appointment-related German words
    'termin': 'appointment',
    'termine': 'appointments',
    'besprechung': 'meeting',
    'sitzung': 'meeting',
    'treffen': 'meeting',
    'kalender': 'calendar',
    'zeitplan': 'schedule',

    # Action verbs (German → English)
    'erstellen': 'create',
    'hinzufügen': 'add',
    'hinzufugen': 'add',
    'löschen': 'delete',
    'loschen': 'delete',
    'entfernen': 'remove',
    'absagen': 'cancel',
    'ändern': 'change',
    'andern': 'change',
    'aktualisieren': 'update',
    'verschieben': 'move',
    'zeigen': 'show',
    'anzeigen': 'show',

    # Question words (German → English)
    'was': 'what',
    'wann': 'when',
    'wo': 'where',
    'wie': 'how',
    'welche': 'which',
    'welcher': 'which',

    # Common German phrases/words
    'bitte': 'please',
    'danke': 'thanks',
    'ja': 'yes',
    'nein': 'no',
    'und': 'and',
    'oder': 'or',
    'für': 'for',
    'fur': 'for',
    'um': 'at',
    'uhr': "o'clock",
    'in': 'in',
    'am': 'on',
    'mein': 'my',
    'meine': 'my',
    'nächster': 'next',
    'nachster': 'next',
    'nächste': 'next',
    'nachste': 'next',

    # Common misrecognitions
    'whether': 'weather',
    'wether': 'weather',
    'feather': 'weather',
    'village raid': 'will it rain',
    'village rate': 'will it rain',
    'buch': 'book',

    # Common title/meeting word errors
    'teon': 'team',
    'teem': 'team',
    'metting': 'meeting',
    'meating': 'meeting',
    'apointment': 'appointment',
    'appointement': 'appointment',
    'scedule': 'schedule',
    'shedule': 'schedule',
    'titeled': 'titled',
    'tytled': 'titled',
    'caled': 'called',
    'nemed': 'named',

    # Location/place errors
    'marbourg': 'Marburg',
    'marberg': 'Marburg',
    'frankfort': 'Frankfurt',
    'berling': 'Berlin',
    'munic': 'Munich',
    'hambourg': 'Hamburg',

    # Common word errors
    'tommorow': 'tomorrow',
    'tomorow': 'tomorrow',
    'tomarrow': 'tomorrow',
    'yestarday': 'yesterday',
    'wendsday': 'Wednesday',
    'thurdsay': 'Thursday',

    # ASR errors for weather conditions
    'thander': 'thunder',
    'tunder': 'thunder',

    # ASR errors for days
    'sanday': 'sunday',
    'munday': 'monday',
    'tusday': 'tuesday',
    'wensday': 'wednesday',
    'wendsday': 'wednesday',
    'thursay': 'thursday',
    'fridey': 'friday',
    'saterday': 'saturday',

    # ASR errors for months
    'yesnuary': 'january',
    'janury': 'january',
    'febuary': 'february',
    'febrary': 'february',

    # City name ASR errors
    'honburg': 'Hamburg',
    'hamborg': 'Hamburg',
    'bochat': 'Bochum',
    'bocham': 'Bochum',

    # Common word errors
    'wheather': 'weather',
    'temperture': 'temperature',
    'temprature': 'temperature',
}

# Regex patterns for more complex corrections
ASR_PATTERN_CORRECTIONS = [
    # "in my book" → "in Marburg" (contextual fix)
    (r'\bin\s+my\s+book\b', 'in Marburg'),
    (r'\bin\s+my\s+berg\b', 'in Marburg'),
    # "for my book" → "for Marburg"
    (r'\bfor\s+my\s+book\b', 'for Marburg'),
    # Weather context fixes
    (r'\bweather\s+in\s+my\s+book\b', 'weather in Marburg'),
    # "Feather in X" → "Weather in X" (weather misrecognition)
    (r'^feather\s+in\s+', 'Weather in '),
    (r'\bfeather\s+in\s+', 'weather in '),
    # "and an appointment" → "Add an appointment" (add misrecognition)
    (r'^and\s+an\s+appointment\b', 'Add an appointment'),
    (r',\s*and\s+an\s+appointment\b', ', add an appointment'),
    # "At an appointment" → "Add an appointment" (add misrecognition)
    (r'^at\s+an\s+appointment\b', 'Add an appointment'),
    # "Ad appointment" → "Add appointment" (add misrecognition)
    (r'^ad\s+appointment\b', 'Add appointment'),
    # "Buch and appointment" → "Book an appointment"
    (r'\bbuch\s+and\s+appointment\b', 'book an appointment'),
    # "Moved my appointment" → "Move my appointment" (past tense fix for commands)
    (r'^moved\s+my\s+appointment\b', 'Move my appointment'),
    # "So my calendar" → "Show my calendar" (show misrecognition)
    (r'^so\s+my\s+calendar\b', 'Show my calendar'),
    # "Village raid today" → "Will it rain today"
    (r'^village\s+raid\s+', 'Will it rain '),
    (r'^village\s+rate\s+', 'Will it rain '),

    # ========== GERMAN PHRASE PATTERNS ==========
    # "Wie ist das Wetter" → "What is the weather"
    (r'\bwie\s+ist\s+das\s+wetter\b', 'what is the weather'),
    (r'\bwie\s+ist\s+das\s+wetter\s+in\b', 'what is the weather in'),
    # "Wird es regnen" → "Will it rain"
    (r'\bwird\s+es\s+regnen\b', 'will it rain'),
    # "Regnet es" → "Is it raining"
    (r'\bregnet\s+es\b', 'is it raining'),
    # "Was ist mein Termin" → "What is my appointment"
    (r'\bwas\s+ist\s+mein\s+termin\b', 'what is my appointment'),
    # "Zeig mir meine Termine" → "Show me my appointments"
    (r'\bzeig\s+mir\s+meine\s+termine\b', 'show me my appointments'),
    # "Erstelle einen Termin" → "Create an appointment"
    (r'\berstelle\s+einen\s+termin\b', 'create an appointment'),
    # "Lösche den Termin" → "Delete the appointment"
    (r'\blösche\s+den\s+termin\b', 'delete the appointment'),
    (r'\blosche\s+den\s+termin\b', 'delete the appointment'),
    # "Ändere meinen Termin" → "Change my appointment"
    (r'\bändere\s+meinen\s+termin\b', 'change my appointment'),
    (r'\bandere\s+meinen\s+termin\b', 'change my appointment'),
    # "um X Uhr" → "at X o'clock"
    (r'\bum\s+(\d{1,2})\s+uhr\b', r'at \1 oclock'),
    # German time format "14 Uhr 30" → "14:30"
    (r'\b(\d{1,2})\s+uhr\s+(\d{2})\b', r'\1:\2'),
    # "am Montag" → "on Monday"
    (r'\bam\s+montag\b', 'on Monday'),
    (r'\bam\s+dienstag\b', 'on Tuesday'),
    (r'\bam\s+mittwoch\b', 'on Wednesday'),
    (r'\bam\s+donnerstag\b', 'on Thursday'),
    (r'\bam\s+freitag\b', 'on Friday'),
    (r'\bam\s+samstag\b', 'on Saturday'),
    (r'\bam\s+sonntag\b', 'on Sunday'),
    # "Wetter morgen" → "weather tomorrow"
    (r'\bwetter\s+morgen\b', 'weather tomorrow'),
    (r'\bwetter\s+heute\b', 'weather today'),

    # ASR error corrections
    (r'\bnoned\b', 'named'),  # "noned" → "named"
    (r'\btiteld\b', 'titled'),  # "titeld" → "titled"
    (r'\bcalled\b', 'called'),  # ensure "called" stays

    # Common misheard phrases
    (r'^this\s+does\s+weather\b', "What's the weather"),  # "This does weather" → "What's the weather"
    (r'\bthis\s+does\s+weather\b', "what's the weather"),  # non-initial position
    (r'^what\s+does\s+weather\b', "What's the weather"),  # "What does weather" → "What's the weather"
    (r'^what\s+is\s+does\s+weather\b', "What's the weather"),  # "What is does weather"

    # Leading comma/punctuation cleanup
    (r'^[,\s]+', ''),

    # "Whether" at start of sentence likely "What's the weather"
    (r'^whether\s+in\s+', "What's the weather in "),

    # Time format normalization
    (r'\b(\d{1,2})\s+thirty\b', r'\1:30'),
    (r'\b(\d{1,2})\s+fifteen\b', r'\1:15'),
    (r'\bhalf\s+past\s+(\d{1,2})\b', r'\1:30'),
    (r'\bquarter\s+past\s+(\d{1,2})\b', r'\1:15'),
]


def post_process_transcription(text):
    """
    Apply post-processing corrections to ASR output

    Fixes known transcription errors, especially for German city names
    that are commonly misrecognized.

    Args:
        text: Raw transcribed text

    Returns:
        str: Corrected text
    """
    if not text:
        return text

    corrected = text

    # Apply pattern-based corrections first (more specific)
    for pattern, replacement in ASR_PATTERN_CORRECTIONS:
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

    # Apply word-level corrections
    for wrong, right in ASR_CORRECTIONS.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(wrong), re.IGNORECASE)
        corrected = pattern.sub(right, corrected)

    return corrected


def detect_best_device():
    """
    Auto-detect the best available compute device

    Priority: CUDA > CPU (MPS not supported by faster-whisper)

    Returns:
        tuple: (device, compute_type)
    """
    # Check environment variable override
    env_device = os.environ.get('WHISPER_DEVICE', 'auto').lower()
    env_compute = os.environ.get('WHISPER_COMPUTE_TYPE', '')

    if env_device != 'auto':
        # User specified device
        if env_device == 'cuda':
            compute = env_compute or 'float16'
            return 'cuda', compute
        elif env_device == 'cpu':
            compute = env_compute or 'int8'
            return 'cpu', compute

    # Auto-detect: Check for CUDA
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA detected: {torch.cuda.get_device_name(0)}")
            return 'cuda', env_compute or 'float16'
    except ImportError:
        pass

    # Check for CUDA without torch (ctranslate2 backend)
    try:
        import ctranslate2
        if 'cuda' in ctranslate2.get_supported_compute_types():
            print("CUDA detected via ctranslate2")
            return 'cuda', env_compute or 'float16'
    except (ImportError, Exception):
        pass

    # Fallback to CPU
    print("Using CPU (no GPU acceleration detected)")
    return 'cpu', env_compute or 'int8'


class ASRModule:
    """Handles speech-to-text conversion using faster-whisper (optimized)"""

    def __init__(self, model_size=None, device=None, compute_type=None):
        """
        Initialize ASR module with faster-whisper

        Args:
            model_size: Size of Whisper model (tiny, base, small, medium, large-v2, large-v3)
                       - tiny: 39M params, very fast, least accurate
                       - base: 74M params, fast, okay accuracy
                       - small: 244M params, balanced (recommended)
                       - medium: 769M params, slower, very accurate
                       - large-v3: 1550M params, slowest, best accuracy
                       If None, uses WHISPER_MODEL_SIZE env var or 'small'
            device: "cpu", "cuda", or None for auto-detect
            compute_type: "int8" (CPU), "float16" (GPU), "float32", or None for auto
        """
        # Get model size from env or default
        if model_size is None:
            model_size = os.environ.get('WHISPER_MODEL_SIZE', 'small')

        # Auto-detect device if not specified
        if device is None or compute_type is None:
            detected_device, detected_compute = detect_best_device()
            device = device or detected_device
            compute_type = compute_type or detected_compute

        print(f"Loading faster-whisper model ({model_size}, device={device}, compute={compute_type})...")

        # Load faster-whisper model (4x faster than regular whisper)
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=None
        )

        self.device = device
        self.compute_type = compute_type

        self.recognizer = sr.Recognizer()

        # Optimized recognition settings for better accuracy
        self.recognizer.energy_threshold = 300  # Lower = more sensitive
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.5  # Seconds of silence to consider end (increased)

        # Generate audio cue tones
        self._generate_tone_files()

        print(f"faster-whisper ASR initialized successfully (4x faster than standard Whisper)")

    def _generate_tone_files(self):
        """Generate subtle audio cue tones for listening indicators"""
        self.tone_dir = tempfile.mkdtemp()

        # Start tone: gentle ascending tone (indicates "start speaking")
        self.start_tone_path = os.path.join(self.tone_dir, "start_tone.wav")
        self._create_tone(self.start_tone_path, frequencies=[440, 550], duration=0.15, volume=0.3)

        # Stop tone: gentle descending tone (indicates "done listening")
        self.stop_tone_path = os.path.join(self.tone_dir, "stop_tone.wav")
        self._create_tone(self.stop_tone_path, frequencies=[550, 440], duration=0.15, volume=0.3)

    def _create_tone(self, filepath, frequencies, duration=0.15, volume=0.3, sample_rate=44100):
        """Create a simple tone WAV file"""
        import wave
        import struct

        samples_per_freq = int(sample_rate * duration / len(frequencies))
        samples = []

        for freq in frequencies:
            for i in range(samples_per_freq):
                t = i / sample_rate
                # Smooth fade in/out to avoid clicks
                fade = min(i / 500, 1.0, (samples_per_freq - i) / 500)
                sample = volume * fade * np.sin(2 * np.pi * freq * t)
                samples.append(sample)

        # Convert to 16-bit PCM
        audio_data = np.array(samples) * 32767
        audio_data = audio_data.astype(np.int16)

        # Write WAV file
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

    def _play_tone(self, tone_path, blocking=True):
        """Play an audio tone file"""
        try:
            import platform
            if platform.system() == "Darwin":
                cmd = ["afplay", tone_path]
            else:
                cmd = ["aplay", "-q", tone_path]

            if blocking:
                subprocess.run(cmd, check=False, capture_output=True)
            else:
                # Non-blocking playback
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass  # Silently fail if tone can't be played

    def play_start_tone(self, blocking=True):
        """Play the start listening tone"""
        self._play_tone(self.start_tone_path, blocking=blocking)

    def play_stop_tone(self, blocking=True):
        """Play the stop listening tone"""
        self._play_tone(self.stop_tone_path, blocking=blocking)

    def listen_from_microphone(self, timeout=8, phrase_time_limit=20):
        """
        Listen to microphone input and convert to text

        Args:
            timeout: Maximum time to wait for phrase to start (increased to 8s)
            phrase_time_limit: Maximum time for phrase (increased to 20s)

        Returns:
            str: Transcribed text or None if failed
        """
        import time

        with sr.Microphone(sample_rate=16000) as source:
            # Calibrate for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            # Play start tone BEFORE listening begins (blocking so user hears it first)
            self.play_start_tone(blocking=True)
            # Small delay to let tone finish and user prepare
            time.sleep(0.05)

            print("Listening... (speak now)")

            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                # Play stop tone IMMEDIATELY after audio captured (non-blocking)
                # so transcription can start while tone plays
                self.play_stop_tone(blocking=False)
                return self.transcribe_audio(audio)
            except sr.WaitTimeoutError:
                self.play_stop_tone(blocking=False)
                print("No speech detected - timeout waiting for speech")
                return None
            except Exception as e:
                self.play_stop_tone(blocking=False)
                print(f"Error listening to microphone: {e}")
                return None

    def transcribe_audio(self, audio, return_alternatives: bool = False):
        """
        Transcribe audio using faster-whisper

        Args:
            audio: AudioData object from speech_recognition
            return_alternatives: If True, return list of (text, confidence) tuples

        Returns:
            str: Transcribed text (or list of alternatives if return_alternatives=True)
        """
        try:
            # Convert audio to format faster-whisper expects (float32)
            audio_data = np.frombuffer(audio.get_raw_data(), np.int16).astype(np.float32) / 32768.0

            # Transcribe using faster-whisper with optimized settings
            # Use initial_prompt to bias towards appointment/weather vocabulary AND German cities
            prompt = (
                "appointment, meeting, schedule, weather, forecast, tomorrow, today, delete, create, update, "
                "titled, called, named, rain, sunny, cloudy, temperature, "
                "Marburg, Frankfurt, Berlin, Munich, Hamburg, Cologne, Stuttgart, Dresden, Leipzig, "
                "Dusseldorf, Bonn, Hannover, Bremen, Essen, Nuremberg, Dortmund, Duisburg, Bochum, "
                "Wuppertal, Bielefeld, Dhaka, London, Paris, New York"
            )

            segments, info = self.model.transcribe(
                audio_data,
                language="en",
                beam_size=5,  # Beam search for better accuracy
                best_of=5,  # Try 5 different decodings
                temperature=0.0,  # Deterministic (no randomness)
                condition_on_previous_text=False,  # Don't bias based on history
                vad_filter=True,  # Voice Activity Detection - removes silence
                vad_parameters=dict(min_silence_duration_ms=500),  # Ignore short silences
                initial_prompt=prompt,  # Vocabulary hints for better accuracy
                word_timestamps=False,  # Faster without word-level timestamps
                no_speech_threshold=0.6,  # Higher threshold to filter out noise
            )

            # Combine all segments into final text
            segments_list = list(segments)
            text = " ".join([segment.text for segment in segments_list]).strip()

            # Calculate average confidence from segments
            if segments_list:
                avg_confidence = sum(seg.avg_logprob for seg in segments_list) / len(segments_list)
                # Convert log probability to confidence (0-1 scale)
                confidence = max(0, min(1, 1 + avg_confidence))  # log probs are negative
            else:
                confidence = 0.5

            # Apply post-processing corrections for known ASR errors
            text = post_process_transcription(text)

            print(f"Transcribed: {text}")

            if return_alternatives:
                return [(text, confidence)]
            return text
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return [] if return_alternatives else None

    def transcribe_audio_nbest(self, audio, n: int = 3):
        """
        Transcribe audio and return N-best hypotheses.
        Uses temperature sampling to generate diverse alternatives.

        Args:
            audio: AudioData object from speech_recognition
            n: Number of hypotheses to return

        Returns:
            List of (text, confidence) tuples, sorted by confidence
        """
        try:
            audio_data = np.frombuffer(audio.get_raw_data(), np.int16).astype(np.float32) / 32768.0

            prompt = (
                "appointment, meeting, schedule, weather, forecast, tomorrow, today, delete, create, update, "
                "titled, called, named, rain, sunny, cloudy, temperature, "
                "Marburg, Frankfurt, Berlin, Munich, Hamburg, Cologne, Stuttgart, Dresden, Leipzig, "
                "Dusseldorf, Bonn, Hannover, Bremen, Essen, Nuremberg, Dortmund, Duisburg, Bochum"
            )

            hypotheses = []

            # Generate primary hypothesis (beam search, deterministic)
            segments, _ = self.model.transcribe(
                audio_data,
                language="en",
                beam_size=5,
                best_of=5,
                temperature=0.0,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                initial_prompt=prompt,
            )
            segments_list = list(segments)
            if segments_list:
                text = " ".join([seg.text for seg in segments_list]).strip()
                text = post_process_transcription(text)
                confidence = max(0, min(1, 1 + sum(seg.avg_logprob for seg in segments_list) / len(segments_list)))
                hypotheses.append((text, confidence))

            # Generate alternative hypotheses with temperature sampling
            if n > 1:
                for temp in [0.2, 0.4]:
                    if len(hypotheses) >= n:
                        break
                    segments, _ = self.model.transcribe(
                        audio_data,
                        language="en",
                        beam_size=3,
                        best_of=3,
                        temperature=temp,
                        vad_filter=True,
                        initial_prompt=prompt,
                    )
                    segments_list = list(segments)
                    if segments_list:
                        text = " ".join([seg.text for seg in segments_list]).strip()
                        text = post_process_transcription(text)
                        # Only add if different from existing hypotheses
                        if text and text not in [h[0] for h in hypotheses]:
                            confidence = max(0, min(1, 1 + sum(seg.avg_logprob for seg in segments_list) / len(segments_list)))
                            # Penalize temperature-sampled hypotheses slightly
                            hypotheses.append((text, confidence * 0.95))

            # Sort by confidence
            hypotheses.sort(key=lambda x: x[1], reverse=True)
            return hypotheses[:n]

        except Exception as e:
            print(f"Error in N-best transcription: {e}")
            return []

    def transcribe_file(self, audio_file_path):
        """
        Transcribe audio from file

        Args:
            audio_file_path: Path to audio file (supports wav, mp3, m4a, etc.)

        Returns:
            str: Transcribed text
        """
        try:
            # Use same settings as microphone transcription for consistency
            # Include German city names in prompt for better recognition
            prompt = (
                "appointment, meeting, schedule, weather, forecast, tomorrow, today, delete, create, update, "
                "Marburg, Frankfurt, Berlin, Munich, Hamburg, Cologne, Stuttgart, Dresden, Leipzig, "
                "Dusseldorf, Bonn, Hannover, Bremen, Essen, Nuremberg, Dortmund, Duisburg, Bochum, "
                "Wuppertal, Bielefeld"
            )

            segments, info = self.model.transcribe(
                audio_file_path,
                language="en",
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                initial_prompt=prompt,
                word_timestamps=False,
                no_speech_threshold=0.6,
            )

            text = " ".join([segment.text for segment in segments]).strip()

            # Apply post-processing corrections for known ASR errors
            text = post_process_transcription(text)

            return text
        except Exception as e:
            print(f"Error transcribing file: {e}")
            return None


if __name__ == "__main__":
    # Test ASR module
    print("Testing faster-whisper ASR Module\n")
    asr = ASRModule(model_size="small")

    print("\nSpeak something...")
    text = asr.listen_from_microphone()
    if text:
        print(f"You said: {text}")
