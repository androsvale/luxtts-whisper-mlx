#!/bin/bash
# Test script for LuxTTS + Whisper MLX Server

echo "Testing LuxTTS + Whisper MLX Server..."
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
if curl -s http://192.168.86.29:8000/health | grep -q "healthy"; then
    echo "   ✓ Server is healthy"
else
    echo "   ✗ Server not responding"
    echo "   Run: python3 ~/luxtts-whisper-server/server.py"
    exit 1
fi

# Test TTS (if voice exists)
if [ -f "$HOME/voices/andros_voice.wav" ]; then
    echo ""
    echo "2. Testing TTS..."
    curl -s -X POST http://192.168.86.29:8000/v1/audio/speech \
        -d "input=Hello, this is a test" \
        -d "voice=andros" \
        --output /tmp/test-tts.wav
    
    if [ -f "/tmp/test-tts.wav" ] && [ -s "/tmp/test-tts.wav" ]; then
        echo "   ✓ TTS test successful (/tmp/test-tts.wav)"
    else
        echo "   ✗ TTS test failed"
    fi
else
    echo ""
    echo "2. Skipping TTS test (no voice at ~/voices/andros_voice.wav)"
fi

echo ""
echo "Test complete!"
