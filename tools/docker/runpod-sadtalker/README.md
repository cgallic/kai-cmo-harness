# SadTalker RunPod Serverless Worker

Generate talking head videos from a static image and audio.

## Features

- Animates faces to match audio speech
- GFPGAN face enhancement
- Automatic chunking for long audio (>45s) to prevent drift
- R2 integration for result storage

## Build

```bash
# Build image
docker build -t video-toolkit-sadtalker .

# Tag for GHCR
docker tag video-toolkit-sadtalker ghcr.io/conalmullan/video-toolkit-sadtalker:latest

# Push to registry
docker push ghcr.io/conalmullan/video-toolkit-sadtalker:latest
```

## Deploy on RunPod

1. Create a new serverless template with:
   - Image: `ghcr.io/conalmullan/video-toolkit-sadtalker:latest`
   - Container disk: 20GB
   - GPU: RTX 4090 24GB recommended

2. Create endpoint from template

3. Note the endpoint ID

## API

### Input

```json
{
  "input": {
    "image_url": "https://...",
    "audio_url": "https://...",
    "still_mode": false,
    "enhancer": "gfpgan",
    "preprocess": "crop",
    "size": 256,
    "r2": {
      "endpoint_url": "https://...",
      "access_key_id": "...",
      "secret_access_key": "...",
      "bucket_name": "..."
    }
  }
}
```

**Image input** (one required):
- `image_url` - URL to download image
- `image_base64` - Base64 encoded image

**Audio input** (one required):
- `audio_url` - URL to download audio
- `audio_base64` - Base64 encoded audio

**Options:**
- `still_mode` - Less head movement (default: false)
- `enhancer` - "gfpgan" (default) or "none"
- `preprocess` - "crop" (default), "resize", or "full"
- `size` - Output resolution: 256 (default) or 512
- `expression_scale` - Expression intensity (default: 1.0)
- `pose_style` - Pose variation 0-45 (default: 0)

### Output

```json
{
  "success": true,
  "video_url": "https://presigned-r2-url...",
  "r2_key": "sadtalker/results/job_xxx.mp4",
  "duration_seconds": 120,
  "chunks_processed": 3,
  "processing_time_seconds": 180
}
```

## Chunking

Audio longer than 45 seconds is automatically split into chunks. This prevents the gradual head position drift that occurs with long continuous generation.

Each chunk is processed independently, then concatenated into the final video.

## Image Requirements

- Face should be centered and clearly visible
- 30-70% of frame should be the face
- Neutral expression works best
- PNG or JPG format
- Minimum 256x256 resolution

## Cost Estimates

| Video Length | Chunks | Processing Time | Cost (RTX 4090) |
|--------------|--------|-----------------|-----------------|
| 30 seconds   | 1      | ~1 min          | ~$0.04          |
| 1 minute     | 2      | ~2 min          | ~$0.09          |
| 3 minutes    | 4      | ~6 min          | ~$0.27          |

Processing is roughly 2x realtime after cold start.

## Local Testing

```bash
# Run container with GPU
docker run --gpus all -p 8000:8000 video-toolkit-sadtalker

# Test with curl
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image_base64": "...",
      "audio_base64": "..."
    }
  }'
```
