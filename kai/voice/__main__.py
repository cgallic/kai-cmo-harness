"""Operator interface for voice memory. Inputs are JSON, outputs JSON/JSONL."""
import argparse
import json
from pathlib import Path

from .store import VoiceStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("command", choices=["profile", "example", "packet", "feedback",
                                            "export", "metrics", "calibrate", "replay", "outcome"])
    parser.add_argument("--input", required=True, help="JSON argument file")
    args = parser.parse_args()
    inputs = json.loads(Path(args.input).read_text())
    store = VoiceStore(args.db)
    if args.command in {"calibrate", "replay"}:
        from agent.llm.content import ContentClient
        from .evaluation import calibrate, compare_replay
        model = inputs.pop("model", None)
        if args.command == "calibrate":
            result = calibrate(store, judge=ContentClient("content_quality_review", model=model), **inputs)
        else:
            result = compare_replay(store, candidate=ContentClient(model=model), **inputs)
    else:
        result = getattr(store, args.command)(**inputs)
    if args.command == "export":
        for event in result:
            print(json.dumps(event, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
