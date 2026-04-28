"""Unit tests for `validate_brand_lock` in knowledge.py.

The brand lock must distinguish IDENTITY DRIFT (Kai is described AS one of the
forbidden categories) from COMPARISON ANCHOR usage (the category appears as a
competitor Kai is positioned against, like "Receptionist: $3,500/mo. Kai: $69").

Run with: .venv/bin/python -m scripts.ads.autoreason.test_brand_lock
"""

from __future__ import annotations

from .knowledge import validate_brand_lock
from .trace import AdCopy


def _ad(headline: str = "", body: str = "", description: str = "") -> AdCopy:
    return AdCopy(
        headline=headline,
        primary_text=body,
        description=description,
        cta="LEARN_MORE",
        link="https://kaicalls.com",
    )


CASES: list[tuple[str, AdCopy, bool]] = [
    # name, ad, expect_violation
    (
        "Kai is an AI receptionist (identity drift)",
        _ad(headline="Kai is an AI receptionist for trades.",
            body="Set up in 4 minutes."),
        True,
    ),
    (
        "Receptionist price comparison (anchor — allow)",
        _ad(
            headline="You're paying $3,500/mo for a receptionist. Kai is $69.",
            body=(
                "Receptionist: $3,500/mo + benefits + sick days. "
                "Answering service: $1,500/mo + per-minute overages. "
                "Kai: $69/mo flat. No contract. No sick days. No hold music."
            ),
            description="The math doesn't lie.",
        ),
        False,
    ),
    (
        "Tried answering services then tried Kai (allow)",
        _ad(body=(
            "Tried one of those answering services. They put my customers on hold. "
            "Then I tried Kai. Booked three jobs the first day."
        )),
        False,
    ),
    (
        "Kai — your AI virtual assistant (identity drift via apposition)",
        _ad(headline="Kai — your AI virtual assistant for missed calls.",
            body="Try free."),
        True,
    ),
    (
        "Stop missing calls (no drift phrase — allow)",
        _ad(headline="Stop missing calls. Start booking jobs.",
            body="Your new business phone number with AI built in."),
        False,
    ),
    # ------- additional regression cases -------
    (
        "Fixture incumbent (must still reject)",
        _ad(
            headline="Never Miss a Call Again",
            body=(
                "Innovative AI receptionist for small business. Our seamless "
                "platform leverages cutting-edge technology to revolutionize "
                "how you handle missed calls. Start your free trial today!"
            ),
            description="AI Phone Answering",
        ),
        True,
    ),
    (
        "Kai: virtual receptionist (colon apposition — drift)",
        _ad(headline="Kai: the virtual receptionist that never sleeps."),
        True,
    ),
    (
        "Phone bot category contrast (allow)",
        _ad(body=(
            "Most phone bots sound like phone bots. Kai sounds like you, "
            "because Kai is your business phone number with AI built in."
        )),
        False,
    ),
    (
        "An answering service named Kai (drift)",
        _ad(body="Try Kai, an answering service built for tradesmen."),
        True,
    ),
    (
        "Auto attendant comparison with explicit contrast (allow)",
        _ad(body=(
            "Most auto attendants make customers press 1, press 2, press 3. "
            "Kai just answers and books the job."
        )),
        False,
    ),
]


def run() -> int:
    failures = 0
    for name, ad, expect_violation in CASES:
        hits = validate_brand_lock(ad)
        violated = bool(hits)
        status = "OK"
        if violated != expect_violation:
            failures += 1
            status = (
                f"FAIL  expected={'reject' if expect_violation else 'allow'} "
                f"got={'reject' if violated else 'allow'} hits={hits}"
            )
        print(f"  [{status}] {name}")
    print()
    if failures:
        print(f"{failures} / {len(CASES)} cases failed")
        return 1
    print(f"All {len(CASES)} cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
