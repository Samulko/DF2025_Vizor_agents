# Speech Transcription Module - Integration Guide

## Overview

This module provides a complete, modular speech detection and transcription system that can be integrated into any Python application. It combines:

- **Wake Word Detection** (Picovoice Porcupine)
- **Voice Activity Detection** (Picovoice Cobra) 
- **Speech Transcription** (OpenAI Whisper)
- **Audio Recording** (PvRecorder)

## Quick Integration

### 1. Install Dependencies
```bash
pip install openai-whisper torch torchaudio numpy pvporcupine pvcobra pvrecorder pyaudio scipy python-dotenv
```

### 2. Required Files
Copy these files to your project:
- `speech_transcription_module.py` (main module)
- `models/hello-mave_en_windows_v3_0_0.ppn` (your wake word model)
- `.env` (configuration file)

### 3. Basic Integration
```python
from speech_transcription_module import SpeechDetectionEngine, create_config_from_env

def handle_voice_command(text: str):
    print(f"User said: {text}")
    # Process the command in your application

# Setup
config = create_config_from_env()
engine = SpeechDetectionEngine(config)
engine.set_callbacks(on_transcription_ready=handle_voice_command)

# Start listening in background
thread = engine.start_listening_async()

# Your app continues running...
```

## Configuration

### Environment Variables (.env)
```env
ACCESS_KEY=your_picovoice_api_key_here
WAKE_WORD_MODEL_PATH=models/hello-mave_en_windows_v3_0_0.ppn
WHISPER_MODEL=tiny.en
WHISPER_INITIAL_PROMPT=
VAD_SENSITIVITY=0.7
```

### Whisper Models (choose based on your needs)
| Model | Size | Speed | Accuracy | VRAM |
|-------|------|-------|----------|------|
| tiny.en | 39M | Fastest | Basic | ~1GB |
| base.en | 74M | Fast | Good | ~1GB |  
| small.en | 244M | Medium | Better | ~2GB |
| medium.en | 769M | Slow | Best | ~5GB |

## Advanced Integration Examples

### Web Application Integration
```python
from flask import Flask, jsonify
from speech_transcription_module import SpeechDetectionEngine, create_config_from_env
import threading

app = Flask(__name__)
latest_transcription = ""

def update_transcription(text: str):
    global latest_transcription
    latest_transcription = text
    print(f"New transcription: {text}")

@app.route('/latest_speech')
def get_latest_speech():
    return jsonify({"text": latest_transcription})

if __name__ == "__main__":
    # Start speech engine in background
    config = create_config_from_env()
    engine = SpeechDetectionEngine(config)
    engine.set_callbacks(on_transcription_ready=update_transcription)
    
    speech_thread = engine.start_listening_async()
    
    # Start web server
    app.run(host='0.0.0.0', port=5000)
```

### GUI Application Integration
```python
import tkinter as tk
from speech_transcription_module import SpeechDetectionEngine, create_config_from_env

class VoiceApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Assistant")
        
        self.text_display = tk.Text(self.root, width=60, height=20)
        self.text_display.pack()
        
        self.status_label = tk.Label(self.root, text="Ready...")
        self.status_label.pack()
        
        # Setup speech engine
        config = create_config_from_env()
        self.engine = SpeechDetectionEngine(config)
        self.engine.set_callbacks(
            on_wake_word_detected=self.on_wake_word,
            on_transcription_ready=self.on_transcription
        )
        
        # Start speech detection
        self.speech_thread = self.engine.start_listening_async()
    
    def on_wake_word(self):
        self.status_label.config(text="Listening...")
    
    def on_transcription(self, text: str):
        self.text_display.insert(tk.END, f"You said: {text}\n")
        self.text_display.see(tk.END)
        self.status_label.config(text="Ready...")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = VoiceApp()
    app.run()
```

