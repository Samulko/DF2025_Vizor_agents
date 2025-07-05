#!/usr/bin/env python3
"""
Text-to-Speech Transcriber using Gemini API
Simple script to convert text to speech using Gemini's TTS capabilities
"""

import os
import wave
from google import genai
from google.genai import types
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Save PCM audio data to a wave file"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def text_to_speech(text, voice_name="Kore", output_file="output.wav"):
    """Convert text to speech using Gemini TTS"""
    # Initialize client with API key from environment
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Generate speech
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
    
    # Extract audio data
    data = response.candidates[0].content.parts[0].inline_data.data
    
    # Save to file
    wave_file(output_file, data)
    print(f"Audio saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Convert text to speech using Gemini TTS")
    parser.add_argument("text", help="Text to convert to speech")
    parser.add_argument("-v", "--voice", default="Kore", 
                        choices=["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", 
                                "Orus", "Aoede", "Callirrhoe", "Autonoe", "Enceladus", 
                                "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", 
                                "Algenib", "Rasalgethi", "Laomedeia", "Achernar", 
                                "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", 
                                "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", 
                                "Sulafat"],
                        help="Voice to use for TTS")
    parser.add_argument("-o", "--output", default="output.wav", 
                        help="Output wave file name")
    
    args = parser.parse_args()
    
    try:
        text_to_speech(args.text, args.voice, args.output)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())