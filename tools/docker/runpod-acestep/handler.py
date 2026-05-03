#!/usr/bin/env python3
"""
RunPod serverless handler for ACE-Step 1.5 Music Generation.

Supports:
- text2music: Generate music from text prompt + optional lyrics
- cover: Style transfer from reference audio
- extract: Stem extraction (vocals, drums, bass, etc.)

Input format:
{
    "input": {
        "task_type": str,              # "text2music" (default), "cover", "extract"
        "prompt": str,                 # Music description or stem name for extract
        "lyrics": str,                 # Optional lyrics (enables vocals)
        "vocal_language": str,         # Language code (default: "en")
        "audio_duration": int,         # Duration in seconds (10-600, default: 30)
        "bpm": int,                    # Tempo (30-300)
        "key_scale": str,              # Musical key (e.g., "C Major", "Am")
        "time_signature": int,         # Time signature (2, 3, 4, 6)
        "inference_steps": int,        # Denoising steps (default: 8 for turbo)
        "seed": int,                   # Random seed
        "audio_format": str,           # "mp3", "wav", "flac" (default: "mp3")

        # Cover mode
        "reference_audio_base64": str, # Base64 reference audio for cover
        "audio_cover_strength": float, # Cover strength 0.0-1.0 (default: 0.7)

        # Extract mode
        "src_audio_base64": str,       # Base64 source audio for extraction

        # R2 upload
        "r2": dict,                    # Optional R2 config for file transfer
    }
}

Output format:
{
    "success": true,
    "audio_base64": str,               # Base64-encoded audio (if no R2)
    "output_url": str,                 # R2 presigned URL (if R2 configured)
    "seed_value": int,
    "metas": {"bpm": ..., "keyscale": ..., "duration": ..., "timesignature": ...},
    "inference_time_ms": int,
    "actual_duration_seconds": float
}
"""

import base64
import io
import os
import random
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

import runpod
import torch

# --- Logging ---

def log(message: str) -> None:
    """Log message to stderr (visible in RunPod logs)."""
    print(message, file=sys.stderr, flush=True)


# --- Model management ---

_dit_handler = None
_llm_handler = None


def setup_hf_cache() -> None:
    """Set up HuggingFace cache."""
    baked_cache = Path("/root/.cache/huggingface")
    if baked_cache.exists():
        os.environ["HF_HOME"] = str(baked_cache)
        log(f"Using baked-in model cache: {baked_cache}")
    elif Path("/runpod-volume").exists() and os.access("/runpod-volume", os.W_OK):
        cache_path = Path("/runpod-volume/.cache/huggingface")
        cache_path.mkdir(parents=True, exist_ok=True)
        os.environ["HF_HOME"] = str(cache_path)
        log(f"Using RunPod network volume cache: {cache_path}")


def get_dit_handler():
    """Lazy-load the DiT handler."""
    global _dit_handler
    if _dit_handler is None:
        log("Loading ACE-Step DiT model...")
        t0 = time.time()

        from acestep.handler import AceStepHandler
        _dit_handler = AceStepHandler()

        config_path = os.environ.get("ACESTEP_CONFIG_PATH", "acestep-v15-turbo")
        device = os.environ.get("ACESTEP_DEVICE", "cuda")

        _dit_handler.initialize_service(
            project_root="/app/acestep-repo",
            config_path=config_path,
            device=device,
        )

        elapsed = time.time() - t0
        log(f"DiT model loaded in {elapsed:.1f}s")

    return _dit_handler


# --- R2 upload ---

def upload_to_r2(file_path: str, r2_config: dict) -> Optional[str]:
    """Upload file to R2 and return presigned download URL."""
    try:
        import boto3
        from botocore.config import Config

        s3 = boto3.client(
            "s3",
            endpoint_url=r2_config["endpoint_url"],
            aws_access_key_id=r2_config["access_key_id"],
            aws_secret_access_key=r2_config["secret_access_key"],
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

        bucket = r2_config["bucket_name"]
        key = f"acestep/{uuid.uuid4().hex}{Path(file_path).suffix}"

        s3.upload_file(file_path, bucket, key)

        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )

        log(f"Uploaded to R2: {key}")
        return url

    except Exception as e:
        log(f"R2 upload failed: {e}")
        return None


# --- Audio helpers ---

def save_temp_audio(audio_base64: str, suffix: str = ".mp3") -> str:
    """Save base64 audio to a temp file, return path."""
    audio_bytes = base64.b64decode(audio_base64)
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(audio_bytes)
    tmp.close()
    return tmp.name


def get_audio_duration(file_path: str) -> Optional[float]:
    """Get audio duration using torchaudio or ffprobe."""
    try:
        import torchaudio
        info = torchaudio.info(file_path)
        return info.num_frames / info.sample_rate
    except Exception:
        pass

    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", file_path],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass

    return None


# --- Main handler ---

