# Voice Samples Directory

Place your voice samples here for cloning.

## Requirements

- **Format:** WAV (16-bit or 24-bit PCM)
- **Length:** 10-30 seconds
- **Content:** Clear speech, varied sentences
- **Quality:** No background noise, clean audio

## Example

```bash
# Record with QuickTime Player or Voice Memos
# Save as: default_voice.wav
```

## Default Voice

The server looks for `default_voice.wav` as the default voice. You can also use any voice ID:

```bash
curl -d "voice=custom" -d "input=Hello" http://192.168.86.29:8000/v1/audio/speech
# Looks for: voices/custom.wav
```
