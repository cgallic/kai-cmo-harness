"""
OpenAI Ads adapter.

Thin subprocess wrapper around scripts/ads/openai_ads*.py — same shell-out
convention as scripts/ads/ad_loop.py uses for meta_ads_create.py. Keeps
validation/exit logic inside the CLI scripts and isolates failures from
the gateway process.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADS_DIR = REPO_ROOT / "scripts" / "ads"

READ_SCRIPT = ADS_DIR / "openai_ads.py"
WRITE_SCRIPT = ADS_DIR / "openai_ads_create.py"
CONV_SCRIPT = ADS_DIR / "openai_ads_conversions.py"


class OpenAIAdsAdapter:
    """Adapter for the OpenAI Ads CLI scripts."""

    # ------------------------------------------------------------------ helpers
    def _run(self, script: Path, args: List[str]) -> Dict[str, Any]:
        cmd = [sys.executable, str(script), *args]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        out = proc.stdout.strip()
        if proc.returncode != 0:
            return {
                "error": f"{script.name} exited {proc.returncode}",
                "stderr": proc.stderr.strip(),
                "stdout": out,
            }
        if not out:
            return {}
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {"raw": out}

    @staticmethod
    def _kv(opts: Dict[str, Any]) -> List[str]:
        """{a: 1, b: 'x'} -> ['--a=1', '--b=x'] (skips Nones/empties)."""
        return [f"--{k}={v}" for k, v in opts.items() if v is not None and v != ""]

    # ------------------------------------------------------------------- reads
    def account(self) -> Dict[str, Any]:
        return self._run(READ_SCRIPT, ["account"])

    def campaigns(self, limit: int = 100) -> Dict[str, Any]:
        return self._run(READ_SCRIPT, ["campaigns", *self._kv({"limit": limit})])

    def campaign(self, campaign_id: str) -> Dict[str, Any]:
        return self._run(READ_SCRIPT, ["campaign", *self._kv({"campaign_id": campaign_id})])

    def adgroups(self, campaign_id: str, limit: int = 100) -> Dict[str, Any]:
        return self._run(READ_SCRIPT, ["adgroups", *self._kv({"campaign_id": campaign_id, "limit": limit})])

    def ads(self, ad_group_id: str, limit: int = 100) -> Dict[str, Any]:
        return self._run(READ_SCRIPT, ["ads", *self._kv({"ad_group_id": ad_group_id, "limit": limit})])

    def insights(
        self,
        ad_id: Optional[str] = None,
        ad_group_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        granularity: str = "daily",
        fields: str = "impressions,clicks,spend,ctr,cpc,cpm",
        time_ranges: Optional[str] = None,
        aggregation_level: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        opts = {
            "ad_id": ad_id, "ad_group_id": ad_group_id, "campaign_id": campaign_id,
            "granularity": granularity, "fields": fields, "limit": limit,
            "time_ranges": time_ranges, "aggregation_level": aggregation_level,
        }
        return self._run(READ_SCRIPT, ["insights", *self._kv(opts)])

    def spend(self, days: int = 30) -> Dict[str, Any]:
        return self._run(READ_SCRIPT, ["spend", *self._kv({"days": days})])

    def dashboard(self, days: int = 7) -> Dict[str, Any]:
        return self._run(READ_SCRIPT, ["dashboard", *self._kv({"days": days})])

    # ------------------------------------------------------------------- writes
    def upload_image(self, file_path: str) -> Dict[str, Any]:
        return self._run(WRITE_SCRIPT, ["upload-image", f"--file={file_path}"])

    def upload_url(self, image_url: str) -> Dict[str, Any]:
        return self._run(WRITE_SCRIPT, ["upload-url", f"--image-url={image_url}"])

    def create_campaign(self, name: str, budget_usd: float, status: str = "paused") -> Dict[str, Any]:
        return self._run(WRITE_SCRIPT, ["create-campaign",
                                         f"--name={name}", f"--budget-usd={budget_usd}", f"--status={status}"])

    def create_adgroup(
        self, campaign_id: str, name: str, bid_usd: float,
        status: str = "paused", context_hints: Optional[str] = None,
    ) -> Dict[str, Any]:
        args = ["create-adgroup",
                f"--campaign-id={campaign_id}", f"--name={name}",
                f"--bid-usd={bid_usd}", f"--status={status}"]
        if context_hints:
            args.append(f"--context-hints={context_hints}")
        return self._run(WRITE_SCRIPT, args)

    def create_ad(
        self, ad_group_id: str, name: str, headline: str, description: str,
        link: str, file_id: str, status: str = "paused",
    ) -> Dict[str, Any]:
        return self._run(WRITE_SCRIPT, ["create-ad",
                                         f"--ad-group-id={ad_group_id}", f"--name={name}",
                                         f"--headline={headline}", f"--description={description}",
                                         f"--link={link}", f"--file-id={file_id}",
                                         f"--status={status}"])

    def state(self, type_: str, id_: str, action: str) -> Dict[str, Any]:
        if action not in {"activate", "pause", "archive"}:
            return {"error": f"Invalid action: {action}"}
        if type_ not in {"campaign", "adgroup", "ad"}:
            return {"error": f"Invalid type: {type_}"}
        return self._run(WRITE_SCRIPT, [action, f"--type={type_}", f"--id={id_}"])

    # -------------------------------------------------------------- conversions
    def conversion(
        self, event_id: str, type_: str, amount: int = 0, currency: str = "USD",
        source_url: Optional[str] = None, action_source: str = "web",
        timestamp_ms: Optional[int] = None, validate_only: bool = False,
    ) -> Dict[str, Any]:
        cmd = "validate" if validate_only else "send"
        args = [cmd, f"--event-id={event_id}", f"--type={type_}",
                f"--amount={amount}", f"--currency={currency}",
                f"--action-source={action_source}"]
        if source_url:
            args.append(f"--source-url={source_url}")
        if timestamp_ms is not None:
            args.append(f"--timestamp-ms={timestamp_ms}")
        return self._run(CONV_SCRIPT, args)

    def conversion_batch(self, file_path: str, validate_only: bool = False) -> Dict[str, Any]:
        args = ["batch", f"--file={file_path}"]
        if validate_only:
            args.append("--validate-only")
        return self._run(CONV_SCRIPT, args)
