#!/usr/bin/env python3
"""
Generate individual audio segments for each line of dialogue
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

def generate_dialogue_segments():
    """Generate individual audio files for each dialogue segment"""
    
    # Define the dialogue segments
    segments = [
        ("WORKER", "Sulafat", "01_worker_hey_mave.wav", 
         "Hey Mave, bridge these two points with an arch"),
        
        ("ROBOT", "Gacrux", "02_robot_sure_arch.wav", 
         "Sure, I generated a curve that represents the arch. Shall I generate a truss to represent the element?"),
        
        ("WORKER", "Sulafat", "03_worker_lets_do.wav", 
         "Let's do something like this."),
        
        ("ROBOT", "Gacrux", "04_robot_sure_truss.wav", 
         "Sure, I can do that, uhmm, I generated a truss element that follows this shape."),
        
        ("WORKER", "Sulafat", "05_worker_enough_material.wav", 
         "Do we have enough material to build it?"),
        
        ("ROBOT", "Gacrux", "06_robot_yes_calculated.wav", 
         "Yes I calculated the cuts and you will have 2 m left over."),
        
        ("WORKER", "Sulafat", "07_worker_adjustment.wav", 
         "Great. I want to make one adjustment. Can we make the edge elements to look like this?"),
        
        ("ROBOT", "Gacrux", "08_robot_how_about.wav", 
         "How about this?"),
        
        ("WORKER", "Sulafat", "09_worker_great_build.wav", 
         "Great, let's build this with my robot!"),
        
        ("ROBOT", "Gacrux", "10_robot_element_exceeding.wav", 
         "There is one element exceeding 80 cm, and the robot cannot place it."),
        
        ("WORKER", "Sulafat", "11_worker_make_shorter.wav", 
         "What if you make this beam shorter and update the connected beams? Can the robot do that?"),
        
        ("ROBOT", "Gacrux", "12_robot_yes_works.wav", 
         "Yes, that works."),
        
        # Fabrication dialogue
        ("WORKER", "Sulafat", "13_worker_hey_build_fabrication.wav", 
         "Hey Mave, Let's Build this"),
        
        ("ROBOT", "Gacrux", "14_robot_alright_place_fabrication.wav", 
         "Alright. I'll place the beams and I need your help screwing them down."),
        
        ("WORKER", "Sulafat", "15_worker_okay_fabrication.wav", 
         "Okay!"),
        
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
    
    print("\nAll segments generated successfully!")
    print(f"Files saved in: {os.path.abspath('voices')}")

if __name__ == "__main__":
    generate_dialogue_segments()