"""
Text-to-Speech (TTS) Module
Uses Coqui TTS or pyttsx3 for local text-to-speech conversion
"""

import pyttsx3
import os

# Try to import Coqui TTS, but it's optional (requires Python <= 3.11)
try:
    from TTS.api import TTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False


class TTSModule:
    """Handles text-to-speech conversion"""

    def __init__(self, use_coqui=True, model_name="tts_models/en/ljspeech/tacotron2-DDC"):
        """
        Initialize TTS module

        Args:
            use_coqui: If True, use Coqui TTS (if available); otherwise use pyttsx3
            model_name: Coqui TTS model name
        """
        self.use_coqui = use_coqui and COQUI_AVAILABLE

        if self.use_coqui:
            try:
                print(f"Loading Coqui TTS model ({model_name})...")
                self.tts = TTS(model_name=model_name)
                print("Coqui TTS initialized successfully")
            except Exception as e:
                print(f"Failed to load Coqui TTS: {e}")
                print("Falling back to pyttsx3...")
                self.use_coqui = False
                self._init_pyttsx3()
        else:
            if not COQUI_AVAILABLE and use_coqui:
                print("Coqui TTS not available (requires Python 3.11 or lower)")
                print("Using pyttsx3 instead...")
            self._init_pyttsx3()

    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speed of speech
        self.engine.setProperty('volume', 0.9)  # Volume level
        print("pyttsx3 TTS initialized successfully")

    def speak(self, text, output_file=None):
        """
        Convert text to speech

        Args:
            text: Text to convert to speech
            output_file: Optional path to save audio file

        Returns:
            bool: True if successful
        """
        if not text:
            print("No text to speak")
            return False

        print(f"Speaking: {text}")

        try:
            if self.use_coqui:
                if output_file:
                    self.tts.tts_to_file(text=text, file_path=output_file)
                    print(f"Audio saved to {output_file}")
                    # Play the audio file
                    self._play_audio(output_file)
                else:
                    # Generate to temporary file and play
                    temp_file = "/tmp/tts_output.wav"
                    self.tts.tts_to_file(text=text, file_path=temp_file)
                    self._play_audio(temp_file)
            else:
                # Use pyttsx3
                if output_file:
                    self.engine.save_to_file(text, output_file)
                    self.engine.runAndWait()
                    print(f"Audio saved to {output_file}")
                else:
                    self.engine.say(text)
                    self.engine.runAndWait()

            return True
        except Exception as e:
            print(f"Error in TTS: {e}")
            return False

    def _play_audio(self, audio_file):
        """
        Play audio file

        Args:
            audio_file: Path to audio file
        """
        try:
            # Use system command to play audio
            if os.path.exists(audio_file):
                # For macOS
                os.system(f"afplay {audio_file}")
                # For Linux, you might use: os.system(f"aplay {audio_file}")
        except Exception as e:
            print(f"Error playing audio: {e}")

    def set_voice_properties(self, rate=None, volume=None):
        """
        Set voice properties (only for pyttsx3)

        Args:
            rate: Speech rate
            volume: Volume level (0.0 to 1.0)
        """
        if not self.use_coqui:
            if rate:
                self.engine.setProperty('rate', rate)
            if volume:
                self.engine.setProperty('volume', volume)


if __name__ == "__main__":
    # Test TTS module
    print("Testing TTS Module")
    print(f"Coqui TTS available: {COQUI_AVAILABLE}")
    print()

    # Try Coqui TTS first, fall back to pyttsx3
    tts = TTSModule(use_coqui=True)

    test_text = "Hello! I am your voice assistant. How can I help you today?"
    tts.speak(test_text)

    print("TTS test completed")
