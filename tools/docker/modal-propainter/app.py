"""
Modal deployment for ProPainter video inpainting (dewatermark).

Deploy:
    modal deploy docker/modal-propainter/app.py

Removes watermarks/objects from video using AI inpainting.
Specify region as x,y,width,height or provide a mask image URL.
"""

import modal

app = modal.App("video-toolkit-dewatermark")

WEIGHT_URLS = {
    "ProPainter.pth": "https://github.com/sczhou/ProPainter/releases/download/v0.1.0/ProPainter.pth",
    "recurrent_flow_completion.pth": "https://github.com/sczhou/ProPainter/releases/download/v0.1.0/recurrent_flow_completion.pth",
    "raft-things.pth": "https://github.com/sczhou/ProPainter/releases/download/v0.1.0/raft-things.pth",
    "i3d_rgb_imagenet.pt": "https://github.com/sczhou/ProPainter/releases/download/v0.1.0/i3d_rgb_imagenet.pt",
}

# Memory profiles based on GPU VRAM
MEMORY_PROFILES = {
    8:  {"subvideo_length": 20, "neighbor_length": 3, "ref_stride": 30},
    15: {"subvideo_length": 30, "neighbor_length": 5, "ref_stride": 20},
    22: {"subvideo_length": 40, "neighbor_length": 5, "ref_stride": 15},
    45: {"subvideo_length": 50, "neighbor_length": 5, "ref_stride": 15},
    75: {"subvideo_length": 60, "neighbor_length": 5, "ref_stride": 15},
}

image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04",
        add_python="3.10",
    )
    .apt_install("git", "ffmpeg", "curl")
    .pip_install("numpy<2")
    .pip_install("torch==2.4.0", "torchvision==0.19.0")
    # Clone ProPainter and install deps
    .run_commands(
        "git clone --depth 1 https://github.com/sczhou/ProPainter.git /app/propainter",
        "cd /app/propainter && pip install -r requirements.txt",
    )
    # Download model weights (~2GB)
    .run_commands(
        "mkdir -p /app/propainter/weights",
        *[f"curl -sL -o /app/propainter/weights/{name} {url}" for name, url in WEIGHT_URLS.items()],
    )
    .pip_install("boto3", "requests", "fastapi[standard]")
)


