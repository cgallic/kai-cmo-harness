"""Shared cloud GPU provider abstraction.

Routes job submission to RunPod or Modal endpoints with a unified interface.
Each tool builds its own payload dict, then calls call_cloud_endpoint() which
handles submission, polling, timeout, and cancellation for the chosen provider.

Supported providers:
- runpod: RunPod serverless endpoints (existing)
- modal: Modal web endpoints (new)
"""

import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Provider config: maps tool_name → env var for each provider
# ---------------------------------------------------------------------------

_RUNPOD_ENV_VARS = {
    "qwen3_tts": "RUNPOD_QWEN3_TTS_ENDPOINT_ID",
    "flux2": "RUNPOD_FLUX2_ENDPOINT_ID",
    "upscale": "RUNPOD_UPSCALE_ENDPOINT_ID",
    "sadtalker": "RUNPOD_SADTALKER_ENDPOINT_ID",
    "image_edit": "RUNPOD_QWEN_EDIT_ENDPOINT_ID",
    "music_gen": "RUNPOD_ACESTEP_ENDPOINT_ID",
    "dewatermark": "RUNPOD_ENDPOINT_ID",
}

_MODAL_ENV_VARS = {
    "qwen3_tts": "MODAL_QWEN3_TTS_ENDPOINT_URL",
    "flux2": "MODAL_FLUX2_ENDPOINT_URL",
    "upscale": "MODAL_UPSCALE_ENDPOINT_URL",
    "sadtalker": "MODAL_SADTALKER_ENDPOINT_URL",
    "image_edit": "MODAL_IMAGE_EDIT_ENDPOINT_URL",
    "music_gen": "MODAL_MUSIC_GEN_ENDPOINT_URL",
    "dewatermark": "MODAL_DEWATERMARK_ENDPOINT_URL",
    "ltx2": "MODAL_LTX2_ENDPOINT_URL",
}


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def _log(msg: str, level: str = "info"):
    """Print formatted log message to stderr."""
    colors = {
        "info": "\033[94m",
        "success": "\033[92m",
        "error": "\033[91m",
        "warn": "\033[93m",
        "dim": "\033[90m",
    }
    reset = "\033[0m"
    prefix = {"info": "->", "success": "OK", "error": "!!", "warn": "??", "dim": "  "}
    color = colors.get(level, "")
    print(f"{color}{prefix.get(level, '->')} {msg}{reset}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

# GPU hourly rates (approximate, as of March 2026)
_GPU_HOURLY_RATES = {
    "modal": {
        "A10G": 1.10,
        "A100": 3.73,      # 40GB
        "A100-80GB": 4.68,
        "T4": 0.59,
        "L4": 0.80,
        "H100": 8.10,
    },
    "runpod": {
        "ADA_24": 0.44,    # RTX 4090
        "AMPERE_24": 0.44, # RTX 3090 / A5000
        "AMPERE_48": 0.69, # A6000 / RTX A6000
        "AMPERE_80": 1.64, # A100 80GB
    },
}

# Which GPU each tool uses per provider
_TOOL_GPU = {
    "modal": {
        "qwen3_tts": "A10G",
        "flux2": "A10G",
        "upscale": "A10G",
        "sadtalker": "A10G",
        "image_edit": "A10G",
        "music_gen": "A10G",
        "dewatermark": "A10G",
        "ltx2": "A100-80GB",
    },
    "runpod": {
        "qwen3_tts": "ADA_24",
        "flux2": "AMPERE_24",
        "upscale": "AMPERE_24",
        "sadtalker": "AMPERE_24",
        "image_edit": "AMPERE_80",
        "music_gen": "AMPERE_24",
        "dewatermark": "AMPERE_24",
    },
}


def _estimate_cost(provider: str, tool_name: str, elapsed_seconds: float) -> float | None:
    """Estimate cost for a job based on GPU time.

    Returns estimated USD cost, or None if pricing data unavailable.
    """
    gpu = _TOOL_GPU.get(provider, {}).get(tool_name)
    rate = _GPU_HOURLY_RATES.get(provider, {}).get(gpu)
    if rate is None:
        return None
    return (elapsed_seconds / 3600) * rate


def get_provider_config(provider: str, tool_name: str) -> dict:
    """Get configuration for a provider + tool combination.

    Returns dict with provider-specific keys:
    - RunPod: {"api_key": str, "endpoint_id": str}
    - Modal: {"endpoint_url": str, "token_id": str, "token_secret": str}
    """
    if provider == "runpod":
        env_var = _RUNPOD_ENV_VARS.get(tool_name)
        return {
            "api_key": os.getenv("RUNPOD_API_KEY"),
            "endpoint_id": os.getenv(env_var) if env_var else None,
        }
    elif provider == "modal":
        env_var = _MODAL_ENV_VARS.get(tool_name)
        return {
            "endpoint_url": os.getenv(env_var) if env_var else None,
            "token_id": os.getenv("MODAL_TOKEN_ID"),
            "token_secret": os.getenv("MODAL_TOKEN_SECRET"),
        }
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'runpod' or 'modal'.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def call_cloud_endpoint(
    provider: str,
    payload: dict,
    tool_name: str,
    timeout: int = 600,
    poll_interval: int = 5,
    queue_timeout: int = 300,
    progress_label: str = "Processing",
    verbose: bool = True,
) -> tuple[dict, float]:
    """Submit a job to a cloud GPU endpoint and wait for the result.

    Args:
        provider: "runpod" or "modal"
        payload: The job payload ({"input": {...}} for RunPod, raw dict for Modal)
        tool_name: Config lookup key (e.g., "qwen3_tts", "flux2")
        timeout: Overall timeout in seconds
        poll_interval: Seconds between status checks (RunPod only)
        queue_timeout: Cancel if stuck in queue longer than this (RunPod only)
        progress_label: Label for progress messages (e.g., "Generating speech")
        verbose: Print progress to stderr

    Returns:
        (result_dict, elapsed_seconds) — result_dict contains the job output
        or {"error": "..."} on failure.
    """
    config = get_provider_config(provider, tool_name)

    if provider == "runpod":
        result, elapsed = _call_runpod(
            payload=payload,
            api_key=config["api_key"],
            endpoint_id=config["endpoint_id"],
            timeout=timeout,
            poll_interval=poll_interval,
            queue_timeout=queue_timeout,
            progress_label=progress_label,
            verbose=verbose,
        )
    elif provider == "modal":
        result, elapsed = _call_modal(
            payload=payload,
            endpoint_url=config["endpoint_url"],
            token_id=config["token_id"],
            token_secret=config["token_secret"],
            timeout=timeout,
            progress_label=progress_label,
            verbose=verbose,
        )

    else:
        raise ValueError(f"Unknown provider: {provider}")

    # Print cost estimate
    if verbose and elapsed > 0 and not result.get("error"):
        cost = _estimate_cost(provider, tool_name, elapsed)
        if cost is not None:
            _log(f"Est. cost: ${cost:.4f} ({elapsed:.0f}s on {provider})", "dim")

    return result, elapsed


# ---------------------------------------------------------------------------
# RunPod implementation
# ---------------------------------------------------------------------------

def _call_runpod(
    payload: dict,
    api_key: str | None,
    endpoint_id: str | None,
    timeout: int = 600,
    poll_interval: int = 5,
    queue_timeout: int = 300,
    progress_label: str = "Processing",
    verbose: bool = True,
) -> tuple[dict, float]:
    """Submit + poll a RunPod serverless endpoint.

    Consolidates the pattern duplicated across flux2.py, music_gen.py,
    qwen3_tts.py, upscale.py, sadtalker.py, and image_edit.py.
    """
    if not api_key:
        return {"error": "RUNPOD_API_KEY not set in .env"}, 0
    if not endpoint_id:
        return {"error": "RunPod endpoint ID not set. Run with --setup first."}, 0

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start = time.time()

    try:
        # Submit job
        run_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        response = requests.post(run_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()

        job_id = result.get("id")
        status = result.get("status")

        if verbose and job_id:
            _log(f"Job submitted: {job_id}", "dim")

        # Immediate completion (warm worker)
        if status == "COMPLETED":
            return result.get("output", result), time.time() - start

        if status == "FAILED":
            return {"error": result.get("error", "Unknown error")}, time.time() - start

        # Poll for completion
        if verbose:
            _log(f"{progress_label}... (cold start may take 3-5 min on first run)", "warn")

        status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
        queue_start = time.time()
        last_status = None

        while time.time() - start < timeout:
            time.sleep(poll_interval)
            elapsed = time.time() - start

            try:
                status_resp = requests.get(status_url, headers=headers, timeout=30)
                status_data = status_resp.json()
                status = status_data.get("status")
            except Exception as e:
                if verbose:
                    _log(f"[{elapsed:.0f}s] Status check error: {e}", "dim")
                continue

            if status != last_status:
                if verbose:
                    if status == "IN_PROGRESS":
                        _log(f"[{elapsed:.0f}s] {progress_label}...", "dim")
                    elif status == "IN_QUEUE":
                        _log(f"[{elapsed:.0f}s] Waiting for GPU...", "dim")
                last_status = status

            if status == "COMPLETED":
                return status_data.get("output", status_data), time.time() - start

            if status == "FAILED":
                error = status_data.get("error", "Unknown error")
                return {"error": error}, time.time() - start

            if status in ("CANCELLED", "TIMED_OUT"):
                return {"error": f"Job {status}"}, time.time() - start

            # Cancel jobs stuck in queue too long
            if status == "IN_QUEUE" and queue_start and (time.time() - queue_start > queue_timeout):
                if verbose:
                    _log(f"Job stuck in queue for {queue_timeout}s — cancelling", "warn")
                _cancel_runpod_job(endpoint_id, api_key, job_id)
                return {"error": f"Cancelled: no GPU available after {queue_timeout}s in queue"}, time.time() - start

            # Reset queue timer when job starts processing
            if status == "IN_PROGRESS" and queue_start:
                queue_start = None

        # Overall timeout — cancel the job
        if verbose:
            _log("Polling timeout — cancelling job on RunPod", "warn")
        _cancel_runpod_job(endpoint_id, api_key, job_id)
        return {"error": "polling timeout (job cancelled)"}, time.time() - start

    except requests.exceptions.Timeout:
        return {"error": "HTTP request timeout"}, time.time() - start
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}, time.time() - start
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}, time.time() - start


