"""
Text-to-Speech (TTS) Module - High Performance Version
Uses Piper TTS for fast, high-quality neural speech synthesis
"""

import os
import subprocess
import tempfile
import wave
from pathlib import Path

# Try to import Piper TTS
try:
    from piper import PiperVoice
    from piper.download_voices import download_voice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

# Fallback imports
import pyttsx3


class TTSModule:
    """Handles text-to-speech conversion with multiple engine support"""

    def __init__(self, use_piper=True, voice_name="en_US-lessac-medium"):
        """
        Initialize TTS module

        Args:
            use_piper: If True, use Piper TTS (fast neural); otherwise use pyttsx3
            voice_name: Piper voice name (en_US-lessac-medium recommended)
                       Options:
                       - en_US-lessac-medium: Natural male voice (recommended)
                       - en_US-amy-medium: Natural female voice
                       - en_GB-alan-medium: British male voice
        """
        self.use_piper = use_piper and PIPER_AVAILABLE
        self.voice_name = voice_name

        if self.use_piper:
            try:
                print(f"Loading Piper TTS voice ({voice_name})...")

                # Set up voice directory
                voice_dir = Path.home() / ".local" / "share" / "piper-tts"
                voice_dir.mkdir(parents=True, exist_ok=True)

                # Check if voice files exist
                model_path = voice_dir / f"{voice_name}.onnx"
                config_path = voice_dir / f"{voice_name}.onnx.json"

                # Download voice if needed
                if not model_path.exists() or not config_path.exists():
                    print(f"Downloading Piper voice ({voice_name})...")
                    try:
                        download_voice(voice_name, voice_dir)
                        print(f"Voice downloaded to {voice_dir}")
                    except Exception as e:
                        print(f"Failed to download voice: {e}")
                        print("Falling back to pyttsx3...")
                        self.use_piper = False
                        self._init_pyttsx3()
                        return

                # Load the voice
                self.voice = PiperVoice.load(str(model_path), config_path=str(config_path))
                print("Piper TTS initialized successfully (high-quality neural voice)")

            except Exception as e:
                print(f"Failed to load Piper TTS: {e}")
                print("Falling back to pyttsx3...")
                self.use_piper = False
                self._init_pyttsx3()
        else:
            if not PIPER_AVAILABLE and use_piper:
                print("Piper TTS not available")
                print("Using pyttsx3 instead...")
            self._init_pyttsx3()

    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine as fallback"""
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 175)  # Slightly faster speech
        self.engine.setProperty('volume', 0.9)
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
            if self.use_piper:
                # Use Piper TTS
                if output_file:
                    # Synthesize to file
                    with wave.open(output_file, 'wb') as wav_file:
                        self.voice.synthesize_wav(text, wav_file)
                    print(f"Audio saved to {output_file}")
                    # Play the audio
                    self._play_audio(output_file)
                else:
                    # Synthesize to temporary file and play
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        temp_path = temp_file.name

                    with wave.open(temp_path, 'wb') as wav_file:
                        self.voice.synthesize_wav(text, wav_file)

                    self._play_audio(temp_path)

                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

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
        Play audio file using system player

        Args:
            audio_file: Path to audio file
        """
        try:
            # macOS uses afplay
            if os.path.exists("/usr/bin/afplay"):
                subprocess.run(["afplay", audio_file], check=False)
            # Linux uses aplay or paplay
            elif os.path.exists("/usr/bin/aplay"):
                subprocess.run(["aplay", audio_file], check=False)
            elif os.path.exists("/usr/bin/paplay"):
                subprocess.run(["paplay", audio_file], check=False)
            else:
                print("No audio player found")
        except Exception as e:
            print(f"Error playing audio: {e}")


if __name__ == "__main__":
    # Test TTS module
    print("Testing Piper TTS Module\n")

    # Test with Piper
    tts = TTSModule(use_piper=True)
    tts.speak("Hello! This is the Piper text to speech system. It's fast and sounds natural.")

    print("\nAudio test complete!")
