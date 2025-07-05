#!/usr/bin/env python3
"""
Retry failed segments
"""

import os
import wave
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Save PCM audio data to a wave file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def generate_single_line(text, voice_name, output_file):
    """Generate TTS for a single line"""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    response = client.models.generate_content(
        model="gemini-2.5-pro-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name,
                    )
                )
            ),
        )
    )
    
    data = response.candidates[0].content.parts[0].inline_data.data
    wave_file(output_file, data)
    print(f"Generated: {output_file}")

# Retry the failed segments
segments = [
    ("WORKER", "Sulafat", "15_worker_okay_fabrication.wav", 
     "Okay! Let's do this."),
    
    ("ROBOT", "Gacrux", "16_robot_fetch_beam_fabrication.wav", 
     "Could you fetch me a fifty centimeter beam?")
]

for speaker, voice, filename, text in segments:
    output_path = os.path.join("voices", filename)
    try:
        generate_single_line(text, voice, output_path)
        time.sleep(1)  # Small delay between requests
    except Exception as e:
        print(f"Error generating {filename}: {e}")