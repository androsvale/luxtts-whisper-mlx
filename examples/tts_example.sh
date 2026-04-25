#!/bin/bash
# TTS Example - Generate speech with LuxTTS

# Create output directory
mkdir -p ~/tts-output

# Test TTS (WAV format)
curl -X POST http://192.168.86.29:8000/v1/audio/speech \
  -d "input=Hello, this is a test of LuxTTS with my cloned voice" \
  -d "voice=andros" \
  -d "response_format=wav" \
  --output ~/tts-output/example.wav

# Play it (macOS)
afplay ~/tts-output/example.wav
