# LuxTTS + Whisper MLX Server v1.0.1

OpenAI-compatible TTS/STT server optimized for Apple Silicon (M1/M2/M3).
Runs on host Mac — ~100x realtime TTS with voice cloning + real-time STT.

**Target:** macOS 12.3+ with Apple Silicon  
**Performance:** TTS ~100x realtime, STT real-time  
**License:** MIT (server code), dependencies per upstream

---

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv luxtts-venv
source luxtts-venv/bin/activate

# 2. Install dependencies (see Requirements section)

# 3. Clone LuxTTS
git clone https://github.com/ysharma3501/LuxTTS.git

# 4. Clone and install Linacodec
git clone https://github.com/ysharma3501/Linacodec.git
cd Linacodec && pip install -e . && cd ..

# 5. Place server.py and start
python3 server.py
```

---

## Requirements

### System
- **macOS:** 12.3+ (for Metal Performance Shaders)
- **Hardware:** Apple Silicon (M1/M2/M3)
- **Python:** 3.9+
- **Disk:** ~15GB free (for models)
- **RAM:** 8GB+ recommended

### Python Packages

**Core stack:**
```bash
pip install torch torchvision torchaudio mlx-whisper fastapi uvicorn python-multipart soundfile librosa numpy
```

**LuxTTS dependencies (discovered during installation):**
```bash
pip install safetensors transformers lhotse tensorboard jieba pypinyin cn2an inflect piper_phonemize pydub onnxruntime
```

**Manual install:**
```bash
git clone https://github.com/ysharma3501/Linacodec.git
cd Linacodec && pip install -e .
```

### Voice Sample
For voice cloning, place a 10-30 second WAV file at:
```
~/voices/andros_voice.wav
```

**Requirements:**
- Format: WAV (16-bit or 24-bit PCM)
- Length: 10-30 seconds
- Quality: Clean speech, no background noise

---

## Installation

### Step 1: Prepare Environment

```bash
# Create project directory
mkdir -p ~/luxtts-whisper-server
cd ~/luxtts-whisper-server

# Create virtual environment
python3 -m venv ~/luxtts-venv
source ~/luxtts-venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Dependencies

```bash
# Core packages
pip install torch torchvision torchaudio mlx-whisper fastapi uvicorn python-multipart soundfile librosa numpy

# LuxTTS-specific packages
pip install safetensors transformers lhotse tensorboard jieba pypinyin cn2an inflect piper_phonemize pydub onnxruntime
```

### Step 3: Install Linacodec (Manual)

```bash
cd ~
git clone https://github.com/ysharma3501/Linacodec.git
cd Linacodec
pip install -e .
```

### Step 4: Clone LuxTTS

```bash
cd ~/luxtts-whisper-server
git clone https://github.com/ysharma3501/LuxTTS.git
```

### Step 5: Configure Voice

```bash
mkdir -p ~/voices
# Copy your voice sample:
cp /path/to/your/voice.wav ~/voices/andros_voice.wav
```

### Step 6: Start Server

```bash
cd ~/luxtts-whisper-server
source ~/luxtts-venv/bin/activate
python3 server.py
```

Server will be available at: `http://192.168.86.29:8000`

---

## API Reference

### Text-to-Speech (TTS)

**Endpoint:** `POST /v1/audio/speech`

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `input` | string | Yes | Text to synthesize |
| `voice` | string | Yes | `andros` or `clone:/path/to/voice.wav` |
| `response_format` | string | No | `wav` (default) or `mp3` |
| `speed` | float | No | Speed multiplier (0.5-2.0), default 1.0 |

**Example:**
```bash
curl -X POST http://192.168.86.29:8000/v1/audio/speech \
  -d "input=Hello, this is my cloned voice" \
  -d "voice=andros" \
  -d "response_format=wav" \
  --output speech.wav
```

**Performance:**
- First request: ~30 seconds (model download + voice encoding)
- Subsequent: ~0.5 seconds (voice cached)

---

### Speech-to-Text (STT)

**Endpoint:** `POST /v1/audio/transcriptions`

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | file | Yes | Audio file (WAV) |
| `language` | string | No | Language code (e.g., `en`). Auto-detect if omitted |
| `prompt` | string | No | Optional context hint |

**Example:**
```bash
curl -X POST http://192.168.86.29:8000/v1/audio/transcriptions \
  -F "file=@/path/to/audio.wav" \
  -F "language=en"
```

**Response:**
```json
{
  "text": "Transcribed text here",
  "language": "en"
}
```

**Model:** Uses `mlx_whisper` default (`openai/whisper-base` or `openai/whisper-large-v3` depending on mlx-whisper version). The `model` parameter is accepted for API compatibility but currently uses the default model. For higher accuracy, edit `server.py` to specify `path_or_hf_repo="openai/whisper-large-v3"`.

**Default behavior:** Auto-detects and loads the best available model. First run downloads ~150MB-1.5GB from HuggingFace.

---

### Health Check

**Endpoint:** `GET /health`

**Example:**
```bash
curl http://192.168.86.29:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "luxtts_loaded": true,
  "whisper_available": true,
  "voices_cached": 1
}
```

---

## OpenClaw Integration

This server is **OpenAI-compatible**, making it easy to integrate with OpenClaw as a custom TTS/STT provider.

### As OpenClaw TTS Provider

Configure OpenClaw to use your local server:

**`~/.openclaw/openclaw.json`:**
```json
{
  "agents": {
    "defaults": {
      "tts": {
        "provider": "openai",
        "baseUrl": "http://192.168.86.29:8000/v1",
        "apiKey": "dummy",
        "model": "luxtts",
        "voice": "andros"
      },
      "stt": {
        "provider": "openai",
        "baseUrl": "http://192.168.86.29:8000/v1",
        "apiKey": "dummy",
        "model": "whisper-1"
      }
    }
  }
}
```

### For Talk Mode (Future)

**Architecture for OpenClaw Talk Mode:**

```
OpenClaw (iPad/VM) ←→ WebSocket ←→ Talk Mode Bridge ←→ This Server
                                        ↓
                                   Wyoming Protocol
                                        ↓
                              Local Whisper/Piper
```

**Implementation Plan:**
1. **Phase 1:** Configure OpenClaw to use this server as TTS provider (REST API)
2. **Phase 2:** Create Wyoming Protocol bridge for streaming STT/TTS
3. **Phase 3:** Implement WebSocket handler for real-time audio streaming
4. **Phase 4:** Add VAD (Voice Activity Detection) for interruption handling

**Benefits:**
- **Privacy:** All processing on local Mac, no cloud TTS/STT
- **Speed:** ~100x realtime TTS, real-time STT
- **Quality:** Human-like voice cloning
- **Cost:** Zero API costs

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Client (iPad/VM)                  │
│                       HTTP Requests                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Server (Port 8000)                   │
│  ┌──────────────────┐              ┌──────────────────────┐  │
│  │   POST /v1/      │              │   POST /v1/audio/    │  │
│  │   audio/speech   │─────────────▶│   transcriptions     │  │
│  │                  │              │                      │  │
│  │   LuxTTS TTS     │              │   Whisper MLX STT    │  │
│  │   ~100x realtime │              │   Real-time          │  │
│  │   PyTorch MPS    │              │   MLX optimized      │  │
│  └──────────────────┘              └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
           Apple Silicon GPU      Apple Silicon Neural Engine
           (PyTorch MPS)          (Whisper MLX)
```

---

## Performance

| Task | Speed | Backend | Notes |
|------|-------|---------|-------|
| TTS | ~100x realtime | PyTorch MPS | Apple Silicon GPU |
| STT | Real-time | MLX | Apple Silicon optimized |

**Comparison:**
- LuxTTS: ~10GB disk, premium quality, voice cloning
- Piper TTS: ~500MB disk, good quality, no cloning

---

## Troubleshooting

### "No module named 'X'"

Install the missing package from the Requirements section. Common ones discovered during setup:
- `safetensors`, `transformers`, `lhotse`, `jieba`, `pypinyin`, `cn2an`, `inflect`, `piper_phonemize`, `onnxruntime`

### "MPS device not available"

Update macOS to 12.3+ and ensure you're on Apple Silicon (M1/M2/M3).

### "Voice reference not found"

Ensure your voice file exists in `~/voices/`.  
Example: `~/voices/andros_voice.wav`

**Default voice setup:**
```bash
mkdir -p ~/voices
cp /path/to/your/voice.wav ~/voices/andros_voice.wav
```

**Using a custom voice:**
```bash
curl -X POST http://192.168.86.29:8000/v1/audio/speech \
  -d "input=Hello with custom voice" \
  -d "voice=clone:/path/to/your/custom.wav"
```

### First request is slow

Expected. The first request downloads models from HuggingFace (~1-2GB) and encodes your voice (~30s). Subsequent requests are fast.

### MP3 conversion fails

Ensure `pydub` is installed: `pip install pydub`

---

## Files

```
luxtts-whisper-server/
├── server.py              # This server
├── LuxTTS/                # Cloned repo
│   └── zipvoice/
│       └── luxvoice.py    # Core TTS engine
├── voices/                # Voice samples
│   ├── README.md          # Voice requirements
│   └── SAMPLE_VOICES.md   # Recording prompts
├── tts-output/            # TTS output directory
├── examples/                # Usage examples
│   ├── tts_example.sh
│   └── stt_example.sh
└── install.log            # Installation log

~/voices/
└── andros_voice.wav       # Your voice sample

~/luxtts-venv/             # Virtual environment

~/Linacodec/               # Cloned repo (required)
```

---

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| macOS 12.3+ (Apple Silicon) | ✅ Supported | MPS acceleration |
| macOS (Intel) | ⚠️ CPU only | Would need fallback |
| Linux | ❌ Not supported | Would need PyTorch Whisper |
| Windows | ❌ Not supported | Would need PyTorch Whisper |

---

## Version History

- **v1.0.1** (2026-04-25): Fixed Whisper MLX integration (STT working)
- **v1.0.0** (2026-04-25): Initial release (TTS working)

---

## Credits

- **LuxTTS:** [YatharthS/LuxTTS](https://github.com/ysharma3501/LuxTTS) — Voice cloning TTS
- **Whisper MLX:** [mlx-examples/whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — Apple Silicon STT
- **FastAPI:** [fastapi.tiangolo.com](https://fastapi.tiangolo.com) — Web framework
- **Linacodec:** [ysharma3501/Linacodec](https://github.com/ysharma3501/Linacodec) — Vocoder

---

## License

MIT License — See LICENSE file

**Note:** This project bundles or depends on multiple open-source projects. Please respect their individual licenses.
