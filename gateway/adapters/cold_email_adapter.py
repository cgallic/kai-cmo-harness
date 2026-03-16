"""
Cold Email adapter.

Wraps scripts/cold_email modules for programmatic access.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure scripts path is available
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / "scripts" / ".env")

# Path to accounts storage
ACCOUNTS_FILE = Path(__file__).parent.parent.parent / "scripts" / "cold_email" / "accounts.json"


class ColdEmailAdapter:
    """Adapter for cold email CLI commands."""

    def _load_accounts_db(self) -> Dict:
        """Load accounts database from JSON file."""
        if ACCOUNTS_FILE.exists():
            with open(ACCOUNTS_FILE) as f:
                return json.load(f)
        return {"accounts": [], "domains": []}

    def get_warmup_status(self) -> Dict[str, Any]:
        """Get warmup status for all accounts."""
        try:
            from scripts.cold_email.instantly_client import InstantlyClient
            client = InstantlyClient()
        except (ValueError, ImportError) as e:
            return {"error": str(e), "accounts": []}

        response = client.list_accounts()
        if not response.success:
            return {"error": response.error, "accounts": []}

        accounts = response.data.get("items", [])
        warmup_accounts = [a for a in accounts if a.get("warmup_enabled")]

        # Get warmup analytics
        analytics_data = {}
        if warmup_accounts:
            emails = [a["email"] for a in warmup_accounts]
            analytics = client.get_warmup_analytics(emails)
            if analytics.success:
                for item in analytics.data.get("items", []):
                    analytics_data[item.get("email", "")] = item

        # Load local database for start dates
        db = self._load_accounts_db()
        db_accounts = {a["email"]: a for a in db.get("accounts", [])}

        result_accounts = []
        for acc in warmup_accounts:
            email = acc.get("email", "")
            stats = analytics_data.get(email, {})

            # Calculate days in warmup
            days_warming = None
            db_acc = db_accounts.get(email, {})
            warmup_start = db_acc.get("warmup_start_date")
            if warmup_start:
                try:
                    start_date = datetime.strptime(warmup_start, "%Y-%m-%d")
                    days_warming = (datetime.now() - start_date).days
                except ValueError:
                    pass

            result_accounts.append({
                "email": email,
                "status": acc.get("status", "unknown"),
                "sent_count": stats.get("sent_count", 0),
                "received_count": stats.get("received_count", 0),
                "warmup_reputation": stats.get("warmup_reputation", 0),
                "days_warming": days_warming,
                "ready": days_warming is not None and days_warming >= 14,
            })

        return {
            "accounts": result_accounts,
            "total_warming": len(warmup_accounts),
            "ready_to_send": sum(1 for a in result_accounts if a.get("ready")),
        }

    def get_accounts_ready(self) -> Dict[str, Any]:
        """Get accounts ready to send (14+ days warmup)."""
        try:
            from scripts.cold_email.instantly_client import InstantlyClient
            client = InstantlyClient()
        except (ValueError, ImportError) as e:
            return {"error": str(e), "ready": [], "almost_ready": []}

        response = client.list_accounts()
        if not response.success:
            return {"error": response.error, "ready": [], "almost_ready": []}

        accounts = response.data.get("items", [])

        # Load local database for start dates
        db = self._load_accounts_db()
        db_accounts = {a["email"]: a for a in db.get("accounts", [])}

        ready = []
        almost_ready = []

        for acc in accounts:
            email = acc.get("email", "")
            warmup_enabled = acc.get("warmup_enabled", False)

            db_acc = db_accounts.get(email, {})
            warmup_start = db_acc.get("warmup_start_date")

            if warmup_start:
                try:
                    start_date = datetime.strptime(warmup_start, "%Y-%m-%d")
                    days = (datetime.now() - start_date).days

                    if days >= 14:
                        ready.append({
                            "email": email,
                            "days_warming": days,
                            "warmup_enabled": warmup_enabled,
                        })
                    elif days >= 10:
                        almost_ready.append({
                            "email": email,
                            "days_warming": days,
                            "days_remaining": 14 - days,
                        })
                except ValueError:
                    pass

        return {
            "ready": ready,
            "almost_ready": almost_ready,
            "ready_count": len(ready),
            "almost_ready_count": len(almost_ready),
        }

    def list_accounts(self) -> Dict[str, Any]:
        """List all Instantly accounts."""
        try:
            from scripts.cold_email.instantly_client import InstantlyClient
            client = InstantlyClient()
        except (ValueError, ImportError) as e:
            return {"error": str(e), "accounts": []}

        response = client.list_accounts()
        if not response.success:
            return {"error": response.error, "accounts": []}

        accounts = response.data.get("items", [])
        return {
            "accounts": [
                {
                    "email": acc.get("email", ""),
                    "status": acc.get("status", "unknown"),
                    "warmup_enabled": acc.get("warmup_enabled", False),
                    "daily_limit": acc.get("daily_limit", 0),
                }
                for acc in accounts
            ],
            "total": len(accounts),
        }

    def list_campaigns(self) -> Dict[str, Any]:
        """List all Instantly campaigns."""
        try:
            from scripts.cold_email.instantly_client import InstantlyClient
            client = InstantlyClient()
        except (ValueError, ImportError) as e:
            return {"error": str(e), "campaigns": []}

        response = client.list_campaigns()
        if not response.success:
            return {"error": response.error, "campaigns": []}

        campaigns = response.data.get("items", [])
        return {
            "campaigns": [
                {
                    "id": c.get("id", ""),
                    "name": c.get("name", "Unnamed"),
                    "status": c.get("status", "unknown"),
                }
                for c in campaigns
            ],
            "total": len(campaigns),
        }

    def get_dashboard(self) -> Dict[str, Any]:
        """Get cold email infrastructure dashboard."""
        db = self._load_accounts_db()

        accounts = db.get("accounts", [])
        domains = db.get("domains", [])

        return {
            "accounts": {
                "total": len(accounts),
                "by_status": self._count_by_field(accounts, "status"),
            },
            "domains": {
                "total": len(domains),
                "dns_configured": sum(1 for d in domains if d.get("dns_configured")),
            },
            "summary": {
                "total_accounts": len(accounts),
                "total_domains": len(domains),
                "ready_for_warmup": sum(1 for a in accounts if a.get("status") == "ready"),
                "warming": sum(1 for a in accounts if a.get("warmup_enabled")),
            }
        }

    def _count_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Count items by a field value."""
        counts = {}
        for item in items:
            value = item.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def check_domain(self, brand: str, count: int = 5) -> Dict[str, Any]:
        """Check domain availability for a brand."""
        try:
            from scripts.cold_email.domain_manager import DomainManager
            manager = DomainManager()
        except (ValueError, ImportError) as e:
            return {"error": str(e), "results": []}

        results = manager.check_brand_domains(brand, count=count)

        return {
            "brand": brand,
            "results": [
                {
                    "domain": r.domain,
                    "available": r.available,
                    "price": r.price if r.available else None,
                }
                for r in results
            ],
            "available_count": sum(1 for r in results if r.available),
        }

    def run_onboard(
        self,
        domain: str,
        brand: str,
        user: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run full domain onboarding."""
        # This is a complex multi-step process
        # For now, return a stub indicating it would need manual intervention
        return {
            "domain": domain,
            "brand": brand,
            "user": user,
            "email": f"{user}@{domain}",
            "status": "manual_steps_required",
            "message": "Full onboarding requires manual app password generation. "
                       "Use CLI: python -m scripts.cold_email onboard-full {domain} --brand {brand} --user {user}",
            "next_steps": [
                f"1. Run: python -m scripts.cold_email onboard-full {domain} --brand {brand} --user {user}",
                "2. Complete 2FA setup in Google",
                "3. Generate app password",
                "4. Enter app password when prompted",
            ]
        }

    def run_dns_setup(
        self,
        domain: str,
        provider: str = "google"
    ) -> Dict[str, Any]:
        """Setup DNS for a domain."""
        try:
            from scripts.cold_email.dns_manager import DNSManager
            manager = DNSManager()
        except (ValueError, ImportError) as e:
            return {"error": str(e), "success": False}

        if provider == "google":
            result = manager.setup_google_workspace(domain, dry_run=False)
        else:
            result = manager.setup_zoho_mail(domain, dry_run=False)

        return {
            "domain": domain,
            "provider": provider,
            "success": result.success,
            "message": result.message,
        }

    def spam_check(self, text: str) -> Dict[str, Any]:
        """Check email content for spam triggers."""
        try:
            from scripts.cold_email.split_testing import SpamChecker
            checker = SpamChecker()
            result = checker.check(text)
            return {
                "text_length": len(text),
                "spam_score": result.score,
                "triggers": result.triggers,
                "is_safe": result.score < 50,
            }
        except ImportError:
            # Fallback basic check
            spam_words = [
                "free", "guarantee", "limited time", "act now", "urgent",
                "winner", "congratulations", "click here", "buy now",
                "!!!",  "???", "CAPS LOCK", "100%", "$$$",
            ]

            text_lower = text.lower()
            triggers = [word for word in spam_words if word.lower() in text_lower]

            return {
                "text_length": len(text),
                "triggers": triggers,
                "trigger_count": len(triggers),
                "is_safe": len(triggers) < 3,
            }

    def get_campaign_analytics(self, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get analytics for campaigns.

        Args:
            campaign_id: Optional specific campaign ID. If None, gets all campaigns.

        Returns:
            Campaign analytics with sent, opened, replied, bounced counts.
        """
        try:
            from scripts.cold_email.instantly_client import InstantlyClient
            client = InstantlyClient()
        except (ValueError, ImportError) as e:
            return {"error": str(e), "campaigns": []}

        if campaign_id:
            # Get specific campaign
            response = client.get_campaign_analytics(campaign_id)
            if not response.success:
                return {"error": response.error, "campaigns": []}
            return {
                "campaigns": [self._format_campaign_analytics(campaign_id, response.data)],
                "total": 1,
            }

        # Get all campaigns and their analytics
        campaigns_resp = client.list_campaigns()
        if not campaigns_resp.success:
            return {"error": campaigns_resp.error, "campaigns": []}

        campaigns = campaigns_resp.data.get("items", [])
        results = []

        for campaign in campaigns:
            cid = campaign.get("id", "")
            analytics_resp = client.get_campaign_analytics(cid)

            if analytics_resp.success:
                results.append(self._format_campaign_analytics(
                    cid,
                    analytics_resp.data,
                    name=campaign.get("name", "Unknown"),
                    status=campaign.get("status", "unknown")
                ))
            else:
                results.append({
                    "id": cid,
                    "name": campaign.get("name", "Unknown"),
                    "status": campaign.get("status", "unknown"),
                    "error": analytics_resp.error
                })

        return {
            "campaigns": results,
            "total": len(results),
        }

    def _format_campaign_analytics(
        self,
        campaign_id: str,
        data: Dict,
        name: str = "",
        status: str = ""
    ) -> Dict[str, Any]:
        """Format campaign analytics data."""
        sent = data.get("sent", 0) or 0
        opened = data.get("opened", 0) or 0
        replied = data.get("replied", 0) or 0
        bounced = data.get("bounced", 0) or 0
        unsubscribed = data.get("unsubscribed", 0) or 0

        return {
            "id": campaign_id,
            "name": name or data.get("name", "Unknown"),
            "status": status or data.get("status", "unknown"),
            "sent": sent,
            "opened": opened,
            "replied": replied,
            "bounced": bounced,
            "unsubscribed": unsubscribed,
            "open_rate": round((opened / sent * 100), 1) if sent > 0 else 0,
            "reply_rate": round((replied / sent * 100), 1) if sent > 0 else 0,
            "bounce_rate": round((bounced / sent * 100), 1) if sent > 0 else 0,
        }

    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get summary analytics across all campaigns and accounts.

        Returns aggregate metrics for quick dashboard view.
        """
        try:
            from scripts.cold_email.instantly_client import InstantlyClient
            client = InstantlyClient()
        except (ValueError, ImportError) as e:
            return {"error": str(e)}

        # Get account stats
        accounts_resp = client.list_accounts()
        accounts = accounts_resp.data.get("items", []) if accounts_resp.success else []

        total_accounts = len(accounts)
        warmup_accounts = [a for a in accounts if a.get("warmup_enabled")]
        active_accounts = [a for a in accounts if a.get("status") == "active"]

        # Get campaign stats
        campaigns_resp = client.list_campaigns()
        campaigns = campaigns_resp.data.get("items", []) if campaigns_resp.success else []

        total_campaigns = len(campaigns)
        active_campaigns = [c for c in campaigns if c.get("status") == "active"]

        # Aggregate campaign analytics
        total_sent = 0
        total_opened = 0
        total_replied = 0
        total_bounced = 0

        for campaign in campaigns:
            cid = campaign.get("id", "")
            analytics_resp = client.get_campaign_analytics(cid)
            if analytics_resp.success:
                data = analytics_resp.data
                total_sent += data.get("sent", 0) or 0
                total_opened += data.get("opened", 0) or 0
                total_replied += data.get("replied", 0) or 0
                total_bounced += data.get("bounced", 0) or 0

        # Load local DB for warmup tracking
        db = self._load_accounts_db()
        db_accounts = {a["email"]: a for a in db.get("accounts", [])}

        ready_count = 0
        for acc in warmup_accounts:
            email = acc.get("email", "")
            db_acc = db_accounts.get(email, {})
            warmup_start = db_acc.get("warmup_start_date")
            if warmup_start:
                try:
                    start_date = datetime.strptime(warmup_start, "%Y-%m-%d")
                    if (datetime.now() - start_date).days >= 14:
                        ready_count += 1
                except ValueError:
                    pass

        return {
            "accounts": {
                "total": total_accounts,
                "active": len(active_accounts),
                "warming": len(warmup_accounts),
                "ready_to_send": ready_count,
            },
            "campaigns": {
                "total": total_campaigns,
                "active": len(active_campaigns),
            },
            "totals": {
                "sent": total_sent,
                "opened": total_opened,
                "replied": total_replied,
                "bounced": total_bounced,
            },
            "rates": {
                "open_rate": round((total_opened / total_sent * 100), 1) if total_sent > 0 else 0,
                "reply_rate": round((total_replied / total_sent * 100), 1) if total_sent > 0 else 0,
                "bounce_rate": round((total_bounced / total_sent * 100), 1) if total_sent > 0 else 0,
            },
            "health": {
                "status": "healthy" if total_bounced / max(total_sent, 1) < 0.05 else "warning",
                "deliverability": round((1 - total_bounced / max(total_sent, 1)) * 100, 1),
            }
        }
