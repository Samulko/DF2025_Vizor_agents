#!/usr/bin/env python3
"""
Multi-speaker dialogue transcription using Gemini TTS
Transcribes the construction worker and robot dialogue
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

def generate_dialogue():
    """Generate the construction worker and robot dialogue"""
    
    # Initialize client
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # The dialogue to transcribe
    dialogue = """You are team of human and a robot. The human is an expert construction worker. You collaborate together to build a structure together.

The ROBOT is: a calm, experienced team manager who coordinates AI agents and communicates with users. It is a machine that has relaxed, professional tone. Keep responses close to the text I am giving you. Act natural, use human nuances of speech, be witty from time to time.

Human WORKER: You are a calm, experienced construction worker, quite rough from and shaped by your long year experience. You act relaxed and composed. You are quite cool.

WORKER: Hey Mave, bridge these two points with an arch
ROBOT: Sure, I generated a curve that represents the arch. Shall I generate a truss to represent the element?
WORKER: Let's do something like this.
ROBOT: Sure, I can do that, uhmm, I generated a truss element that follows this shape.
WORKER: Do we have enough material to build it?
ROBOT: Yes I calculated the cuts and you will have 2 m left over.
WORKER: Great. I want to make one adjustment. Can we make the edge elements to look like this?
ROBOT: How about this?
WORKER: Great, let's build this with my robot!
ROBOT: There is one element exceeding 80 cm, and the robot cannot place it.
WORKER: What if you make this beam shorter and update the connected beams? Can the robot do that?
ROBOT: Yes, that works."""
    
    # Generate multi-speaker audio
    response = client.models.generate_content(
        model="gemini-2.5-pro-preview-tts",
        contents=dialogue,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker='WORKER',
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name='Sulafat',  # Warm voice
                                )
                            )
                        ),
                        types.SpeakerVoiceConfig(
                            speaker='ROBOT',
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name='Gacrux',  # Mature voice
                                )
                            )
                        ),
                    ]
                )
            )
        )
    )
    
    # Extract and save audio
    data = response.candidates[0].content.parts[0].inline_data.data
    output_file = "construction_dialogue.wav"
    wave_file(output_file, data)
    print(f"Dialogue audio saved to: {output_file}")
    print("\nVoices used:")
    print("- WORKER: Sulafat (warm voice)")
    print("- ROBOT: Gacrux (mature voice)")

if __name__ == "__main__":
    try:
        generate_dialogue()
    except Exception as e:
        print(f"Error generating dialogue: {e}")