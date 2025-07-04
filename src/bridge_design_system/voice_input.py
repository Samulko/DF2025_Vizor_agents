"""Voice input integration for Bridge Design System.

This module provides voice input functionality as an alternative to keyboard input,
using OpenAI Whisper for speech recognition and Picovoice for wake word detection.
"""

import os
import time
import io
import wave
from collections import deque
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from .config.logging_config import get_logger

logger = get_logger(__name__)

# Global flag for voice dependencies availability
_VOICE_DEPENDENCIES_AVAILABLE = None


def check_voice_dependencies() -> bool:
    """Check if voice input dependencies are available."""
    global _VOICE_DEPENDENCIES_AVAILABLE
    
    if _VOICE_DEPENDENCIES_AVAILABLE is not None:
        return _VOICE_DEPENDENCIES_AVAILABLE
    
    try:
        import numpy as np
        import pvporcupine
        import pvcobra
        import whisper
        from pvrecorder import PvRecorder
        import torch
        from openai import OpenAI
        
        _VOICE_DEPENDENCIES_AVAILABLE = True
        logger.info("✅ Voice input dependencies available")
        return True
        
    except ImportError as e:
        _VOICE_DEPENDENCIES_AVAILABLE = False
        logger.debug(f"Voice dependencies not available: {e}")
        return False


class VoiceTranscriber:
    """Handles speech transcription using OpenAI Whisper (local or API)."""
    
    def __init__(self, model: str = "tiny.en") -> None:
        if not check_voice_dependencies():
            raise RuntimeError("Voice dependencies not available")
            
        # Import here to avoid errors when dependencies aren't available
        import numpy as np
        from openai import OpenAI
        import whisper
        
        self.np = np
        self.use_openai_api = os.environ.get("USE_OPENAI_API", "false").lower() == "true"
        self.prompts = os.environ.get("WHISPER_INITIAL_PROMPT", "")
        
        if self.use_openai_api:
            logger.info("🌐 Using OpenAI API for transcription")
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            self.model = None
        else:
            logger.info("🔄 Loading local Whisper model...")
            self.model = whisper.load_model(model)
            logger.info("✅ Local Whisper model loaded")
            self.client = None
        
        if self.prompts:
            logger.info(f"🎯 Using context prompts: {self.prompts}")

    def transcribe(self, frames) -> str:
        """Transcribe audio frames to text."""
        try:
            if self.use_openai_api:
                return self._transcribe_with_api(frames)
            else:
                return self._transcribe_locally(frames)
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return "transcription failed"
    
    def _transcribe_locally(self, frames) -> str:
        """Transcribe using local Whisper model."""
        samples = self.np.array(frames, self.np.int16).flatten().astype(self.np.float32) / 32768.0

        result = self.model.transcribe(
            audio=samples,
            language="en",
            fp16=False,
            initial_prompt=self.prompts,
        )

        return result.get("text", "speech not detected").strip()
    
    def _transcribe_with_api(self, frames) -> str:
        """Transcribe using OpenAI API."""
        try:
            import wave
            
            # Convert frames to WAV format for OpenAI API
            samples = self.np.array(frames, self.np.int16).flatten()
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(samples.tobytes())
            
            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"  # OpenAI requires a filename
            
            # Send to OpenAI API
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                language="en",
                prompt=self.prompts if self.prompts else None
            )
            
            return transcript.text.strip() if transcript.text.strip() else "speech not detected"
            
        except Exception as e:
            logger.error(f"OpenAI API transcription error: {e}")
            return "transcription failed"


