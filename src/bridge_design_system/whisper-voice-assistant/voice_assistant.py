import time
from collections import deque
import os
import io
import wave
from dotenv import load_dotenv

import numpy as np
import pvporcupine
import pvcobra
import whisper
from pvrecorder import PvRecorder
import torch
from openai import OpenAI

load_dotenv()

# Handle relative paths by making them relative to this script's directory
import pathlib
script_dir = pathlib.Path(__file__).parent
wake_word_path = os.environ.get("WAKE_WORD_MODEL_PATH")
if wake_word_path and not os.path.isabs(wake_word_path):
    wake_word_path = str(script_dir / wake_word_path)

porcupine = pvporcupine.create(
    access_key=os.environ.get("ACCESS_KEY"),
    keyword_paths=[wake_word_path],
)

cobra = pvcobra.create(
    access_key=os.environ.get("ACCESS_KEY"),
)

recoder = PvRecorder(device_index=-1, frame_length=512)

# frame length = 512
# samples per frame = 16,000
# 1 sec = 16,000 / 512


class Transcriber:
    def __init__(self, model) -> None:
        self.use_openai_api = os.environ.get("USE_OPENAI_API", "false").lower() == "true"
        self.prompts = os.environ.get("WHISPER_INITIAL_PROMPT", "")
        
        if self.use_openai_api:
            print("Using OpenAI API for transcription")
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            self.model = None
        else:
            print("loading local model")
            # TODO: put model on GPU
            self.model = whisper.load_model(model)
            print("loading model finished")
            self.client = None
        
        print(f"Using prompts: {self.prompts}")

    def transcribe(self, frames):
        transcribe_start = time.time()
        
        if self.use_openai_api:
            return self._transcribe_with_api(frames)
        else:
            return self._transcribe_locally(frames)
    
    def _transcribe_locally(self, frames):
        samples = np.array(frames, np.int16).flatten().astype(np.float32) / 32768.0

        result = self.model.transcribe(
            audio=samples,
            language="en",
            fp16=False,
            initial_prompt=self.prompts,
        )

        return result.get("text", "speech not detected")
    
    def _transcribe_with_api(self, frames):
        try:
            # Convert frames to WAV format for OpenAI API
            samples = np.array(frames, np.int16).flatten()
            
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
            
            return transcript.text if transcript.text.strip() else "speech not detected"
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "transcription failed"


def main():
    transcriber = Transcriber(os.environ.get("WHISPER_MODEL"))

    sample_rate = 16000
    frame_size = 512
    vad_mean_probability_sensitivity = float(os.environ.get("VAD_SENSITIVITY"))

    try:
        recoder.start()

        max_window_in_secs = 3
        window_size = sample_rate * max_window_in_secs
        samples = deque(maxlen=(window_size * 6))
        vad_samples = deque(maxlen=25)
        is_recording = False

        while True:
            data = recoder.read()
            vad_prob = cobra.process(data)
            vad_samples.append(vad_prob)
            # print(f"{vad_prob} - {np.mean(vad_samples)} - {len(vad_samples)}")
            if porcupine.process(data) >= 0:
                print(f"Detected wakeword")
                is_recording = True
                samples.clear()

            if is_recording:
                if (
                    len(samples) < window_size
                    or np.mean(vad_samples) >= vad_mean_probability_sensitivity
                ):
                    samples.extend(data)
                    print(f"listening - samples: {len(samples)}")
                else:
                    print("is_recording: False")
                    print(transcriber.transcribe(samples))
                    is_recording = False
    except KeyboardInterrupt:
        recoder.stop()
    finally:
        porcupine.delete()
        recoder.delete()
        cobra.delete()

if __name__ == "__main__":
    main()
