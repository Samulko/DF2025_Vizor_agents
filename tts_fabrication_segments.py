#!/usr/bin/env python3
"""
Generate fabrication dialogue segments only
"""

import os
import wave
from google import genai
from google.genai import types
from dotenv import load_dotenv

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

def generate_fabrication_segments():
    """Generate fabrication dialogue segments"""
    
    # Fabrication dialogue segments
    segments = [
        ("WORKER", "Sulafat", "13_worker_hey_build_fabrication.wav", 
         "Hey Mave, Let's Build this"),
        
        ("ROBOT", "Gacrux", "14_robot_alright_place_fabrication.wav", 
         "Alright. I'll place the beams and I need your help screwing them down."),
        
        ("WORKER", "Sulafat", "15_worker_okay_fabrication.wav", 
         "Okay! Let's do this."),
        
        ("ROBOT", "Gacrux", "16_robot_fetch_beam_fabrication.wav", 
         "Could you fetch me a 50cm beam?"),
        
        ("WORKER", "Sulafat", "17_worker_which_beam_fabrication.wav", 
         "Which beam?")
    ]
    
    # Create voices directory if it doesn't exist
    os.makedirs("voices", exist_ok=True)
    
    # Generate each segment
    for speaker, voice, filename, text in segments:
        output_path = os.path.join("voices", filename)
        try:
            generate_single_line(text, voice, output_path)
        except Exception as e:
            print(f"Error generating {filename}: {e}")
    
    print("\nFabrication segments generated successfully!")

if __name__ == "__main__":
    generate_fabrication_segments()