@app.cls(
    image=image,
    gpu="A10G",
    timeout=1800,
    scaledown_window=60,
)
@modal.concurrent(max_inputs=1)
class Dewatermark:
    @modal.enter()
    def verify_setup(self):
        import torch
        from pathlib import Path

        print(f"PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")

        weights_dir = Path("/app/propainter/weights")
        print(f"Weights: {[f.name for f in weights_dir.iterdir()]}")

    @modal.fastapi_endpoint(method="POST")
    def dewatermark(self, request: dict) -> dict:
        import json
        import math
        import os
        import shutil
        import subprocess
        import tempfile
        import time
        import uuid
        from pathlib import Path

        import requests as req
        import torch

        video_url = request.get("video_url")
        region = request.get("region")
        mask_url = request.get("mask_url")
        fp16 = request.get("fp16", True)
        requested_resize_ratio = request.get("resize_ratio", "auto")
        r2_config = request.get("r2")

        if not video_url:
            return {"error": "Missing required 'video_url'"}
        if not region and not mask_url:
            return {"error": "Either 'region' (x,y,w,h) or 'mask_url' is required"}

        work_dir = Path(tempfile.mkdtemp(prefix="modal_dewatermark_"))
        start_time = time.time()

        try:
            # Download video
            print(f"Downloading video from {video_url[:80]}...")
            video_path = str(work_dir / "input.mp4")
            resp = req.get(video_url, stream=True, timeout=300)
            resp.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)

            # Get video info
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height,duration,r_frame_rate,nb_frames",
                 "-show_entries", "format=duration", "-of", "json", video_path],
                capture_output=True, text=True, timeout=30,
            )
            vinfo = json.loads(probe.stdout) if probe.returncode == 0 else {}
            stream = vinfo.get("streams", [{}])[0]
            fmt = vinfo.get("format", {})
            width = int(stream.get("width", 0))
            height = int(stream.get("height", 0))
            duration = float(stream.get("duration") or fmt.get("duration", 0))
            fps_str = stream.get("r_frame_rate", "30/1")
            fps = eval(fps_str) if "/" in str(fps_str) else float(fps_str or 30)
            nb_frames = int(stream.get("nb_frames") or int(duration * fps))

            if not width or not height:
                return {"error": "Could not read video dimensions"}

            print(f"Video: {width}x{height}, {duration:.1f}s, {nb_frames} frames")

            # GPU memory profile
            vram_gb = torch.cuda.get_device_properties(0).total_memory // (1024**3) if torch.cuda.is_available() else 16
            profile = MEMORY_PROFILES[8]
            for threshold in sorted(MEMORY_PROFILES.keys(), reverse=True):
                if vram_gb >= threshold:
                    profile = MEMORY_PROFILES[threshold]
                    break

            # Auto resize ratio
            if requested_resize_ratio == "auto":
                pixels = width * height
                bytes_per_frame = 6.5 * 1024 * 1024 * (pixels / (1280 * 720))
                total_needed = bytes_per_frame * nb_frames + 2 * (1024**3)
                available = vram_gb * (1024**3) * 0.7
                if total_needed > available:
                    frame_mem = bytes_per_frame * nb_frames
                    usable = available - 2 * (1024**3)
                    resize_ratio = max(0.25, min(1.0, math.sqrt(max(0, usable) / max(1, frame_mem))))
                    for nice in [1.0, 0.75, 0.5, 0.375, 0.25]:
                        if resize_ratio >= nice:
                            resize_ratio = nice
                            break
                else:
                    resize_ratio = 1.0
            else:
                resize_ratio = float(requested_resize_ratio)

            print(f"GPU: {vram_gb}GB, profile: {profile}, resize: {resize_ratio}")

            # Create mask
            mask_path = str(work_dir / "mask.png")
            if mask_url:
                resp = req.get(mask_url, timeout=60)
                resp.raise_for_status()
                with open(mask_path, "wb") as f:
                    f.write(resp.content)
            else:
                parts = [int(v.strip()) for v in region.split(",")]
                if len(parts) != 4:
                    return {"error": f"Region must be x,y,width,height — got: {region}"}
                x, y, w, h = parts
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "lavfi",
                     "-i", f"color=black:s={width}x{height}:d=1",
                     "-vf", f"drawbox=x={x}:y={y}:w={w}:h={h}:c=white:t=fill",
                     "-frames:v", "1", mask_path],
                    capture_output=True, timeout=30, check=True,
                )

            # Run ProPainter
            output_dir = str(work_dir / "results")
            os.makedirs(output_dir, exist_ok=True)

            cmd = [
                "python3", "/app/propainter/inference_propainter.py",
                "-i", video_path, "-m", mask_path, "-o", output_dir,
                "--neighbor_length", str(profile["neighbor_length"]),
                "--ref_stride", str(profile["ref_stride"]),
                "--subvideo_length", str(profile["subvideo_length"]),
            ]
            if fp16:
                cmd.append("--fp16")
            if resize_ratio != 1.0:
                cmd.extend(["--resize_ratio", str(resize_ratio)])

            print(f"Running ProPainter...")
            proc = subprocess.run(
                cmd, cwd="/app/propainter",
                capture_output=True, text=True, timeout=3600,
            )

            if proc.returncode != 0:
                print(f"ProPainter stderr: {proc.stderr[-500:]}")
                return {"error": f"ProPainter failed: {proc.stderr[-300:]}"}

            # Find output
            result_path = None
            video_stem = Path(video_path).stem
            expected = Path(output_dir) / video_stem / "inpaint_out.mp4"
            if expected.exists():
                result_path = str(expected)
            else:
                for mp4 in Path(output_dir).rglob("inpaint_out.mp4"):
                    result_path = str(mp4)
                    break
                if not result_path:
                    for mp4 in Path(output_dir).rglob("*.mp4"):
                        if "masked" not in mp4.name:
                            result_path = str(mp4)
                            break

            if not result_path:
                return {"error": "No output file produced"}

            elapsed = time.time() - start_time
            print(f"Done: {elapsed:.1f}s")

            result = {
                "success": True,
                "video_dimensions": f"{width}x{height}",
                "video_duration_seconds": round(duration, 2),
                "video_frame_count": nb_frames,
                "gpu_vram_gb": vram_gb,
                "profile_used": profile,
                "resize_ratio": resize_ratio,
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
                object_key = f"dewatermark/results/{uuid.uuid4().hex[:12]}.mp4"
                client.upload_file(
                    result_path, r2_config["bucket_name"], object_key,
                    ExtraArgs={"ContentType": "video/mp4"},
                )
                result["output_url"] = client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": r2_config["bucket_name"], "Key": object_key},
                    ExpiresIn=7200,
                )
                result["r2_key"] = object_key
            else:
                import base64
                result["video_base64"] = base64.b64encode(Path(result_path).read_bytes()).decode("utf-8")
                print("Warning: Returning video as base64 (use R2 for large files)")

            return result

        except subprocess.TimeoutExpired:
            return {"error": "ProPainter timed out (1h limit)"}
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            print(traceback.format_exc())
            return {"error": f"Internal error: {str(e)}"}
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
