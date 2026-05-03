#!/usr/bin/env python3
"""
RunPod serverless handler for FLUX.2 Klein 4B.

Supports:
- generate: Text-to-image generation
- edit: Image editing with text prompt (pass reference image)

Input format:
{
    "input": {
        "operation": str,              # "generate" (default) or "edit"
        "prompt": str,                 # Required - text prompt
        "image_base64": str,           # Required for edit - reference image (base64)
        "images_base64": [str],        # Optional - additional reference images (up to 2 more)
        "negative_prompt": str,        # Optional (default: "")
        "width": int,                  # Optional (default: 1024)
        "height": int,                 # Optional (default: 1024)
        "num_inference_steps": int,    # Optional (default: 4 for generate, 50 for edit)
        "guidance_scale": float,       # Optional (default: 1.0 for generate, 4.0 for edit)
        "seed": int,                   # Optional (random if not set)
        "r2": dict,                    # Optional - R2 upload config
    }
}

Output format:
{
    "success": true,
    "image_base64": str,
    "seed": int,
    "inference_time_ms": int,
    "image_size": [width, height]
}
"""

import base64
import io
import os
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

import runpod
import torch
from PIL import Image

MODEL_ID = "black-forest-labs/FLUX.2-klein-4B"

# Lazy-loaded pipeline
_pipeline = None


def log(message: str) -> None:
    """Log message to stderr (visible in RunPod logs)."""
    print(message, file=sys.stderr, flush=True)


def setup_hf_cache() -> None:
    """Set up HuggingFace cache - prefer network volume, fall back to default."""
    baked_cache = Path("/root/.cache/huggingface")
    if baked_cache.exists():
        os.environ["HF_HOME"] = str(baked_cache)
        log(f"Using baked-in model cache: {baked_cache}")
    elif Path("/runpod-volume").exists() and os.access("/runpod-volume", os.W_OK):
        cache_path = Path("/runpod-volume/.cache/huggingface")
        cache_path.mkdir(parents=True, exist_ok=True)
        os.environ["HF_HOME"] = str(cache_path)
        log(f"Using RunPod network volume cache: {cache_path}")
    else:
        log("WARNING: No cache found, will download models")


def decode_base64_image(image_base64: str) -> Optional[Image.Image]:
    """Decode base64 string to PIL Image."""
    try:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return image
    except Exception as e:
        log(f"Error decoding base64 image: {e}")
        return None


def encode_image_base64(image: Image.Image, format: str = "PNG") -> str:
    """Encode PIL Image to base64 string."""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_pipeline():
    """Get or initialize the Flux2 Klein pipeline (lazy loading)."""
    global _pipeline

    if _pipeline is not None:
        return _pipeline

    log(f"Loading Flux2 Klein pipeline from {MODEL_ID}...")
    start = time.time()

    try:
        from diffusers import Flux2KleinPipeline

        _pipeline = Flux2KleinPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
        )
        _pipeline.to("cuda")
    except Exception as e:
        import traceback
        log(f"Pipeline loading error: {e}")
        log(f"Full traceback:\n{traceback.format_exc()}")
        raise

    log(f"Pipeline loaded in {time.time() - start:.1f}s")
    return _pipeline


