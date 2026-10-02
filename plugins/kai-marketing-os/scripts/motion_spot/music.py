"""Generate hype scores with ElevenLabs Music (composition plan, instrumental, music_v1).

  python music.py trap stomp                          -> audio/eleven_trap.mp3, audio/eleven_stomp.mp3
  python music.py --custom mytag "120 BPM, ..., hard-hitting"
  python music.py --dry-run trap                      -> prints the plan, no API call, no key needed

Key: ELEVENLABS_API_KEY from the environment only. It is never printed or written anywhere.
Facts learned the hard way:
  * max 2 concurrent requests on the standard plan;
  * sections must be >= 3000 ms, and their timing is IGNORED: the drop lands wherever the model puts it,
    so always measure it with analyze.py and cut with build_score.py;
  * naming an artist or song gets the plan rejected as copyrighted;
  * a launch is hype by default: never let the look of a brand talk you into calm or ambient music.
Cost: billed per generated track (30 s each here). Check your ElevenLabs plan for the current rate.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

NEG = ["vocals", "singing", "lyrics", "spoken word", "rap verses", "tempo changes", "lo-fi", "chill", "ambient",
       "soft", "gentle", "corporate stock music", "ukulele", "acoustic guitar", "piano ballad", "cheesy"]

STYLES = {
    "trap": ["120 BPM", "hype hybrid trap anthem", "huge distorted 808 bass", "hard trap drums", "rapid hi-hat rolls",
             "massive snare hits", "epic brass stabs", "aggressive and triumphant", "stadium energy",
             "sports commercial", "premium sneaker ad energy", "hard-hitting", "loud modern master"],
    "festival": ["120 BPM", "big room festival EDM", "massive supersaw lead drop", "pounding sidechained kick",
                 "euphoric and explosive", "huge snare build with riser", "hands-in-the-air drop", "crowd-energy",
                 "hard-hitting", "loud modern master"],
    "stomp": ["120 BPM", "aggressive electronic stomp", "heavy distorted bass", "punchy four-on-the-floor kick",
              "big claps and stomps", "gritty synth riff", "bold, swaggering, cocky", "tech launch hype trailer",
              "product launch meets sneaker drop", "hard-hitting", "loud modern master"],
    "phonk": ["120 BPM", "hard electronic phonk", "cowbell melody", "distorted 808 slides", "punchy drums",
              "dark aggressive swagger", "viral short-video energy", "hard-hitting", "loud modern master"],
    "anthem": ["120 BPM", "uplifting electronic anthem", "driving four-on-the-floor", "bright synth hook",
               "confident and optimistic", "big build and drop", "hard-hitting", "loud modern master"],
}


def plan(style: list[str], build_ms: int = 6000, drop_ms: int = 20000, end_ms: int = 4000) -> dict:
    return {
        "positive_global_styles": style + ["instrumental"],
        "negative_global_styles": NEG,
        "sections": [
            {"section_name": "Build", "duration_ms": build_ms, "lines": [],
             "positive_local_styles": ["tense build", "accelerating snare roll", "rising riser", "anticipation",
                                       "one beat of silence right before the drop"],
             "negative_local_styles": ["full drop", "calm"]},
            {"section_name": "Drop", "duration_ms": drop_ms, "lines": [],
             "positive_local_styles": ["MASSIVE drop hitting on the first beat", "full power", "maximum energy",
                                       "chest-hitting low end", "catchy hook riff", "relentless drive"],
             "negative_local_styles": ["breakdown", "quiet", "slowing down"]},
            {"section_name": "Final hit", "duration_ms": end_ms, "lines": [],
             "positive_local_styles": ["one huge final impact hit", "ringing tail"],
             "negative_local_styles": ["drum loop", "new melody"]},
        ],
    }


def gen(tag: str, key: str) -> str:
    body = {"composition_plan": plan(STYLES[tag]), "model_id": "music_v1"}
    req = urllib.request.Request("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=400) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        return f"{tag} HTTP {e.code} {e.read().decode(errors='replace')[:400]}"
    out = Path("audio") / f"eleven_{tag}.mp3"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)
    return f"{tag} -> {out} {len(data)} bytes"


def main() -> None:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    if args[:1] == ["--custom"]:
        STYLES[args[1]] = [x.strip() for x in args[2].split(",")]
        tags = [args[1]]
    else:
        tags = args or ["trap", "stomp"]
    unknown = [t for t in tags if t not in STYLES]
    if unknown:
        sys.exit(f"unknown style(s) {unknown}; presets: {', '.join(STYLES)}")
    if dry:
        for t in tags:
            print(t, json.dumps(plan(STYLES[t]), indent=1))
        return
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set. Export it in your shell (never paste it into chat or a file in the repo).")
    with ThreadPoolExecutor(min(2, len(tags))) as ex:   # max 2 concurrent requests
        for r in ex.map(lambda t: gen(t, key), tags):
            print(r)


if __name__ == "__main__":
    main()
