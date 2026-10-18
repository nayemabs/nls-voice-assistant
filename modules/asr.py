"""
Automatic Speech Recognition (ASR) Module
Uses OpenAI Whisper for local speech-to-text conversion
"""

import whisper
import speech_recognition as sr
import numpy as np
import torch


class ASRModule:
    """Handles speech-to-text conversion using Whisper model"""

    def __init__(self, model_size="small"):
        """
        Initialize ASR module with Whisper model

        Args:
            model_size: Size of Whisper model (tiny, base, small, medium, large)
                       - tiny: fastest, least accurate
                       - base: fast, okay accuracy
                       - small: balanced (recommended)
                       - medium: slower, more accurate
                       - large: slowest, most accurate
        """
        print(f"Loading Whisper model ({model_size})...")
        self.model = whisper.load_model(model_size)
        self.recognizer = sr.Recognizer()

        # Improve recognition settings
        self.recognizer.energy_threshold = 300  # Lower = more sensitive
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Seconds of silence to consider end of phrase

        print("ASR module initialized successfully")

    def listen_from_microphone(self, timeout=5, phrase_time_limit=15):
        """
        Listen to microphone input and convert to text

        Args:
            timeout: Maximum time to wait for phrase to start
            phrase_time_limit: Maximum time for phrase

        Returns:
            str: Transcribed text or None if failed
        """
        with sr.Microphone(sample_rate=16000) as source:
            print("Listening... (speak now)")
            # Calibrate for ambient noise - important for better recognition
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)

            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                return self.transcribe_audio(audio)
            except sr.WaitTimeoutError:
                print("No speech detected - timeout waiting for speech")
                return None
            except Exception as e:
                print(f"Error listening to microphone: {e}")
                return None

    def transcribe_audio(self, audio):
        """
        Transcribe audio using Whisper

        Args:
            audio: AudioData object from speech_recognition

        Returns:
            str: Transcribed text
        """
        try:
            # Convert audio to format Whisper expects
            audio_data = np.frombuffer(audio.get_raw_data(), np.int16).astype(np.float32) / 32768.0

            # Transcribe using Whisper with improved settings
            result = self.model.transcribe(
                audio_data,
                language="en",
                fp16=False,
                temperature=0.0,  # More deterministic (less random)
                best_of=5,  # Try 5 different decodings, pick best
                beam_size=5,  # Beam search for better accuracy
                condition_on_previous_text=False  # Don't bias based on previous text
            )
            text = result["text"].strip()

            print(f"Transcribed: {text}")
            return text
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None

    def transcribe_file(self, audio_file_path):
        """
        Transcribe audio from file

        Args:
            audio_file_path: Path to audio file

        Returns:
            str: Transcribed text
        """
        try:
            result = self.model.transcribe(audio_file_path, language="en")
            return result["text"].strip()
        except Exception as e:
            print(f"Error transcribing file: {e}")
            return None


if __name__ == "__main__":
    # Test ASR module
    print("Testing ASR Module")
    asr = ASRModule(model_size="base")

    print("\nSpeak something...")
    text = asr.listen_from_microphone()
    if text:
        print(f"You said: {text}")
