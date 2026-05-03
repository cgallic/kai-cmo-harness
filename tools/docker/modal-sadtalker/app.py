"""
Modal deployment for SadTalker talking head generation.

Deploy:
    modal deploy docker/modal-sadtalker/app.py

Generates talking head videos from a portrait image + audio file.
Audio >45s is split into chunks to prevent drift.

Note: Uses subprocess to run SadTalker inference.py (not a direct Python API).
Cold start ~45-60s (models baked into image).
"""

import modal

app = modal.App("video-toolkit-sadtalker")

CHUNK_DURATION = 45  # seconds — split long audio to prevent drift

# Model weight URLs (baked into image at build time)
SADTALKER_WEIGHTS = {
    "mapping_109": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar",
    "mapping_229": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar",
    "model_256": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors",
    "model_512": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors",
    "bfm": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2/BFM_Fitting.zip",
    "hub": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2/hub.zip",
    "gfpgan": "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
    "facexlib_det": "https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth",
    "facexlib_parse": "https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth",
}

image = (
    modal.Image.from_registry(
        "nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04",
        add_python="3.10",
        force_build=True,
    )
    .apt_install(
        "ffmpeg", "git", "wget", "unzip", "cmake", "build-essential",
        "libgl1-mesa-glx", "libglib2.0-0",
    )
    # torch 2.4+ handles both numpy 1.x and 2.x correctly.
    # Earlier torch versions fail with "Numpy is not available" on Modal's runtime.
    .pip_install("numpy<2")
    .pip_install("torch==2.4.0", "torchvision==0.19.0", "torchaudio==2.4.0")
    .pip_install("basicsr>=1.4.2", "facexlib>=0.3.0", "gfpgan", "realesrgan")
    # Patch basicsr for torchvision 0.19+ (functional_tensor removed)
    .run_commands(
        r"find /usr/local/lib -name 'degradations.py' -path '*/basicsr/*' -exec "
        r"sed -i 's/from torchvision.transforms.functional_tensor import rgb_to_grayscale/"
        r"from torchvision.transforms.functional import rgb_to_grayscale/g' {} \;"
    )
    .pip_install(
        "dlib-bin",
        "face_alignment",
        "imageio",
        "imageio-ffmpeg",
        "kornia",
        "librosa",
        "pydub",
        "scipy",
        "tqdm",
        "yacs",
        "safetensors",
        "boto3",
        "requests",
        "fastapi[standard]",
    )
    # Clone SadTalker
    .run_commands("git clone --depth 1 https://github.com/OpenTalker/SadTalker.git /app/SadTalker")
    # Patch numpy 2.0 compat (belt-and-suspenders even with numpy<2 pin)
    .run_commands(
        r"find /app/SadTalker -name '*.py' -exec sed -i 's/np\.float\b/float/g' {} \;",
        r"find /app/SadTalker -name '*.py' -exec sed -i 's/np\.int\b/int/g' {} \;",
        r"find /app/SadTalker -name '*.py' -exec sed -i 's/np\.VisibleDeprecationWarning/DeprecationWarning/g' {} \;",
        # Fix trans_params array element error
        r"""sed -i 's/trans_params = np\.array(\[w0, h0, s, t\[0\], t\[1\]\])/trans_params = np.array([w0, h0, s, t[0], t[1]], dtype=object)/g' /app/SadTalker/src/face3d/util/preprocess.py""",
    )
    # Download model weights
    .run_commands(
        "mkdir -p /app/SadTalker/checkpoints",
        f"wget -q -P /app/SadTalker/checkpoints {SADTALKER_WEIGHTS['mapping_109']}",
        f"wget -q -P /app/SadTalker/checkpoints {SADTALKER_WEIGHTS['mapping_229']}",
        f"wget -q -P /app/SadTalker/checkpoints {SADTALKER_WEIGHTS['model_256']}",
        f"wget -q -P /app/SadTalker/checkpoints {SADTALKER_WEIGHTS['model_512']}",
        # BFM fitting models
        f"cd /app/SadTalker/checkpoints && wget -q {SADTALKER_WEIGHTS['bfm']} && unzip -q BFM_Fitting.zip && rm BFM_Fitting.zip",
        # Face detection hub models
        f"mkdir -p /root/.cache/torch && wget -q {SADTALKER_WEIGHTS['hub']} -O /tmp/hub.zip && unzip -q /tmp/hub.zip -d /root/.cache/torch/ && rm /tmp/hub.zip",
        # GFPGAN weights
        f"mkdir -p /app/SadTalker/gfpgan/weights && wget -q -P /app/SadTalker/gfpgan/weights {SADTALKER_WEIGHTS['gfpgan']}",
        # facexlib detection models
        f"mkdir -p /root/.cache/facexlib && wget -q -O /root/.cache/facexlib/detection_Resnet50_Final.pth {SADTALKER_WEIGHTS['facexlib_det']}",
        f"wget -q -O /root/.cache/facexlib/parsing_parsenet.pth {SADTALKER_WEIGHTS['facexlib_parse']}",
    )
    .env({"PYTHONPATH": "/app/SadTalker"})
)


