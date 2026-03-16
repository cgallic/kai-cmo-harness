"""
Content Quality Scorer — Local Gate.

Thin approval layer on top of the quality scorer.
Score content → apply policy → auto-approve / hold / reject.
Stores proposals in local SQLite for audit trail.
"""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

from scripts.quality.types import QualityReport

# Default DB location
_DB_PATH = Path(__file__).parent / "gate.db"
_POLICY_DIR = Path(__file__).parent / "policies"


def _load_yaml(path: Path) -> dict:
    """Load a YAML file. Falls back to basic parsing if PyYAML not installed."""
    text = path.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text)
    # Minimal fallback for simple key: value YAML
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
            elif val.isdigit():
                val = int(val)
            elif val.replace(".", "", 1).isdigit():
                val = float(val)
            result[key.strip()] = val
    return result


class GateDB:
    """SQLite store for gate proposals."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or _DB_PATH
        self._conn = None
        self._ensure_schema()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _ensure_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                file_path TEXT,
                score REAL NOT NULL,
                grade TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                policy TEXT,
                violations_json TEXT,
                top_fixes_json TEXT,
                metadata_json TEXT,
                decision_reason TEXT,
                reviewed_by TEXT,
                created_at REAL NOT NULL,
                reviewed_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
            CREATE INDEX IF NOT EXISTS idx_proposals_created ON proposals(created_at);
        """)
        self.conn.commit()

    def insert(self, proposal: dict) -> str:
        self.conn.execute("""
            INSERT INTO proposals (id, content_hash, file_path, score, grade, status,
                                   policy, violations_json, top_fixes_json, metadata_json,
                                   decision_reason, created_at)
            VALUES (:id, :content_hash, :file_path, :score, :grade, :status,
                    :policy, :violations_json, :top_fixes_json, :metadata_json,
                    :decision_reason, :created_at)
        """, proposal)
        self.conn.commit()
        return proposal["id"]

    def get(self, proposal_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_by_status(self, status: str = "pending", limit: int = 50) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM proposals WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def list_recent(self, days: int = 30, limit: int = 100) -> List[dict]:
        since = time.time() - (days * 86400)
        rows = self.conn.execute(
            "SELECT * FROM proposals WHERE created_at >= ? ORDER BY created_at DESC LIMIT ?",
            (since, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, proposal_id: str, status: str,
                      reviewed_by: str = "human", reason: str = None):
        self.conn.execute("""
            UPDATE proposals SET status = ?, reviewed_by = ?, reviewed_at = ?,
                                 decision_reason = COALESCE(?, decision_reason)
            WHERE id = ?
        """, (status, reviewed_by, time.time(), reason, proposal_id))
        self.conn.commit()


def load_policy(policy_name: str) -> dict:
    """Load a policy YAML file by name."""
    path = _POLICY_DIR / f"{policy_name}.yaml"
    if not path.exists():
        # Try without extension
        path = _POLICY_DIR / policy_name
        if not path.exists():
            return _default_policy()
    return _load_yaml(path)


def _default_policy() -> dict:
    """Sensible defaults when no policy file exists."""
    return {
        "id": "default",
        "auto_approve_above": 85,
        "hold_between": [60, 85],
        "reject_below": 60,
        "require_rules_pass": [],
        "block_if_terms": [],
    }


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _proposal_id() -> str:
    """Generate a short proposal ID."""
    import random
    chars = "abcdefghjkmnpqrstuvwxyz23456789"
    return "gp-" + "".join(random.choices(chars, k=8))


def evaluate_proposal(report: QualityReport, policy: dict) -> Dict[str, Any]:
    """Apply policy rules to a quality report. Returns status + reason."""
    score = report.overall_score
    auto_above = policy.get("auto_approve_above", 85)
    reject_below = policy.get("reject_below", 60)
    required_rules = policy.get("require_rules_pass", [])
    block_terms = policy.get("block_if_terms", [])

    # Check required rules
    failed_required = []
    for cat in report.categories:
        for rule in cat.rules:
            if rule.rule_id in required_rules and not rule.passed:
                failed_required.append(rule.rule_id)

    if failed_required:
        return {
            "status": "rejected",
            "reason": f"Required rules failed: {', '.join(failed_required)}",
        }

    # Check blocked terms (scan violations for them)
    if block_terms:
        all_text = json.dumps(report.to_dict()).lower()
        for term in block_terms:
            if term.lower() in all_text:
                return {
                    "status": "rejected",
                    "reason": f'Blocked term found: "{term}"',
                }

    # Score-based decision
    if score >= auto_above:
        return {"status": "approved", "reason": f"Score {score:.0f} >= {auto_above} (auto-approve)"}
    elif score < reject_below:
        return {"status": "rejected", "reason": f"Score {score:.0f} < {reject_below} (auto-reject)"}
    else:
        return {"status": "pending", "reason": f"Score {score:.0f} in hold range ({reject_below}-{auto_above})"}


async def propose(
    content: str,
    file_path: str = "<stdin>",
    policy_name: str = "default",
    db_path: Path = None,
    engine_kwargs: dict = None,
) -> Dict[str, Any]:
    """Score content, apply policy, store proposal.

    Returns dict with: proposal_id, status, score, grade, reason, violations
    """
    from scripts.quality.engine import QualityEngine

    engine_kwargs = engine_kwargs or {}
    engine = QualityEngine(**engine_kwargs)
    report = await engine.score_content(content, file_path=file_path)

    policy = load_policy(policy_name)
    decision = evaluate_proposal(report, policy)

    db = GateDB(db_path)
    proposal_id = _proposal_id()

    violations = []
    for cat in report.categories:
        for rule in cat.rules:
            for v in rule.violations:
                violations.append({
                    "rule_id": rule.rule_id,
                    "line": v.line,
                    "text": v.text,
                    "fix": v.fix,
                })

    proposal = {
        "id": proposal_id,
        "content_hash": _content_hash(content),
        "file_path": file_path,
        "score": report.overall_score,
        "grade": report.overall_grade,
        "status": decision["status"],
        "policy": policy_name,
        "violations_json": json.dumps(violations[:20]),
        "top_fixes_json": json.dumps(report.top_fixes),
        "metadata_json": json.dumps(report.metadata),
        "decision_reason": decision["reason"],
        "created_at": time.time(),
    }
    db.insert(proposal)

    return {
        "proposal_id": proposal_id,
        "status": decision["status"],
        "score": round(report.overall_score, 1),
        "grade": report.overall_grade,
        "reason": decision["reason"],
        "violation_count": len(violations),
        "top_fixes": report.top_fixes,
        "policy": policy_name,
    }


def approve(proposal_id: str, reviewed_by: str = "human", db_path: Path = None) -> dict:
    """Approve a pending proposal."""
    db = GateDB(db_path)
    proposal = db.get(proposal_id)
    if not proposal:
        return {"error": f"Proposal {proposal_id} not found"}
    if proposal["status"] != "pending":
        return {"error": f"Proposal {proposal_id} is {proposal['status']}, not pending"}
    db.update_status(proposal_id, "approved", reviewed_by=reviewed_by)
    return {"proposal_id": proposal_id, "status": "approved"}


def reject(proposal_id: str, reason: str = "", reviewed_by: str = "human", db_path: Path = None) -> dict:
    """Reject a pending proposal."""
    db = GateDB(db_path)
    proposal = db.get(proposal_id)
    if not proposal:
        return {"error": f"Proposal {proposal_id} not found"}
    if proposal["status"] != "pending":
        return {"error": f"Proposal {proposal_id} is {proposal['status']}, not pending"}
    db.update_status(proposal_id, "rejected", reviewed_by=reviewed_by, reason=reason)
    return {"proposal_id": proposal_id, "status": "rejected", "reason": reason}


def list_proposals(status: str = "pending", days: int = 30, db_path: Path = None) -> List[dict]:
    """List proposals by status or recent history."""
    db = GateDB(db_path)
    if status == "all":
        return db.list_recent(days=days)
    return db.list_by_status(status=status)
