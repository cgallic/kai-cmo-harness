"""
Knowledge Cloner — Phase 2a: Transcription.

Strategy cascade (cheapest first):
1. youtube-transcript-api (free, instant)
2. yt-dlp subtitle download (free, slower)
3. yt-dlp audio download → Gemini Flash transcription (paid fallback)
"""

import asyncio
import shutil
import re
import time
import httpx
from pathlib import Path
from typing import Optional

from .types import ExpertConfig, Source
from .utils import (
    CostTracker, RateLimiter, log, write_file, read_file,
    call_gemini_with_audio, confirm_action,
)
from .prompts import TRANSCRIPTION_PROMPT


async def transcribe_sources(
    config: ExpertConfig,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
    limit: int = 0,
    source_type_filter: Optional[str] = None,
    dry_run: bool = False,
) -> ExpertConfig:
    """Transcribe all queued/discovered sources."""
    # Get sources needing transcription
    candidates = [
        s for s in config.sources
        if s.status in ("queued", "discovered")
        and (not source_type_filter or s.source_type == source_type_filter)
    ]

    if limit:
        candidates = candidates[:limit]

    if not candidates:
        log("No sources need transcription.")
        return config

    log(f"Transcribing {len(candidates)} sources...")

    # Count how many might need paid transcription
    youtube_count = sum(1 for s in candidates if s.source_type == "youtube")
    non_youtube = sum(1 for s in candidates if s.source_type != "youtube")

    if dry_run:
        log(f"[DRY RUN] Would transcribe {len(candidates)} sources:")
        log(f"  YouTube (free captions): {youtube_count}")
        log(f"  Other (may need Gemini): {non_youtube}")
        fallback_est = max(1, youtube_count // 5)  # ~20% need fallback
        log(f"  Estimated Gemini fallbacks: {fallback_est}")
        log(f"  Estimated cost: ~${fallback_est * 0.01:.2f}")
        return config

    succeeded = 0
    failed = 0

    for i, source in enumerate(candidates, 1):
        log(f"  [{i}/{len(candidates)}] {source.source_type}: {source.title or source.id}")

        try:
            transcript = await _transcribe_source(source, expert_dir, tracker, limiter)
            if transcript:
                # Save transcript
                transcript_path = f"raw/transcripts/{source.id}.md"
                full_path = expert_dir / transcript_path

                header = (
                    f"---\n"
                    f"source_id: {source.id}\n"
                    f"source_type: {source.source_type}\n"
                    f"title: {source.title}\n"
                    f"url: {source.url}\n"
                    f"date: {source.date}\n"
                    f"transcribed: {time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"---\n\n"
                    f"# {source.title or source.id}\n\n"
                )
                write_file(full_path, header + transcript)

                source.status = "transcribed"
                source.transcript_path = transcript_path
                succeeded += 1
            else:
                source.status = "failed"
                source.error = "No transcript obtained"
                failed += 1
        except Exception as e:
            log(f"    ERROR: {e}")
            source.status = "failed"
            source.error = str(e)[:200]
            failed += 1

    log(f"Transcription: {succeeded} succeeded, {failed} failed")
    return config


async def _transcribe_source(
    source: Source,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
) -> Optional[str]:
    """Transcribe a single source using the cheapest method available."""
    if source.source_type == "youtube":
        return await _transcribe_youtube(source, expert_dir, tracker, limiter)
    elif source.source_type == "podcast":
        return await _transcribe_podcast(source, expert_dir, tracker, limiter)
    elif source.source_type == "article":
        return await _transcribe_article(source)
    elif source.source_type == "repo":
        return await _transcribe_repo(source, expert_dir)
    elif source.source_type in ("xspace", "file"):
        # These should have been imported as already-transcribed
        return None
    else:
        log(f"    Unknown source type: {source.source_type}")
        return None


async def _transcribe_youtube(
    source: Source,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
) -> Optional[str]:
    """Transcribe YouTube video: captions → subtitles → audio+Gemini."""
    video_id = source.id.replace("yt_", "")

    # Strategy 1: youtube-transcript-api (free, instant)
    transcript = await _try_youtube_transcript_api(video_id)
    if transcript:
        log(f"    Got transcript via youtube-transcript-api (free)")
        return transcript

    # Strategy 2: yt-dlp subtitle download
    transcript = await _try_ytdlp_subtitles(video_id, expert_dir)
    if transcript:
        log(f"    Got transcript via yt-dlp subtitles (free)")
        return transcript

    # Strategy 3: Gemini video URL (Google can access YouTube natively — no IP blocks)
    log(f"    No free captions. Using Gemini video transcription...")
    tracker.check_or_abort()

    transcript = await _try_gemini_youtube_url(video_id, tracker, limiter)
    if transcript:
        log(f"    Got transcript via Gemini YouTube URL")
        return transcript

    # Strategy 4: Download audio → Gemini transcription (last resort)
    transcript = await _try_gemini_audio(source.url, expert_dir, tracker, limiter)
    if transcript:
        log(f"    Got transcript via Gemini audio transcription")
        return transcript

    return None


async def _try_youtube_transcript_api(video_id: str) -> Optional[str]:
    """Try to get transcript using youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        log("    youtube-transcript-api not installed, skipping")
        return None

    try:
        ytt = YouTubeTranscriptApi()
        # Try English first, then any language (Spanish etc.)
        for langs in [["en"], ["es"], None]:
            try:
                if langs:
                    result = ytt.fetch(video_id, languages=langs)
                else:
                    result = ytt.fetch(video_id)
                lines = []
                for snippet in result:
                    start = snippet.start
                    mins = int(start // 60)
                    secs = int(start % 60)
                    text = snippet.text.strip()
                    if text:
                        lines.append(f"[{mins:02d}:{secs:02d}] {text}")
                if lines:
                    return "\n".join(lines)
            except Exception:
                continue
        return None
    except Exception as e:
        log(f"    youtube-transcript-api error: {e}")
        return None


async def _try_gemini_youtube_url(
    video_id: str,
    tracker: CostTracker,
    limiter: RateLimiter,
) -> Optional[str]:
    """Transcribe YouTube video by passing URL directly to Gemini.

    Google's servers can access YouTube natively — no IP blocking issues.
    Costs ~$0.01-0.03 per video depending on length.
    """
    from .config import GEMINI_API_KEY, GEMINI_FLASH_ENDPOINT
    from .prompts import TRANSCRIPTION_PROMPT

    if not GEMINI_API_KEY:
        log("    GEMINI_API_KEY not set, skipping Gemini video transcription")
        return None

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    video_prompt = (
        "Listen to the audio in this YouTube video and transcribe everything "
        "that is spoken, word for word. Include all dialogue. Add paragraph "
        "breaks between different topics. Add timestamps in [HH:MM:SS] format "
        "every few minutes. If there is no speech, say NO_SPEECH."
    )

    await limiter.wait()
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{GEMINI_FLASH_ENDPOINT}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": video_prompt},
                            {"file_data": {
                                "file_uri": youtube_url,
                                "mime_type": "video/mp4",
                            }},
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 16384,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        usage = data.get("usageMetadata", {})
        in_tok = usage.get("promptTokenCount", 0)
        out_tok = usage.get("candidatesTokenCount", len(text) // 4)
        tracker.record("gemini-flash", in_tok, out_tok)

        return text if text else None

    except Exception as e:
        log(f"    Gemini video URL error: {e}")
        return None


async def _try_ytdlp_subtitles(video_id: str, expert_dir: Path) -> Optional[str]:
    """Try to download subtitles using yt-dlp."""
    if not shutil.which("yt-dlp"):
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"
    sub_dir = expert_dir / "raw" / "transcripts"
    sub_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp", "--skip-download",
        "--write-auto-sub", "--sub-lang", "en",
        "--sub-format", "vtt",
        "-o", str(sub_dir / f"yt_{video_id}"),
        url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    # Check for downloaded subtitle file
    for ext in [".en.vtt", ".en.auto.vtt"]:
        sub_file = sub_dir / f"yt_{video_id}{ext}"
        if sub_file.exists():
            vtt_content = sub_file.read_text(encoding="utf-8", errors="replace")
            transcript = _parse_vtt(vtt_content)
            sub_file.unlink()  # Clean up VTT file
            if transcript:
                return transcript

    return None


def _parse_vtt(vtt_content: str) -> str:
    """Parse VTT subtitle content into clean transcript text."""
    lines = []
    seen = set()

    for line in vtt_content.split("\n"):
        line = line.strip()
        # Skip timestamps, WEBVTT header, and empty lines
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}", line):
            continue
        if "-->" in line:
            continue
        # Remove HTML tags
        line = re.sub(r"<[^>]+>", "", line)
        if line and line not in seen:
            seen.add(line)
            lines.append(line)

    return " ".join(lines)


async def _try_gemini_audio(
    url: str,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
) -> Optional[str]:
    """Download audio and transcribe with Gemini Flash."""
    if not shutil.which("yt-dlp"):
        log("    yt-dlp not found for audio download")
        return None

    audio_dir = expert_dir / "raw" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Download audio only
    audio_file = audio_dir / "temp_audio.m4a"
    cmd = [
        "yt-dlp", "-x", "--audio-format", "m4a",
        "--audio-quality", "5",  # Lower quality = smaller file
        "-o", str(audio_file),
        url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    # Find the downloaded file (yt-dlp may add extension)
    actual_files = list(audio_dir.glob("temp_audio*"))
    if not actual_files:
        log("    Audio download failed")
        return None

    audio_path = actual_files[0]
    audio_bytes = audio_path.read_bytes()

    # Clean up audio file
    for f in actual_files:
        f.unlink()

    # Check file size (Gemini has limits)
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > 20:
        log(f"    Audio too large ({size_mb:.1f} MB). Skipping Gemini transcription.")
        return None

    # Determine MIME type
    mime_type = "audio/m4a"
    if audio_path.suffix == ".mp3":
        mime_type = "audio/mp3"
    elif audio_path.suffix == ".wav":
        mime_type = "audio/wav"

    await limiter.wait()
    text, in_tokens, out_tokens = await call_gemini_with_audio(
        audio_bytes, mime_type, TRANSCRIPTION_PROMPT
    )
    tracker.record("gemini-flash", in_tokens, out_tokens)

    return text if text else None


async def _transcribe_repo(
    source: Source,
    expert_dir: Path,
) -> Optional[str]:
    """Convert a GitHub repo into a markdown document for knowledge extraction.

    Strategy (inspired by arXiv:2603.11808 — repo structural analysis):
    1. Shallow clone the repo
    2. Generate directory tree
    3. Identify and read key files (README, configs, main scripts, SKILL.md, etc.)
    4. Concatenate into a structured markdown document
    """
    repo_dir = expert_dir / "raw" / "repos" / source.id
    repo_dir.mkdir(parents=True, exist_ok=True)

    clone_target = repo_dir / "checkout"

    # Step 1: Shallow clone (or pull if already cloned)
    if (clone_target / ".git").exists():
        log(f"    Repo already cloned, pulling latest...")
        proc = await asyncio.create_subprocess_exec(
            "git", "-C", str(clone_target), "pull", "--depth=1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
    else:
        if not shutil.which("git"):
            log("    ERROR: git not found")
            return None
        log(f"    Cloning {source.url} (shallow)...")
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth=1", source.url, str(clone_target),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace").strip()
            log(f"    Clone failed: {err}")
            return None

    # Step 2: Generate directory tree (max 3 levels, skip common noise)
    tree_lines = ["## Repository Structure\n```"]
    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".next", ".nuxt",
        "dist", "build", ".venv", "venv", ".tox", ".mypy_cache",
        ".pytest_cache", "coverage", ".cache", "vendor",
    }
    skip_exts = {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".lock"}

    def _walk_tree(path: Path, prefix: str = "", depth: int = 0):
        if depth > 3:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return
        dirs = [e for e in entries if e.is_dir() and e.name not in skip_dirs and not e.name.startswith(".")]
        files = [e for e in entries if e.is_file() and e.suffix not in skip_exts]

        for d in dirs:
            tree_lines.append(f"{prefix}{d.name}/")
            _walk_tree(d, prefix + "  ", depth + 1)
        for f in files[:30]:  # Cap files per directory
            tree_lines.append(f"{prefix}{f.name}")

    _walk_tree(clone_target)
    tree_lines.append("```\n")

    # Step 3: Identify and read key files
    key_patterns = [
        "README.md", "README.rst", "README",
        "CLAUDE.md", "SKILL.md", "AGENTS.md",
        "pyproject.toml", "package.json", "Cargo.toml", "go.mod",
        "setup.py", "setup.cfg",
        "Makefile", "Dockerfile", "docker-compose.yml",
        ".env.example",
    ]
    # Also find main entry points and configs
    code_patterns = [
        "main.py", "app.py", "server.py", "cli.py", "index.ts", "index.js",
        "config.py", "config.ts", "settings.py",
    ]

    sections = [f"# Repository: {source.title or source.url}\n"]
    sections.append("\n".join(tree_lines))

    total_chars = 0
    max_chars = 200_000  # ~50k tokens — fits comfortably in extraction context

    def _read_key_file(file_path: Path, label: str) -> Optional[str]:
        nonlocal total_chars
        if not file_path.exists() or not file_path.is_file():
            return None
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
        # Skip very large files
        if len(content) > 30_000:
            content = content[:30_000] + "\n\n[... truncated at 30,000 chars ...]"
        if total_chars + len(content) > max_chars:
            return None
        total_chars += len(content)
        rel_path = file_path.relative_to(clone_target)
        return f"\n## File: {rel_path}\n```\n{content}\n```\n"

    # Read key files first (highest priority)
    for pattern in key_patterns:
        for match in clone_target.rglob(pattern):
            if any(skip in match.parts for skip in skip_dirs):
                continue
            result = _read_key_file(match, pattern)
            if result:
                sections.append(result)

    # Then read code entry points
    for pattern in code_patterns:
        for match in clone_target.rglob(pattern):
            if any(skip in match.parts for skip in skip_dirs):
                continue
            result = _read_key_file(match, pattern)
            if result:
                sections.append(result)

    # Then scan for Python/JS/TS files with docstrings or skill-like content
    code_exts = {".py", ".ts", ".js", ".md"}
    for ext in code_exts:
        for match in sorted(clone_target.rglob(f"*{ext}"))[:50]:
            if any(skip in match.parts for skip in skip_dirs):
                continue
            if match.name in key_patterns + code_patterns:
                continue  # Already read
            if total_chars >= max_chars:
                break
            result = _read_key_file(match, f"source{ext}")
            if result:
                sections.append(result)

    transcript = "\n".join(sections)

    # Clean up clone to save disk
    # Keep it — user might want to re-run extraction with different params
    log(f"    Repo analyzed: {len(tree_lines)} tree entries, {total_chars:,} chars extracted")
    return transcript


async def _transcribe_podcast(
    source: Source,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
) -> Optional[str]:
    """Transcribe a podcast episode — download audio then Gemini."""
    import httpx

    audio_dir = expert_dir / "raw" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Download audio
    log(f"    Downloading podcast audio...")
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(source.url)
            resp.raise_for_status()
            audio_bytes = resp.content
    except Exception as e:
        log(f"    Download failed: {e}")
        return None

    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > 20:
        log(f"    Audio too large ({size_mb:.1f} MB). Skipping.")
        return None

    # Determine MIME type from URL
    mime_type = "audio/mpeg"
    if ".m4a" in source.url:
        mime_type = "audio/m4a"
    elif ".wav" in source.url:
        mime_type = "audio/wav"

    tracker.check_or_abort()
    await limiter.wait()
    text, in_tokens, out_tokens = await call_gemini_with_audio(
        audio_bytes, mime_type, TRANSCRIPTION_PROMPT
    )
    tracker.record("gemini-flash", in_tokens, out_tokens)

    return text if text else None


async def _transcribe_article(source: Source) -> Optional[str]:
    """Scrape article content from URL."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        log("    beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        return None

    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(source.url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; KnowledgeCloner/1.0)"
            })
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        log(f"    Article fetch failed: {e}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try common article selectors
    article = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"(content|post|article|entry)"))
        or soup.body
    )

    if not article:
        return None

    # Extract text with paragraph breaks
    paragraphs = []
    for p in article.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote"]):
        text = p.get_text(strip=True)
        if text and len(text) > 20:
            if p.name.startswith("h"):
                paragraphs.append(f"\n## {text}\n")
            elif p.name == "li":
                paragraphs.append(f"- {text}")
            elif p.name == "blockquote":
                paragraphs.append(f"> {text}")
            else:
                paragraphs.append(text)

    return "\n\n".join(paragraphs) if paragraphs else None