### Command Processing Integration
```python
import re
from speech_transcription_module import SpeechDetectionEngine, create_config_from_env

class VoiceCommandProcessor:
    def __init__(self):
        self.commands = {
            r"open (.+)": self.open_application,
            r"search for (.+)": self.web_search,
            r"what time is it": self.get_time,
            r"weather": self.get_weather,
        }
    
    def process_voice_command(self, text: str):
        text = text.lower().strip()
        print(f"Processing: '{text}'")
        
        for pattern, handler in self.commands.items():
            match = re.search(pattern, text)
            if match:
                handler(match)
                return
        
        print(f"Unknown command: {text}")
    
    def open_application(self, match):
        app_name = match.group(1)
        print(f"Opening {app_name}")
        # os.system(f"start {app_name}")  # Windows
    
    def web_search(self, match):
        query = match.group(1)
        print(f"Searching for: {query}")
        # webbrowser.open(f"https://google.com/search?q={query}")
    
    def get_time(self, match):
        from datetime import datetime
        current_time = datetime.now().strftime("%I:%M %p")
        print(f"Current time is {current_time}")
    
    def get_weather(self, match):
        print("Getting weather information...")
        # Integrate with weather API

if __name__ == "__main__":
    processor = VoiceCommandProcessor()
    
    config = create_config_from_env()
    engine = SpeechDetectionEngine(config)
    engine.set_callbacks(on_transcription_ready=processor.process_voice_command)
    
    print("Voice command processor ready!")
    engine.start_listening()
```

## Platform-Specific Setup

### Windows
- Install Visual Studio Build Tools for PyAudio
- Use Windows-specific .ppn wake word models
- May need to run as administrator for microphone access

### Linux
- Install ALSA development headers: `sudo apt-get install libasound2-dev`
- Use Linux-specific .ppn wake word models
- May need to configure PulseAudio permissions

### macOS  
- Install Xcode command line tools
- Use macOS-specific .ppn wake word models
- Grant microphone permissions in System Preferences

## Performance Optimization

### GPU Acceleration
```python
# Use CUDA if available
config = SpeechTranscriptionConfig(
    # ... other settings
    whisper_model="base.en"  # Larger models benefit more from GPU
)

# Check if CUDA is available
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
```

### Memory Management
```python
# For memory-constrained environments
config = SpeechTranscriptionConfig(
    whisper_model="tiny.en",  # Smallest model
    max_recording_seconds=10,  # Shorter recordings
    vad_sensitivity=0.8       # More aggressive VAD
)
```

## Troubleshooting

### Common Issues

1. **"Couldn't find keyword file"**
   - Ensure .ppn file exists in models/ directory
   - Check WAKE_WORD_MODEL_PATH in .env file
   - Verify .ppn file is for correct platform

2. **"ModuleNotFoundError: No module named 'dotenv'"**
   - Install: `pip install python-dotenv`

3. **PyAudio installation fails**
   - Windows: Install Visual Studio Build Tools
   - Ubuntu: `sudo apt-get install python3-pyaudio`
   - macOS: `brew install portaudio && pip install pyaudio`

4. **No microphone detected**
   - Check device permissions
   - Try different device_index values (-1, 0, 1, 2...)
   - List available devices with PyAudio

5. **Slow transcription**
   - Use smaller Whisper model (tiny.en vs medium.en)
   - Enable GPU acceleration if available
   - Reduce max_recording_seconds

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
engine = SpeechDetectionEngine(config)
if engine.initialize_components():
    print("All components working!")
else:
    print("Component initialization failed")
```

## Security Considerations

1. **API Keys**: Never commit .env files to version control
2. **Audio Data**: Consider local-only processing for sensitive audio
3. **Network**: Whisper runs locally, but Picovoice services may phone home
4. **Permissions**: Request microphone permissions appropriately

## License & Attribution

Based on the whisper-voice-assistant project by Andy Garbett.
Uses OpenAI Whisper and Picovoice services.