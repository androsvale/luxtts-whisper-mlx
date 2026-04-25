#!/usr/bin/env python3
"""
LuxTTS + Whisper MLX Server v1.0.1
OpenAI-compatible TTS/STT API for Apple Silicon
Copyright (c) 2026 Simulacrum.sh / Andros Vale
MIT License — See LICENSE file

Integration by Eidos
Created: 2026-04-25
Updated: 2026-04-25 (fixed Whisper MLX integration)

Architecture:
- FastAPI for HTTP handling
- LuxTTS (PyTorch MPS) for TTS (~100x realtime)
- Whisper MLX for STT (real-time transcription)
- Lazy model loading for fast startup

See AUTHORS file for full credits and upstream project attribution.
"""

import os
import sys
import tempfile
import logging
import signal
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/luxtts-whisper-server/server.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global state
lux_tts = None
voice_cache = {}
server_shutdown = False

# Configuration
LUXTTS_PATH = os.path.expanduser('~/luxtts-whisper-server/LuxTTS')
VOICES_DIR = os.path.expanduser('~/voices')
DEFAULT_VOICE = os.path.join(VOICES_DIR, 'andros_voice.wav')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown."""
    logger.info("Server starting up...")
    # Pre-warm voice cache if default voice exists
    if os.path.exists(DEFAULT_VOICE):
        try:
            logger.info(f"Pre-warming voice cache with {DEFAULT_VOICE}")
            _ = load_luxtts()
            voice_cache[DEFAULT_VOICE] = lux_tts.encode_prompt(DEFAULT_VOICE, rms=0.01)
            logger.info("Voice cache warmed")
        except Exception as e:
            logger.warning(f"Could not pre-warm voice cache: {e}")
    
    yield
    
    # Shutdown
    logger.info("Server shutting down...")
    server_shutdown = True

def load_luxtts():
    """Lazy load LuxTTS model."""
    global lux_tts
    if lux_tts is None:
        logger.info("Loading LuxTTS...")
        sys.path.insert(0, LUXTTS_PATH)
        try:
            from zipvoice.luxvoice import LuxTTS
            import torch
            device = 'mps' if torch.backends.mps.is_available() else 'cpu'
            logger.info(f"Using device: {device}")
            lux_tts = LuxTTS('YatharthS/LuxTTS', device=device)
            logger.info("LuxTTS loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load LuxTTS: {e}")
            raise
    return lux_tts

app = FastAPI(
    title="LuxTTS + Whisper MLX Server",
    version="1.0.1",
    lifespan=lifespan
)

@app.post("/v1/audio/speech")
async def text_to_speech(
    input: str = Form(..., description="Text to synthesize"),
    voice: str = Form("andros", description="Voice ID or 'clone:path'"),
    model: str = Form("luxtts", description="Model name"),
    response_format: str = Form("wav", description="Audio format (wav/mp3)"),
    speed: float = Form(1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
):
    """Convert text to speech using LuxTTS."""
    try:
        logger.info(f"TTS request: voice={voice}, speed={speed}, text_length={len(input)}")
        
        tts = load_luxtts()
        
        # Resolve voice path
        if voice.startswith("clone:"):
            ref_path = voice.replace("clone:", "")
        elif voice == "andros":
            ref_path = DEFAULT_VOICE
        else:
            # Try voices directory
            ref_path = os.path.join(VOICES_DIR, f"{voice}.wav")
        
        if not os.path.exists(ref_path):
            logger.error(f"Voice reference not found: {ref_path}")
            raise HTTPException(400, f"Voice reference not found: {ref_path}. Place voice files in ~/voices/ or use 'clone:/path/to/file.wav'")
        
        # Encode voice if not cached
        if ref_path not in voice_cache:
            logger.info(f"Encoding voice prompt: {ref_path}")
            voice_cache[ref_path] = tts.encode_prompt(ref_path, rms=0.01)
            logger.info("Voice encoded")
        
        encoded_prompt = voice_cache[ref_path]
        
        # Generate speech
        logger.info("Generating speech...")
        final_wav = tts.generate_speech(
            input,
            encoded_prompt,
            num_steps=4,  # Fast mode
            t_shift=0.9,
            speed=speed,
            return_smooth=False
        )
        
        # Convert to audio file
        import soundfile as sf
        import numpy as np
        
        audio_data = final_wav.numpy().squeeze()
        
        with tempfile.NamedTemporaryFile(suffix=f".{response_format}", delete=False) as tmp:
            sf.write(tmp.name, audio_data, 48000)
            tmp_path = tmp.name
            
            # Convert to MP3 if requested
            if response_format == "mp3":
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_wav(tmp.name)
                    mp3_path = tmp.name.replace('.wav', '.mp3')
                    audio.export(mp3_path, format='mp3')
                    tmp_path = mp3_path
                except Exception as e:
                    logger.warning(f"MP3 conversion failed: {e}, returning WAV")
        
        logger.info(f"TTS complete: {tmp_path}")
        
        return FileResponse(
            tmp_path,
            media_type=f"audio/{response_format}",
            headers={"Content-Disposition": f"attachment; filename=speech.{response_format}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS failed: {e}", exc_info=True)
        raise HTTPException(500, f"TTS generation failed: {str(e)}")

@app.post("/v1/audio/transcriptions")
async def speech_to_text(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    model: str = Form("whisper-1", description="Model name"),
    language: Optional[str] = Form(None, description="Language code (auto-detect if None)"),
    prompt: Optional[str] = Form(None, description="Optional prompt for context")
):
    """Transcribe audio using Whisper MLX."""
    try:
        logger.info(f"STT request: language={language}, file={file.filename}")
        
        import mlx_whisper
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcribe using mlx_whisper (defaults to base or large-v3 model)
        logger.info("Transcribing with Whisper MLX...")
        # Default model loaded by mlx_whisper - for specific model use:
        # result = mlx_whisper.transcribe(tmp_path, language=language, path_or_hf_repo="openai/whisper-large-v3")
        result = mlx_whisper.transcribe(tmp_path, language=language)
        
        # Cleanup
        os.unlink(tmp_path)
        
        logger.info(f"STT complete: {len(result['text'])} chars")
        
        return JSONResponse(content={
            "text": result["text"].strip(),
            "language": result.get("language", "unknown")
        })
        
    except Exception as e:
        logger.error(f"STT failed: {e}", exc_info=True)
        raise HTTPException(500, f"Transcription failed: {str(e)}")

@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {"id": "luxtts", "object": "model", "owned_by": "simulacrum"},
            {"id": "whisper-1", "object": "model", "owned_by": "simulacrum"}
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "luxtts_loaded": lux_tts is not None,
        "whisper_available": True,  # Whisper MLX loads on demand
        "voices_cached": len(voice_cache)
    }

@app.get("/")
async def root():
    """Root endpoint with info."""
    return {
        "name": "LuxTTS + Whisper MLX Server",
        "version": "1.0.1",
        "endpoints": {
            "speech": "POST /v1/audio/speech",
            "transcriptions": "POST /v1/audio/transcriptions",
            "models": "GET /v1/models",
            "health": "GET /health"
        }
    }

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("Starting LuxTTS + Whisper MLX Server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
