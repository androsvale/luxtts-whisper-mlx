#!/bin/bash
# STT Example - Transcribe audio with Whisper MLX

# Test STT with your recorded voice
curl -X POST http://192.168.86.29:8000/v1/audio/transcriptions \
  -F "file=@/Users/$(whoami)/voices/default_voice.wav" \
  -F "language=en"

# Or transcribe any audio file:
# curl -X POST http://192.168.86.29:8000/v1/audio/transcriptions \
#   -F "file=@/path/to/your/audio.wav" \
#   -F "language=en"
