"""CLI/import alias for the shared Kai data collector."""

from __future__ import annotations

import sys

from scripts.audit.collect import collect_audit_data, collect_kai_data, collect_third_party_sources, main

__all__ = ["collect_audit_data", "collect_kai_data", "collect_third_party_sources", "main"]


if __name__ == "__main__":
    sys.exit(main())
