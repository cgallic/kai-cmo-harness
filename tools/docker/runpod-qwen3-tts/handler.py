#!/usr/bin/env python3
"""
RunPod serverless handler for Qwen3-TTS.
Generates speech from text with built-in voices, emotion control, and voice cloning.

Input format:
{
    "input": {
        # Required
        "text": str,                    # Text to synthesize

        # Voice selection (one mode):
        # Mode 1: CustomVoice (built-in speakers)
        "mode": "custom_voice",         # Default mode
        "speaker": str,                 # Speaker name (default: "Ryan")
        "instruct": str,               # Emotion/style instruction (optional)

        # Mode 2: Clone (reference audio)
        "mode": "clone",
        "ref_audio_url": str,           # URL to reference audio
        "ref_audio_base64": str,        # Or base64 encoded reference audio
        "ref_text": str,                # Transcript of reference audio (required)

        # Options
        "language": str,                # Language hint (default: "Auto")
        "output_format": str,           # "mp3" (default) or "wav"
        "temperature": float,          # Expressiveness (default: 0.7, range: 0.3-1.5)
        "top_p": float,                # Nucleus sampling (default: 0.8, range: 0.1-1.0)

        # R2 config for result upload
        "r2": {
            "endpoint_url": str,
            "access_key_id": str,
            "secret_access_key": str,
            "bucket_name": str
        }
    }
}

Output format:
{
    "success": true,
    "audio_base64": str,            # Base64 encoded audio (if no R2)
    "audio_url": str,               # Presigned R2 URL (if R2 config provided)
    "r2_key": str,                  # R2 object key
    "duration_seconds": float,
    "mode": str,                    # "custom_voice" or "clone"
    "processing_time_seconds": float
}
"""

import base64
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

import runpod
import requests
import soundfile as sf

# Lazy-loaded global models (kept in GPU memory between requests)
_custom_voice_model = None
_base_model = None


def log(message: str) -> None:
    """Log message to stderr (visible in RunPod logs)."""
    print(message, file=sys.stderr, flush=True)


def get_custom_voice_model():
    """Lazy-load CustomVoice model (built-in speakers + instruct)."""
    global _custom_voice_model
    if _custom_voice_model is None:
        import torch
        from qwen_tts import Qwen3TTSModel

        log("Loading CustomVoice model...")
        _custom_voice_model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device_map="cuda:0",
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )
        log("CustomVoice model loaded")
    return _custom_voice_model


def get_base_model():
    """Lazy-load Base model (voice cloning)."""
    global _base_model
    if _base_model is None:
        import torch
        from qwen_tts import Qwen3TTSModel

        log("Loading Base model...")
        _base_model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map="cuda:0",
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )
        log("Base model loaded")
    return _base_model


def download_file(url: str, output_path: Path, timeout: int = 300) -> bool:
    """Download file from URL to local path."""
    try:
        log(f"Downloading from {url[:80]}...")
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        log(f"  Downloaded: {output_path.name} ({output_path.stat().st_size // 1024}KB)")
        return True
    except Exception as e:
        log(f"Download error: {e}")
        return False


def decode_base64_file(data: str, output_path: Path) -> bool:
    """Decode base64 data and write to file."""
    try:
        if "," in data:
            data = data.split(",", 1)[1]

        decoded = base64.b64decode(data)
        output_path.write_bytes(decoded)
        log(f"Decoded base64 to {output_path.name} ({len(decoded) // 1024}KB)")
        return True
    except Exception as e:
        log(f"Base64 decode error: {e}")
        return False


def encode_file_base64(file_path: Path) -> str:
    """Encode file to base64 string."""
    return base64.b64encode(file_path.read_bytes()).decode("utf-8")


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(result.stdout.strip())
    except Exception as e:
        log(f"Error getting audio duration: {e}")
        return 0.0


def wav_to_mp3(wav_path: Path, mp3_path: Path) -> bool:
    """Convert WAV to MP3 using ffmpeg."""
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(wav_path),
                "-codec:a", "libmp3lame",
                "-b:a", "192k",
                str(mp3_path),
            ],
            capture_output=True,
            timeout=120,
            check=True,
        )
        return mp3_path.exists()
    except Exception as e:
        log(f"WAV to MP3 conversion error: {e}")
        return False


def generate_custom_voice(text: str, speaker: str, language: str, instruct: str = "", **kwargs) -> tuple:
    """Generate audio using CustomVoice model (built-in speakers)."""
    model = get_custom_voice_model()

    gen_kwargs = {
        "text": text,
        "language": language,
        "speaker": speaker,
    }
    if instruct:
        gen_kwargs["instruct"] = instruct
    if kwargs:
        gen_kwargs.update(kwargs)

    wavs, sr = model.generate_custom_voice(**gen_kwargs)
    return wavs[0], sr


def generate_clone_voice(text: str, language: str, ref_audio_path: Path, ref_text: str, **kwargs) -> tuple:
    """Generate audio using Base model (voice cloning)."""
    model = get_base_model()

    prompt = model.create_voice_clone_prompt(
        ref_audio=str(ref_audio_path),
        ref_text=ref_text,
    )

    gen_kwargs = {
        "text": text,
        "language": language,
        "voice_clone_prompt": prompt,
    }
    if kwargs:
        gen_kwargs.update(kwargs)

    wavs, sr = model.generate_voice_clone(**gen_kwargs)
    return wavs[0], sr


