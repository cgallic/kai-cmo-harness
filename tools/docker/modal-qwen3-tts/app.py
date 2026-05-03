"""
Modal deployment for Qwen3-TTS.

Generates speech from text with built-in voices, emotion control, and voice cloning.
Equivalent to docker/runpod-qwen3-tts/handler.py but deployed on Modal.

Deploy:
    modal deploy docker/modal-qwen3-tts/app.py

Test:
    modal run docker/modal-qwen3-tts/app.py --text "Hello world"

Input format (POST JSON to web endpoint):
{
    "text": str,                    # Required: text to synthesize
    "mode": "custom_voice",         # "custom_voice" (default) or "clone"
    "speaker": "Ryan",              # Speaker name (custom_voice mode)
    "instruct": "",                 # Emotion/style instruction
    "language": "Auto",
    "output_format": "mp3",         # "mp3" or "wav"
    "temperature": 0.7,
    "top_p": 0.8,

    # Clone mode:
    "ref_audio_url": str,           # URL to reference audio
    "ref_audio_base64": str,        # Or base64 encoded reference audio
    "ref_text": str,                # Transcript of reference audio (required)

    # Optional R2 upload:
    "r2": { "endpoint_url": ..., "access_key_id": ..., "secret_access_key": ..., "bucket_name": ... }
}

Output format:
{
    "success": true,
    "audio_base64": str,            # Base64 audio (if no R2)
    "audio_url": str,               # Presigned R2 URL (if R2 configured)
    "r2_key": str,
    "duration_seconds": float,
    "mode": str,
    "processing_time_seconds": float
}
"""

import modal

app = modal.App("video-toolkit-qwen3-tts")

# Container image — mirrors docker/runpod-qwen3-tts/Dockerfile
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "torch==2.4.0",
        "torchaudio==2.4.0",
        "qwen-tts",
        "soundfile",
        "boto3",
        "requests",
        "fastapi[standard]",
    )
    # Bake model weights into the image (avoids cold-start downloads)
    .run_commands(
        'python -c "'
        "from huggingface_hub import snapshot_download; "
        "snapshot_download('Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice'); "
        "snapshot_download('Qwen/Qwen3-TTS-12Hz-1.7B-Base')"
        '"'
    )
)