def _cancel_runpod_job(endpoint_id: str, api_key: str, job_id: str):
    """Cancel a RunPod job (best-effort, ignores errors)."""
    try:
        cancel_url = f"https://api.runpod.ai/v2/{endpoint_id}/cancel/{job_id}"
        requests.post(
            cancel_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Modal implementation
# ---------------------------------------------------------------------------

def _call_modal(
    payload: dict,
    endpoint_url: str | None,
    token_id: str | None,
    token_secret: str | None,
    timeout: int = 600,
    progress_label: str = "Processing",
    verbose: bool = True,
) -> tuple[dict, float]:
    """Call a Modal web endpoint.

    Modal web endpoints are synchronous — the HTTP request blocks until the
    function completes and returns the result. No polling needed.

    For endpoints that may take longer than the HTTP timeout, Modal
    automatically handles keep-alive. We set a generous requests timeout
    to match the function's server-side timeout.
    """
    if not endpoint_url:
        return {"error": "Modal endpoint URL not set. Run with --setup --cloud modal first."}, 0

    # Modal web endpoints can be public or authenticated.
    # If token is configured, use it; otherwise call without auth (public endpoint).
    headers = {"Content-Type": "application/json"}
    if token_id and token_secret:
        headers["Authorization"] = f"Bearer {token_id}:{token_secret}"

    # Modal expects the payload directly (not wrapped in {"input": ...}).
    # Unwrap if the caller used RunPod's format for compatibility.
    modal_payload = payload.get("input", payload) if isinstance(payload, dict) else payload

    start = time.time()

    if verbose:
        _log(f"{progress_label} via Modal...", "info")

    try:
        # Modal web endpoints are synchronous — single POST, wait for result.
        # Set timeout slightly above the server-side function timeout to avoid
        # the client giving up before the server does.
        response = requests.post(
            endpoint_url,
            json=modal_payload,
            headers=headers,
            timeout=timeout + 30,
        )

        elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()
            if verbose:
                _log(f"Completed in {elapsed:.1f}s", "success")
            return result, elapsed

        # Modal error responses
        error_body = response.text[:500]
        if response.status_code == 422:
            return {"error": f"Modal validation error: {error_body}"}, elapsed
        elif response.status_code == 408:
            return {"error": f"Modal function timed out after {timeout}s"}, elapsed
        elif response.status_code == 503:
            return {"error": "Modal endpoint is scaling up or unavailable. Try again in a moment."}, elapsed
        else:
            return {"error": f"Modal HTTP {response.status_code}: {error_body}"}, elapsed

    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        return {"error": f"Modal request timed out after {elapsed:.0f}s"}, elapsed
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start
        return {"error": f"Modal connection failed (is the endpoint deployed?): {e}"}, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return {"error": f"Modal request failed: {e}"}, elapsed
