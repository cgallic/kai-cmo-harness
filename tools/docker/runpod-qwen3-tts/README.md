# Qwen3-TTS RunPod Serverless Worker

Generate speech from text with built-in voices, emotion control, and voice cloning.

## Features

- 9 built-in speakers (English, Chinese, Japanese, Korean)
- Natural-language emotion/style control via `instruct`
- Voice cloning from reference audio
- WAV and MP3 output
- R2 integration for result storage

## Build

```bash
# Build image
docker build -t video-toolkit-qwen3-tts .

# Tag for GHCR
docker tag video-toolkit-qwen3-tts ghcr.io/conalmullan/video-toolkit-qwen3-tts:latest

# Push to registry
docker push ghcr.io/conalmullan/video-toolkit-qwen3-tts:latest
```

## Deploy on RunPod

1. Create a new serverless template with:
   - Image: `ghcr.io/conalmullan/video-toolkit-qwen3-tts:latest`
   - Container disk: 30GB
   - GPU: RTX 4090 24GB recommended (both models fit in ~12GB VRAM)

2. Create endpoint from template

3. Note the endpoint ID

Or use the automated setup:
```bash
python tools/qwen3_tts.py --setup
```

## API

### Input

```json
{
  "input": {
    "text": "Hello, how are you today?",
    "mode": "custom_voice",
    "speaker": "Ryan",
    "language": "English",
    "instruct": "Speak warmly and enthusiastically",
    "output_format": "mp3",
    "r2": {
      "endpoint_url": "https://...",
      "access_key_id": "...",
      "secret_access_key": "...",
      "bucket_name": "..."
    }
  }
}
```

### Modes

**CustomVoice** (default) — Use built-in speakers with optional emotion control:
- `speaker` — Speaker name (default: "Ryan")
- `instruct` — Natural-language style instruction (optional, e.g., "Speak sadly")

**Clone** — Clone a voice from reference audio:
- `ref_audio_url` or `ref_audio_base64` — Reference audio
- `ref_text` — Transcript of reference audio (required)

### Options

- `language` — Language hint: Auto (default), English, Chinese, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish
- `output_format` — "mp3" (default) or "wav"

### Built-in Speakers

| Speaker | Language |
|---------|----------|
| Ryan | English |
| Aiden | English |
| Vivian | Chinese |
| Serena | Chinese |
| Uncle_Fu | Chinese |
| Dylan | Chinese |
| Eric | Chinese |
| Ono_Anna | Japanese |
| Sohee | Korean |

### Output

```json
{
  "success": true,
  "audio_url": "https://presigned-r2-url...",
  "r2_key": "qwen3-tts/results/job_xxx.mp3",
  "duration_seconds": 3.5,
  "mode": "custom_voice",
  "processing_time_seconds": 8.2
}
```

## Cost Estimates

| Text Length | Processing Time | Cost (RTX 4090) |
|-------------|-----------------|-----------------|
| 1 sentence  | ~5-10s          | ~$0.005         |
| 1 paragraph | ~15-30s         | ~$0.01-0.02     |
| 1 page      | ~1-2 min        | ~$0.05-0.10     |

First request includes model loading (~30s warm-up).

## Local Testing

```bash
# Run container with GPU
docker run --gpus all -p 8000:8000 video-toolkit-qwen3-tts

# Test CustomVoice mode
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Hello, this is a test of Qwen3 text to speech.",
      "speaker": "Ryan",
      "language": "English"
    }
  }'

# Test Clone mode
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "This should sound like the reference speaker.",
      "mode": "clone",
      "ref_audio_url": "https://example.com/reference.wav",
      "ref_text": "Transcript of the reference audio.",
      "language": "English"
    }
  }'
```
