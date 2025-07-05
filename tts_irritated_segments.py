#!/usr/bin/env python3
"""
Generate dialogue segments with irritated robot voice
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

def generate_single_line(text, voice_name, output_file, style_prompt=""):
    """Generate TTS for a single line with optional style prompt"""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Add style prompt if provided
    if style_prompt:
        content = f"{style_prompt}: {text}"
    else:
        content = text
    
    response = client.models.generate_content(
        model="gemini-2.5-pro-preview-tts",
        contents=content,
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

def generate_irritated_segments():
    """Generate dialogue segments with irritated robot"""
    
    # Style prompts for different levels of irritation
    robot_irritated = "Say in an annoyed and irritated tone"
    robot_very_irritated = "Say in a very annoyed, frustrated and exasperated tone"
    robot_resigned = "Say in a resigned, slightly annoyed tone"
    
    segments = [
        ("ROBOT", "Gacrux", "18_robot_already_showed_fabrication.wav", 
         "I already showed you, but here it is again -- FIFTY centimeters.", robot_irritated),
        
        ("WORKER", "Sulafat", "19_worker_there_go_fabrication.wav", 
         "There you go.", ""),
        
        ("ROBOT", "Gacrux", "20_robot_uggh_another_fabrication.wav", 
         "Uggggh. We got another one.", robot_very_irritated),
        
        ("WORKER", "Sulafat", "21_worker_pause_check_fabrication.wav", 
         "Let's pause for a moment. Come to me, I want to check your tool.", ""),
        
        ("ROBOT", "Gacrux", "22_robot_ok_have_to_fabrication.wav", 
         "OK, if I have to...", robot_resigned),
        
        ("WORKER", "Sulafat", "23_worker_ok_continue_fabrication.wav", 
         "OK, let's continue.", ""),
        
        ("ROBOT", "Gacrux", "24_robot_great_forty_fabrication.wav", 
         "Great, could you pass me a FORTY centimeter beam?", robot_irritated),
        
        ("WORKER", "Sulafat", "25_worker_there_go2_fabrication.wav", 
         "There you go", ""),
        
        ("ROBOT", "Gacrux", "26_robot_your_time_fabrication.wav", 
         "Your time to put in the work.", robot_irritated)
    ]
    
    # Create voices directory if it doesn't exist
    os.makedirs("voices", exist_ok=True)
    
    # Generate each segment
    for speaker, voice, filename, text, style in segments:
        output_path = os.path.join("voices", filename)
        try:
            generate_single_line(text, voice, output_path, style)
            time.sleep(1)  # Small delay between requests
        except Exception as e:
            print(f"Error generating {filename}: {e}")
    
    print("\nIrritated robot segments generated successfully!")

if __name__ == "__main__":
    generate_irritated_segments()