def handler(event: dict) -> dict:
    """RunPod serverless handler for ACE-Step music generation."""
    try:
        input_data = event.get("input", {})
        task_type = input_data.get("task_type", "text2music")
        r2_config = input_data.get("r2")

        log(f"Task: {task_type}")

        dit = get_dit_handler()

        t0 = time.time()

        # Build generation params using ACE-Step's dataclass API
        from acestep.inference import GenerationParams, GenerationConfig, generate_music

        prompt = input_data.get("prompt", "")
        lyrics = input_data.get("lyrics", "")
        duration = float(input_data.get("audio_duration", 30))
        steps = int(input_data.get("inference_steps", 8))
        audio_format = input_data.get("audio_format", "mp3")
        seed = input_data.get("seed")

        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        params = GenerationParams(
            task_type=task_type,
            caption=prompt,
            lyrics=lyrics,
            duration=duration,
            inference_steps=steps,
            seed=seed,
            vocal_language=input_data.get("vocal_language", "unknown"),
        )

        # Musical control
        if input_data.get("bpm"):
            params.bpm = int(input_data["bpm"])
        if input_data.get("key_scale"):
            params.keyscale = input_data["key_scale"]
        if input_data.get("time_signature"):
            params.timesignature = str(input_data["time_signature"])

        # Task-specific params
        if task_type == "cover":
            ref_audio = input_data.get("reference_audio_base64")
            if not ref_audio:
                return {"error": "reference_audio_base64 required for cover task"}
            ref_path = save_temp_audio(ref_audio)
            params.reference_audio = ref_path
            params.audio_cover_strength = float(
                input_data.get("audio_cover_strength", 0.7)
            )

        elif task_type == "extract":
            src_audio = input_data.get("src_audio_base64")
            if not src_audio:
                return {"error": "src_audio_base64 required for extract task"}
            src_path = save_temp_audio(src_audio)
            params.src_audio = src_path

        config = GenerationConfig(
            batch_size=1,
            audio_format=audio_format,
            seeds=[seed],
            use_random_seed=False,
        )

        # Use a temp dir for output
        save_dir = tempfile.mkdtemp(prefix="acestep_")

        # Generate using the high-level API (no LLM handler needed)
        log(f"Generating: {duration}s, {steps} steps, seed={seed}")
        result = generate_music(
            dit_handler=dit,
            llm_handler=None,
            params=params,
            config=config,
            save_dir=save_dir,
        )

        inference_time_ms = int((time.time() - t0) * 1000)

        # Extract output from GenerationResult
        if not result or not result.success or not result.audios:
            error_msg = result.error if result and result.error else 'No audio generated'
            return {"error": str(error_msg)}

        audio_entry = result.audios[0]
        output_path = audio_entry.get("path", "")
        audio_params = audio_entry.get("params", {})
        metas = {
            "bpm": audio_params.get("bpm"),
            "keyscale": audio_params.get("keyscale", audio_params.get("key_scale")),
            "duration": audio_params.get("duration"),
            "timesignature": audio_params.get("timesignature"),
        }
        seed_value = audio_params.get("seed", seed)

        if not output_path or not Path(output_path).exists():
            return {"error": "No output audio file produced"}

        actual_duration = get_audio_duration(output_path)

        # Build response
        response = {
            "success": True,
            "seed_value": seed_value,
            "metas": metas,
            "inference_time_ms": inference_time_ms,
        }

        if actual_duration:
            response["actual_duration_seconds"] = round(actual_duration, 2)

        # Upload or encode
        if r2_config:
            url = upload_to_r2(output_path, r2_config)
            if url:
                response["output_url"] = url
            else:
                # Fall back to base64
                with open(output_path, "rb") as f:
                    response["audio_base64"] = base64.b64encode(f.read()).decode("utf-8")
        else:
            with open(output_path, "rb") as f:
                response["audio_base64"] = base64.b64encode(f.read()).decode("utf-8")

        # Cleanup temp files
        if params.reference_audio and os.path.exists(params.reference_audio):
            try:
                os.unlink(params.reference_audio)
            except OSError:
                pass
        if params.src_audio and os.path.exists(params.src_audio):
            try:
                os.unlink(params.src_audio)
            except OSError:
                pass
        try:
            os.unlink(output_path)
        except OSError:
            pass

        log(f"Done: {inference_time_ms}ms, {actual_duration:.1f}s audio")
        return response

    except Exception as e:
        log(f"Handler error: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {"error": str(e)}


# --- Startup ---

if __name__ == "__main__":
    setup_hf_cache()
    log("ACE-Step 1.5 RunPod handler starting...")
    log(f"PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}")

    # Pre-warm the model
    try:
        get_dit_handler()
        log("Model pre-warmed successfully")
    except Exception as e:
        log(f"Pre-warm failed (will retry on first request): {e}")

    runpod.serverless.start({"handler": handler})