@app.cls(
    image=image,
    gpu="A10G",
    timeout=1800,
    scaledown_window=60,
)
@modal.concurrent(max_inputs=1)
class SadTalkerGen:
    @modal.enter()
    def verify_setup(self):
        import subprocess
        import torch
        from pathlib import Path

        print(f"PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")

        # Verify numpy-torch bridge works in this runtime
        import numpy
        t = torch.from_numpy(numpy.array([1.0]))
        print(f"numpy {numpy.__version__}, torch.from_numpy: {t}")

        # Also verify it works from subprocess (since SadTalker runs as subprocess)
        result = subprocess.run(
            ["python", "-c", "import torch, numpy; print(f'subprocess: numpy={numpy.__version__}, from_numpy={torch.from_numpy(numpy.array([1.0]))}')"],
            capture_output=True, text=True,
        )
        print(f"Subprocess check: {result.stdout.strip() or result.stderr.strip()}")

        ckpt = Path("/app/SadTalker/checkpoints")
        print(f"Checkpoints: {[f.name for f in ckpt.iterdir()][:6]}")

    @modal.fastapi_endpoint(method="POST")
    def generate(self, request: dict) -> dict:
        import base64
        import shutil
        import subprocess
        import tempfile
        import time
        import uuid
        from pathlib import Path

        import requests as req

        start_time = time.time()

        # Get inputs
        image_url = request.get("image_url")
        image_base64 = request.get("image_base64")
        audio_url = request.get("audio_url")
        audio_base64 = request.get("audio_base64")

        if not image_url and not image_base64:
            return {"error": "Missing image_url or image_base64"}
        if not audio_url and not audio_base64:
            return {"error": "Missing audio_url or audio_base64"}

        still_mode = request.get("still_mode", False)
        enhancer = request.get("enhancer", "gfpgan")
        preprocess = request.get("preprocess", "crop")
        size = request.get("size", 256)
        expression_scale = request.get("expression_scale", 1.0)
        pose_style = request.get("pose_style", 0)
        r2_config = request.get("r2")

        work_dir = Path(tempfile.mkdtemp(prefix="modal_sadtalker_"))

        try:
            # Download/decode image
            image_path = work_dir / "input_image.png"
            if image_url:
                resp = req.get(image_url, stream=True, timeout=300)
                resp.raise_for_status()
                with open(image_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
            else:
                data = image_base64
                if "," in data:
                    data = data.split(",", 1)[1]
                image_path.write_bytes(base64.b64decode(data))

            # Download/decode audio
            audio_path = work_dir / "input_audio.wav"
            if audio_url:
                resp = req.get(audio_url, stream=True, timeout=300)
                resp.raise_for_status()
                with open(audio_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
            else:
                data = audio_base64
                if "," in data:
                    data = data.split(",", 1)[1]
                audio_path.write_bytes(base64.b64decode(data))

            # Get audio duration
            total_duration = 0.0
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
                    capture_output=True, text=True, timeout=30,
                )
                total_duration = float(result.stdout.strip())
            except Exception:
                pass

            print(f"Audio: {total_duration:.1f}s, size={size}, enhancer={enhancer}")

            # Split audio into chunks if needed
            if total_duration > CHUNK_DURATION:
                audio_chunks = []
                start = 0.0
                idx = 0
                while start < total_duration:
                    chunk_path = work_dir / f"chunk_{idx:03d}.wav"
                    end = min(start + CHUNK_DURATION, total_duration)
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", str(audio_path),
                         "-ss", str(start), "-t", str(end - start),
                         "-c:a", "pcm_s16le", str(chunk_path)],
                        capture_output=True, timeout=60,
                    )
                    if chunk_path.exists():
                        audio_chunks.append(chunk_path)
                    start = end
                    idx += 1
                print(f"Split into {len(audio_chunks)} chunks")
            else:
                audio_chunks = [audio_path]

            # Process each chunk
            video_chunks = []
            for i, chunk in enumerate(audio_chunks):
                print(f"Processing chunk {i + 1}/{len(audio_chunks)}...")
                chunk_out = work_dir / f"output_{i:03d}"
                chunk_out.mkdir()

                cmd = [
                    "python", "/app/SadTalker/inference.py",
                    "--driven_audio", str(chunk),
                    "--source_image", str(image_path),
                    "--result_dir", str(chunk_out),
                    "--checkpoint_dir", "/app/SadTalker/checkpoints",
                    "--size", str(size),
                    "--expression_scale", str(expression_scale),
                    "--pose_style", str(pose_style),
                    "--preprocess", preprocess,
                ]
                if still_mode:
                    cmd.append("--still")
                if enhancer != "none":
                    cmd.extend(["--enhancer", enhancer])

                proc = subprocess.run(
                    cmd, cwd="/app/SadTalker",
                    capture_output=True, text=True, timeout=1800,
                )

                if proc.returncode != 0:
                    print(f"SadTalker stderr: {proc.stderr[-500:]}")
                    return {"error": f"Chunk {i + 1} failed: {proc.stderr[-300:]}"}

                # Find output video
                video_path = None
                for f in chunk_out.glob("*.mp4"):
                    video_path = f
                    break
                if not video_path:
                    for subdir in chunk_out.iterdir():
                        if subdir.is_dir():
                            for f in subdir.glob("*.mp4"):
                                video_path = f
                                break
                        if video_path:
                            break

                if not video_path:
                    return {"error": f"No video output for chunk {i + 1}"}

                video_chunks.append(video_path)

            # Concatenate chunks
            final_video = work_dir / "final.mp4"
            if len(video_chunks) == 1:
                shutil.copy(video_chunks[0], final_video)
            else:
                concat_file = work_dir / "concat.txt"
                with open(concat_file, "w") as f:
                    for vp in video_chunks:
                        f.write(f"file '{vp}'\n")
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                     "-i", str(concat_file), "-c", "copy", str(final_video)],
                    capture_output=True, timeout=120, check=True,
                )

            elapsed = time.time() - start_time
            print(f"Done: {elapsed:.1f}s, {len(audio_chunks)} chunks")

            result = {
                "success": True,
                "duration_seconds": round(total_duration, 2),
                "chunks_processed": len(audio_chunks),
                "processing_time_seconds": round(elapsed, 2),
            }

            # Upload to R2 or return base64
            if r2_config:
                import boto3
                from botocore.config import Config

                client = boto3.client(
                    "s3",
                    endpoint_url=r2_config["endpoint_url"],
                    aws_access_key_id=r2_config["access_key_id"],
                    aws_secret_access_key=r2_config["secret_access_key"],
                    config=Config(signature_version="s3v4"),
                )
                object_key = f"sadtalker/results/{uuid.uuid4().hex[:12]}.mp4"
                client.upload_file(
                    str(final_video), r2_config["bucket_name"], object_key,
                    ExtraArgs={"ContentType": "video/mp4"},
                )
                result["video_url"] = client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": r2_config["bucket_name"], "Key": object_key},
                    ExpiresIn=7200,
                )
                result["r2_key"] = object_key
            else:
                result["video_base64"] = base64.b64encode(final_video.read_bytes()).decode("utf-8")
                print("Warning: Returning video as base64 (use R2 for large files)")

            return result

        except subprocess.TimeoutExpired:
            return {"error": "SadTalker timed out"}
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            print(traceback.format_exc())
            return {"error": f"Internal error: {str(e)}"}
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