@app.cls(
    image=image,
    gpu="A10G",
    timeout=300,
    scaledown_window=60,
)
@modal.concurrent(max_inputs=1)
class Qwen3TTS:
    """Qwen3-TTS inference class. Models are loaded once and reused across requests."""

    @modal.enter()
    def load_models(self):
        """Load models when the container starts (equivalent to lazy-load globals in RunPod handler)."""
        import torch
        from qwen_tts import Qwen3TTSModel

        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")

        print("Loading CustomVoice model...")
        self.custom_voice_model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device_map="cuda:0",
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )
        print("CustomVoice model loaded")

        print("Loading Base model...")
        self.base_model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            device_map="cuda:0",
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )
        print("Base model loaded")

    @modal.fastapi_endpoint(method="POST")
    def generate(self, request: dict) -> dict:
        """Web endpoint — accepts same payload format as RunPod handler."""
        import base64
        import shutil
        import subprocess
        import tempfile
        import time
        import uuid
        from pathlib import Path

        import requests as req
        import soundfile as sf

        start_time = time.time()

        # Validate
        text = request.get("text")
        if not text:
            return {"error": "Missing required field: text"}

        mode = request.get("mode", "custom_voice")
        language = request.get("language", "Auto")
        output_format = request.get("output_format", "mp3")
        r2_config = request.get("r2")

        gen_kwargs = {}
        if "temperature" in request:
            gen_kwargs["temperature"] = float(request["temperature"])
        if "top_p" in request:
            gen_kwargs["top_p"] = float(request["top_p"])

        job_id = uuid.uuid4().hex[:12]
        work_dir = Path(tempfile.mkdtemp(prefix=f"qwen3tts_{job_id}_"))

        try:
            wav_path = work_dir / "output.wav"

            if mode == "clone":
                ref_audio_path = work_dir / "ref_audio.wav"
                ref_text = request.get("ref_text")

                if not ref_text:
                    return {"error": "ref_text is required for clone mode"}

                # Download or decode reference audio
                if request.get("ref_audio_url"):
                    resp = req.get(request["ref_audio_url"], timeout=300)
                    resp.raise_for_status()
                    ref_audio_path.write_bytes(resp.content)
                elif request.get("ref_audio_base64"):
                    data = request["ref_audio_base64"]
                    if "," in data:
                        data = data.split(",", 1)[1]
                    ref_audio_path.write_bytes(base64.b64decode(data))
                else:
                    return {"error": "ref_audio_url or ref_audio_base64 required for clone mode"}

                # Generate with voice cloning
                prompt = self.base_model.create_voice_clone_prompt(
                    ref_audio=str(ref_audio_path),
                    ref_text=ref_text,
                )
                wavs, sr = self.base_model.generate_voice_clone(
                    text=text,
                    language=language,
                    voice_clone_prompt=prompt,
                    **gen_kwargs,
                )
                audio_data = wavs[0]

            else:
                # CustomVoice mode
                speaker = request.get("speaker", "Ryan")
                instruct = request.get("instruct", "")

                cv_kwargs = {
                    "text": text,
                    "language": language,
                    "speaker": speaker,
                }
                if instruct:
                    cv_kwargs["instruct"] = instruct
                cv_kwargs.update(gen_kwargs)

                wavs, sr = self.custom_voice_model.generate_custom_voice(**cv_kwargs)
                audio_data = wavs[0]

            # Write WAV
            sf.write(str(wav_path), audio_data, sr)

            # Convert to output format
            if output_format == "mp3":
                output_path = work_dir / "output.mp3"
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(wav_path),
                     "-codec:a", "libmp3lame", "-b:a", "192k",
                     str(output_path)],
                    capture_output=True, timeout=120, check=True,
                )
                content_type = "audio/mpeg"
            else:
                output_path = wav_path
                content_type = "audio/wav"

            # Get duration
            try:
                dur_result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
                    capture_output=True, text=True, timeout=30,
                )
                duration = float(dur_result.stdout.strip())
            except Exception:
                duration = 0.0

            elapsed = time.time() - start_time

            result = {
                "success": True,
                "duration_seconds": round(duration, 2),
                "mode": mode,
                "processing_time_seconds": round(elapsed, 2),
            }

            # Upload to R2 or return base64
            if r2_config:
                try:
                    import boto3
                    from botocore.config import Config

                    client = boto3.client(
                        "s3",
                        endpoint_url=r2_config["endpoint_url"],
                        aws_access_key_id=r2_config["access_key_id"],
                        aws_secret_access_key=r2_config["secret_access_key"],
                        config=Config(signature_version="s3v4"),
                    )
                    ext = output_path.suffix
                    object_key = f"qwen3-tts/results/{job_id}_{uuid.uuid4().hex[:8]}{ext}"
                    client.upload_file(
                        str(output_path), r2_config["bucket_name"], object_key,
                        ExtraArgs={"ContentType": content_type},
                    )
                    presigned_url = client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": r2_config["bucket_name"], "Key": object_key},
                        ExpiresIn=7200,
                    )
                    result["audio_url"] = presigned_url
                    result["r2_key"] = object_key
                except Exception as e:
                    return {"error": f"R2 upload failed: {e}"}
            else:
                result["audio_base64"] = base64.b64encode(output_path.read_bytes()).decode("utf-8")

            return result

        except Exception as e:
            import traceback
            print(f"Error: {e}")
            print(traceback.format_exc())
            return {"error": f"Internal error: {str(e)}"}
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