def upload_to_r2(image_base64: str, job_id: str, r2_config: dict) -> tuple[Optional[str], Optional[str]]:
    """Upload image to Cloudflare R2 and return (presigned_url, object_key)."""
    try:
        import boto3
        from botocore.config import Config
        import uuid

        log("Uploading to R2...")

        client = boto3.client(
            "s3",
            endpoint_url=r2_config["endpoint_url"],
            aws_access_key_id=r2_config["access_key_id"],
            aws_secret_access_key=r2_config["secret_access_key"],
            config=Config(signature_version="s3v4"),
        )

        object_key = f"flux2/results/{job_id}_{uuid.uuid4().hex[:8]}.png"

        image_bytes = base64.b64decode(image_base64)
        client.put_object(
            Bucket=r2_config["bucket_name"],
            Key=object_key,
            Body=image_bytes,
            ContentType="image/png"
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


def handle_generate(job_input: dict, job_id: str) -> dict:
    """Text-to-image generation."""
    start_time = time.time()

    prompt = job_input.get("prompt")
    if not prompt:
        return {"error": "Missing required 'prompt' in input"}

    width = job_input.get("width", 1024)
    height = job_input.get("height", 1024)
    num_inference_steps = job_input.get("num_inference_steps", 4)
    guidance_scale = job_input.get("guidance_scale", 1.0)
    seed = job_input.get("seed")
    r2_config = job_input.get("r2")

    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    log(f"Using seed: {seed}")

    pipe = get_pipeline()

    log(f"Generating: {width}x{height}, steps={num_inference_steps}, guidance={guidance_scale}")
    gen_start = time.time()

    try:
        generator = torch.Generator(device="cuda").manual_seed(seed)
        output = pipe(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )
        output_image = output.images[0]
    except Exception as e:
        import traceback
        log(f"Generation error: {e}")
        log(f"Traceback:\n{traceback.format_exc()}")
        raise

    gen_time = time.time() - gen_start
    log(f"Generation completed in {gen_time:.1f}s")

    output_base64 = encode_image_base64(output_image)
    elapsed_ms = int((time.time() - start_time) * 1000)

    result = {
        "success": True,
        "image_base64": output_base64,
        "seed": seed,
        "inference_time_ms": elapsed_ms,
        "image_size": [width, height],
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
    }

    if r2_config:
        url, r2_key = upload_to_r2(output_base64, job_id, r2_config)
        if url:
            result["output_url"] = url
            result["r2_key"] = r2_key

    return result


def handle_edit(job_input: dict, job_id: str) -> dict:
    """Image editing with reference image(s)."""
    start_time = time.time()

    prompt = job_input.get("prompt")
    image_base64 = job_input.get("image_base64")
    images_base64 = job_input.get("images_base64", [])

    if not prompt:
        return {"error": "Missing required 'prompt' in input"}
    if not image_base64:
        return {"error": "Missing required 'image_base64' in input"}

    # Decode primary image
    input_image = decode_base64_image(image_base64)
    if input_image is None:
        return {"error": "Failed to decode input image from base64"}
    log(f"Primary image size: {input_image.size}")

    # Build image list (primary + optional references)
    all_images = [input_image]
    for i, ref_b64 in enumerate(images_base64[:2]):
        ref_image = decode_base64_image(ref_b64)
        if ref_image is None:
            return {"error": f"Failed to decode reference image {i+2} from base64"}
        all_images.append(ref_image)
        log(f"Reference image {i+2} size: {ref_image.size}")

    log(f"Total images for edit: {len(all_images)}")

    num_inference_steps = job_input.get("num_inference_steps", 50)
    guidance_scale = job_input.get("guidance_scale", 4.0)
    seed = job_input.get("seed")
    r2_config = job_input.get("r2")

    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    log(f"Using seed: {seed}")

    pipe = get_pipeline()

    log(f"Editing: steps={num_inference_steps}, guidance={guidance_scale}")
    gen_start = time.time()

    try:
        generator = torch.Generator(device="cuda").manual_seed(seed)
        # Pass image(s) for editing — single image or list for multi-reference
        image_input = all_images if len(all_images) > 1 else all_images[0]
        output = pipe(
            prompt=prompt,
            image=image_input,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )
        output_image = output.images[0]
    except Exception as e:
        import traceback
        log(f"Edit error: {e}")
        log(f"Traceback:\n{traceback.format_exc()}")
        raise

    gen_time = time.time() - gen_start
    log(f"Edit completed in {gen_time:.1f}s")

    output_base64 = encode_image_base64(output_image)
    elapsed_ms = int((time.time() - start_time) * 1000)

    result = {
        "success": True,
        "image_base64": output_base64,
        "seed": seed,
        "inference_time_ms": elapsed_ms,
        "image_size": list(output_image.size),
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
    }

    if r2_config:
        url, r2_key = upload_to_r2(output_base64, job_id, r2_config)
        if url:
            result["output_url"] = url
            result["r2_key"] = r2_key

    return result


def handler(job: dict) -> dict:
    """Main RunPod handler — routes to generate or edit."""
    job_id = job.get("id", "unknown")
    job_input = job.get("input", {})

    operation = job_input.get("operation", "generate")
    log(f"Job {job_id}: operation={operation}")

    try:
        if operation == "generate":
            return handle_generate(job_input, job_id)
        elif operation == "edit":
            return handle_edit(job_input, job_id)
        else:
            return {"error": f"Unknown operation: {operation}. Supported: generate, edit"}
    except torch.cuda.OutOfMemoryError as e:
        log(f"CUDA OOM: {e}")
        torch.cuda.empty_cache()
        return {"error": "GPU out of memory. Try smaller dimensions or fewer steps."}
    except Exception as e:
        import traceback
        log(f"Handler exception: {e}")
        log(traceback.format_exc())
        return {"error": f"Internal error: {str(e)}"}


if __name__ == "__main__":
    log("Starting RunPod Flux2 Klein handler...")

    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        vram_gb = props.total_memory // (1024 ** 3)
        log(f"CUDA available: {props.name}, VRAM: {vram_gb}GB")
    else:
        log("WARNING: CUDA not available!")

    setup_hf_cache()

    # Pre-load pipeline at startup
    log("Pre-loading pipeline (first run downloads ~8GB model)...")
    try:
        get_pipeline()
        log("Pipeline pre-loaded successfully")
    except Exception as e:
        log(f"Warning: Pipeline pre-load failed: {e}")
        log("Will retry on first request")

    runpod.serverless.start({"handler": handler})