class VoiceInputBridge:
    """Bridge for voice input integration with the main CLI."""
    
    def __init__(self):
        """Initialize voice input bridge."""
        self.transcriber = None
        self.porcupine = None
        self.cobra = None
        self.recorder = None
        self.initialized = False
        
        # Load environment variables
        load_dotenv()
        
    def initialize(self) -> bool:
        """Initialize voice input components."""
        if self.initialized:
            return True
            
        if not check_voice_dependencies():
            logger.warning("Voice dependencies not available - voice input disabled")
            return False
            
        try:
            # Import here to avoid errors when dependencies aren't available
            import pvporcupine
            import pvcobra
            from pvrecorder import PvRecorder
            
            # Check required environment variables
            access_key = os.environ.get("ACCESS_KEY")
            wake_word_path = os.environ.get("WAKE_WORD_MODEL_PATH")
            whisper_model = os.environ.get("WHISPER_MODEL", "tiny.en")
            
            # Auto-detect platform for wake word model if path contains platform-specific name
            if wake_word_path and ("windows" in wake_word_path.lower() or "linux" in wake_word_path.lower()):
                import platform
                current_platform = platform.system().lower()
                if current_platform == "linux" and "windows" in wake_word_path.lower():
                    # Try to find Linux version
                    linux_path = wake_word_path.replace("windows", "linux")
                    if os.path.exists(linux_path):
                        logger.info(f"🔄 Switching from Windows to Linux wake word model: {linux_path}")
                        wake_word_path = linux_path
                elif current_platform == "windows" and "linux" in wake_word_path.lower():
                    # Try to find Windows version  
                    windows_path = wake_word_path.replace("linux", "windows")
                    if os.path.exists(windows_path):
                        logger.info(f"🔄 Switching from Linux to Windows wake word model: {windows_path}")
                        wake_word_path = windows_path
            
            if not access_key:
                logger.error("ACCESS_KEY not set in environment")
                return False
                
            if not wake_word_path:
                logger.error("WAKE_WORD_MODEL_PATH not set in environment")
                return False
            
            # Initialize components
            logger.info("🎤 Initializing voice input components...")
            
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[wake_word_path],
            )
            
            self.cobra = pvcobra.create(access_key=access_key)
            
            self.recorder = PvRecorder(device_index=-1, frame_length=512)
            
            self.transcriber = VoiceTranscriber(whisper_model)
            
            self.initialized = True
            logger.info("✅ Voice input components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize voice input: {e}")
            return False
    
    def get_voice_input(self, prompt: str = "Designer> ") -> Optional[str]:
        """Get voice input similar to input() function."""
        if not self.initialize():
            return None
            
        try:
            print(f"\n{prompt}🎤 Say your wake word to start speaking...")
            
            # Voice input parameters
            sample_rate = 16000
            vad_sensitivity = float(os.environ.get("VAD_SENSITIVITY", "0.4"))  # Lower = less sensitive
            max_window_secs = 15  # Maximum recording time (increased)
            min_recording_secs = 2  # Minimum recording time before VAD can stop
            window_size = sample_rate * max_window_secs
            min_samples = sample_rate * min_recording_secs
            
            samples = deque(maxlen=(window_size * 6))
            vad_samples = deque(maxlen=50)  # Larger buffer for more stable VAD
            is_recording = False
            recording_start_time = None
            
            self.recorder.start()
            
            try:
                while True:
                    data = self.recorder.read()
                    vad_prob = self.cobra.process(data)
                    vad_samples.append(vad_prob)
                    
                    # Check for wake word
                    if self.porcupine.process(data) >= 0:
                        print("🔊 Wake word detected! Speak your command now...")
                        print("📢 Keep speaking... (I'll wait for you to finish)")
                        is_recording = True
                        recording_start_time = time.time()
                        samples.clear()
                        vad_samples.clear()
                    
                    if is_recording:
                        samples.extend(data)
                        current_time = time.time()
                        recording_duration = current_time - recording_start_time
                        
                        # Show progress every second
                        if int(recording_duration) != int(recording_duration - 0.5):
                            print(f"🎙️ Recording... ({recording_duration:.1f}s)")
                        
                        # Check if we should stop recording
                        import numpy as np
                        
                        # More conservative stopping conditions
                        max_time_reached = len(samples) >= window_size
                        min_time_passed = len(samples) >= min_samples
                        vad_buffer_full = len(vad_samples) >= 50
                        silence_detected = vad_buffer_full and np.mean(vad_samples) < vad_sensitivity
                        
                        if max_time_reached or (min_time_passed and silence_detected):
                            
                            print("🔄 Processing your speech...")
                            text = self.transcriber.transcribe(samples)
                            
                            if text and text != "speech not detected" and text != "transcription failed":
                                print(f"✅ Voice command: '{text}'")
                                return text
                            else:
                                print("❌ No speech detected, please try again...")
                                is_recording = False
                                samples.clear()
                                print(f"{prompt}🎤 Say your wake word to start speaking...")
                                
            except KeyboardInterrupt:
                print("\n⏹️  Voice input cancelled")
                # Re-raise the KeyboardInterrupt to let the main loop handle it properly
                raise
                
            finally:
                self.recorder.stop()
                
        except Exception as e:
            logger.error(f"Voice input error: {e}")
            print(f"❌ Voice input failed: {e}")
            return None
    
    def cleanup(self):
        """Clean up voice input resources."""
        try:
            if self.recorder:
                self.recorder.delete()
            if self.porcupine:
                self.porcupine.delete()
            if self.cobra:
                self.cobra.delete()
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")


def get_user_input(prompt: str = "Designer> ", voice_enabled: bool = False) -> str:
    """Get user input via voice or keyboard.
    
    Args:
        prompt: The prompt to show the user
        voice_enabled: Whether to use voice input
        
    Returns:
        User input as string
    """
    if voice_enabled and check_voice_dependencies():
        # Try voice input first
        voice_bridge = VoiceInputBridge()
        try:
            voice_input = voice_bridge.get_voice_input(prompt)
            voice_bridge.cleanup()
            
            if voice_input:
                return voice_input
            else:
                # Fallback to keyboard input
                print(f"Falling back to keyboard input...")
                return input(f"\n{prompt}").strip()
        except KeyboardInterrupt:
            # Clean up voice resources before re-raising
            voice_bridge.cleanup()
            raise
    else:
        # Standard keyboard input
        if voice_enabled:
            logger.warning("Voice input requested but dependencies not available - using keyboard")
        try:
            return input(f"\n{prompt}").strip()
        except EOFError:
            # Input stream closed (e.g., when process is terminated)
            logger.debug("EOFError in input - stream closed")
            raise  # Re-raise to be handled by caller