def upload_to_r2(file_path: Path, job_id: str, r2_config: dict, content_type: str = "audio/mpeg") -> tuple[Optional[str], Optional[str]]:
    """Upload audio to Cloudflare R2 and return (presigned_url, object_key)."""
    try:
        import boto3
        from botocore.config import Config

        log("Uploading to R2...")

        client = boto3.client(
            "s3",
            endpoint_url=r2_config["endpoint_url"],
            aws_access_key_id=r2_config["access_key_id"],
            aws_secret_access_key=r2_config["secret_access_key"],
            config=Config(signature_version="s3v4"),
        )

        ext = file_path.suffix
        object_key = f"qwen3-tts/results/{job_id}_{uuid.uuid4().hex[:8]}{ext}"

        client.upload_file(
            str(file_path),
            r2_config["bucket_name"],
            object_key,
            ExtraArgs={"ContentType": content_type},
        )

        presigned_url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": r2_config["bucket_name"], "Key": object_key},
            ExpiresIn=7200,
        )

        log(f"  R2 upload complete: {object_key}")
        return presigned_url, object_key
    except Exception as e:
        log(f"Error uploading to R2: {e}")
        return None, None


def handler(job: dict) -> dict:
    """Main RunPod handler for Qwen3-TTS."""
    job_id = job.get("id", "unknown")
    job_input = job.get("input", {})
    start_time = time.time()

    log(f"Job {job_id}: Starting Qwen3-TTS")

    # Validate required input
    text = job_input.get("text")
    if not text:
        return {"error": "Missing required field: text"}

    # Options
    mode = job_input.get("mode", "custom_voice")
    language = job_input.get("language", "Auto")
    output_format = job_input.get("output_format", "mp3")
    r2_config = job_input.get("r2")

    # Generation kwargs (optional)
    gen_kwargs = {}
    if "temperature" in job_input:
        gen_kwargs["temperature"] = float(job_input["temperature"])
    if "top_p" in job_input:
        gen_kwargs["top_p"] = float(job_input["top_p"])

    work_dir = Path(tempfile.mkdtemp(prefix=f"qwen3tts_{job_id}_"))
    log(f"Working directory: {work_dir}")

    try:
        wav_path = work_dir / "output.wav"

        if mode == "clone":
            # Voice cloning mode - need reference audio
            ref_audio_path = work_dir / "ref_audio.wav"
            ref_text = job_input.get("ref_text")

            if not ref_text:
                return {"error": "ref_text is required for clone mode"}

            if job_input.get("ref_audio_url"):
                if not download_file(job_input["ref_audio_url"], ref_audio_path):
                    return {"error": "Failed to download reference audio"}
            elif job_input.get("ref_audio_base64"):
                if not decode_base64_file(job_input["ref_audio_base64"], ref_audio_path):
                    return {"error": "Failed to decode reference audio"}
            else:
                return {"error": "ref_audio_url or ref_audio_base64 required for clone mode"}

            log(f"Generating clone voice (language={language})...")
            audio_data, sr = generate_clone_voice(
                text=text,
                language=language,
                ref_audio_path=ref_audio_path,
                ref_text=ref_text,
                **gen_kwargs,
            )

        else:
            # CustomVoice mode (default)
            speaker = job_input.get("speaker", "Ryan")
            instruct = job_input.get("instruct", "")

            log(f"Generating custom voice (speaker={speaker}, language={language})...")
            audio_data, sr = generate_custom_voice(
                text=text,
                speaker=speaker,
                language=language,
                instruct=instruct,
                **gen_kwargs,
            )

        # Write WAV
        sf.write(str(wav_path), audio_data, sr)
        log(f"WAV generated: {wav_path.stat().st_size // 1024}KB")

        # Convert to output format
        if output_format == "mp3":
            output_path = work_dir / "output.mp3"
            if not wav_to_mp3(wav_path, output_path):
                return {"error": "Failed to convert WAV to MP3"}
            content_type = "audio/mpeg"
        else:
            output_path = wav_path
            content_type = "audio/wav"

        duration = get_audio_duration(output_path)
        elapsed = time.time() - start_time

        log(f"Output: {output_path.name} ({output_path.stat().st_size // 1024}KB, {duration:.1f}s)")

        result = {
            "success": True,
            "duration_seconds": round(duration, 2),
            "mode": mode,
            "processing_time_seconds": round(elapsed, 2),
        }

        # Upload to R2 if configured
        if r2_config:
            url, r2_key = upload_to_r2(output_path, job_id, r2_config, content_type)
            if url:
                result["audio_url"] = url
                result["r2_key"] = r2_key
            else:
                return {"error": "Failed to upload to R2"}
        else:
            result["audio_base64"] = encode_file_base64(output_path)
            log("Warning: Returning audio as base64 (consider using R2)")

        return result

    except Exception as e:
        import traceback
        log(f"Handler exception: {e}")
        log(traceback.format_exc())
        return {"error": f"Internal error: {str(e)}"}
    finally:
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
            log("Cleaned up working directory")
        except Exception:
            pass


# RunPod serverless entry point
if __name__ == "__main__":
    log("Starting RunPod Qwen3-TTS handler...")

    # Check CUDA
    try:
        import torch
        if torch.cuda.is_available():
            log(f"CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            log("WARNING: CUDA not available!")
    except ImportError:
        log("Warning: torch not imported for CUDA check")

    runpod.serverless.start({"handler": handler})
