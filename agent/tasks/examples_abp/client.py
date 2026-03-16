"""
Amazing Backyard Parties Supabase client.

READ-only observer — connects to ABP's Supabase with service role key.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from supabase import create_client, Client


class ABPClient:
    """
    Client for reading Amazing Backyard Parties data.

    All operations are READ via Supabase service role key.
    Writes only go to the agent_actions audit table.
    """

    def __init__(self):
        self._supabase: Optional[Client] = None

    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            url = os.getenv("ABP_SUPABASE_URL", "")
            key = os.getenv("ABP_SUPABASE_KEY", "")
            if not url or not key:
                raise RuntimeError("ABP_SUPABASE_URL and ABP_SUPABASE_KEY must be set")
            self._supabase = create_client(url, key)
        return self._supabase

    # =========================================================================
    # Leads
    # =========================================================================

    async def get_recent_leads(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get leads from the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("leads")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_unmatched_leads(self) -> List[Dict[str, Any]]:
        """Get leads without a vendor match."""
        result = (
            self.supabase.table("leads")
            .select("*")
            .is_("vendor_id", "null")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return result.data or []

    async def get_lead_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get aggregated lead metrics."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("leads")
            .select("id, vendor_id, event_type, zip_code, created_at")
            .gte("created_at", cutoff)
            .execute()
        )
        leads = result.data or []

        matched = sum(1 for l in leads if l.get("vendor_id"))
        by_event_type: Dict[str, int] = {}
        for l in leads:
            et = l.get("event_type") or "unknown"
            by_event_type[et] = by_event_type.get(et, 0) + 1

        by_day: Dict[str, int] = {}
        for l in leads:
            day = (l.get("created_at") or "")[:10]
            by_day[day] = by_day.get(day, 0) + 1

        return {
            "total": len(leads),
            "matched": matched,
            "unmatched": len(leads) - matched,
            "match_rate": round((matched / max(len(leads), 1)) * 100, 1),
            "by_event_type": by_event_type,
            "by_day": by_day,
            "daily_average": round(len(leads) / max(days, 1), 1),
        }

    async def get_high_value_leads(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent leads with upcoming events or large party indicators."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("leads")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        leads = result.data or []

        high_value = []
        now = datetime.now(timezone.utc)
        for lead in leads:
            is_high = False
            reasons = []

            # Upcoming event (within 14 days)
            event_date = lead.get("event_date")
            if event_date:
                try:
                    ed = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
                    days_until = (ed - now).days
                    if 0 <= days_until <= 14:
                        is_high = True
                        reasons.append(f"event in {days_until}d")
                except (ValueError, TypeError):
                    pass

            # Multiple services requested
            services = lead.get("services") or []
            if len(services) >= 3:
                is_high = True
                reasons.append(f"{len(services)} services")

            if is_high:
                lead["_high_value_reasons"] = reasons
                high_value.append(lead)

        return high_value

    # =========================================================================
    # Vendors
    # =========================================================================

    async def get_vendors(self) -> List[Dict[str, Any]]:
        """Get all active vendors."""
        result = (
            self.supabase.table("vendors")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_vendor_coverage(self) -> Dict[str, Any]:
        """Get vendor ZIP code coverage map."""
        # Get all vendor-zip mappings
        zipcodes_result = (
            self.supabase.table("vendor_zipcodes")
            .select("vendor_id, zip_code")
            .execute()
        )
        mappings = zipcodes_result.data or []

        # Get leads to find demand ZIPs
        leads_result = (
            self.supabase.table("leads")
            .select("zip_code, vendor_id")
            .execute()
        )
        leads = leads_result.data or []

        # Coverage: ZIPs with vendors
        covered_zips = set(m["zip_code"] for m in mappings if m.get("zip_code"))

        # Demand: ZIPs with leads
        demand_zips: Dict[str, int] = {}
        for l in leads:
            zc = l.get("zip_code")
            if zc:
                demand_zips[zc] = demand_zips.get(zc, 0) + 1

        # Gaps: ZIPs with leads but no vendors
        gap_zips = {
            zc: count for zc, count in demand_zips.items()
            if zc not in covered_zips
        }

        # Vendors per ZIP
        vendors_per_zip: Dict[str, int] = {}
        for m in mappings:
            zc = m.get("zip_code", "")
            vendors_per_zip[zc] = vendors_per_zip.get(zc, 0) + 1

        return {
            "total_covered_zips": len(covered_zips),
            "total_demand_zips": len(demand_zips),
            "gap_zips": dict(sorted(gap_zips.items(), key=lambda x: -x[1])[:20]),
            "gap_count": len(gap_zips),
            "vendors_per_zip": vendors_per_zip,
        }

    async def get_discovered_vendors(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recently discovered vendors (via Google Maps scraping)."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("discovered_vendors")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_vendor_funnel(self) -> Dict[str, Any]:
        """Get discovered vendor conversion funnel."""
        result = (
            self.supabase.table("discovered_vendors")
            .select("id, invite_email_sent, signup_completed, created_at")
            .execute()
        )
        vendors = result.data or []

        total = len(vendors)
        invited = sum(1 for v in vendors if v.get("invite_email_sent"))
        signed_up = sum(1 for v in vendors if v.get("signup_completed"))

        return {
            "discovered": total,
            "invited": invited,
            "signed_up": signed_up,
            "invite_rate": round((invited / max(total, 1)) * 100, 1),
            "signup_rate": round((signed_up / max(invited, 1)) * 100, 1),
            "pending_invite": total - invited,
            "pending_signup": invited - signed_up,
        }

    async def get_pending_vendor_signups(self, hours: int = 48) -> List[Dict[str, Any]]:
        """Get discovered vendors invited but not signed up after N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("discovered_vendors")
            .select("*")
            .eq("invite_email_sent", True)
            .eq("signup_completed", False)
            .lt("created_at", cutoff)
            .execute()
        )
        return result.data or []

    # =========================================================================
    # SEO / Page Performance
    # =========================================================================

    async def get_page_performance(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get page performance data (from GSC sync)."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("page_performance")
            .select("*")
            .gte("created_at", cutoff)
            .order("clicks", desc=True)
            .limit(100)
            .execute()
        )
        return result.data or []

    async def get_seo_stats(self) -> Dict[str, Any]:
        """Get aggregated SEO metrics."""
        result = (
            self.supabase.table("page_performance")
            .select("url, clicks, impressions, ctr, position")
            .order("clicks", desc=True)
            .limit(200)
            .execute()
        )
        pages = result.data or []

        total_clicks = sum(p.get("clicks") or 0 for p in pages)
        total_impressions = sum(p.get("impressions") or 0 for p in pages)
        avg_position = 0
        if pages:
            positions = [p.get("position") or 0 for p in pages if p.get("position")]
            avg_position = round(sum(positions) / max(len(positions), 1), 1)

        avg_ctr = round((total_clicks / max(total_impressions, 1)) * 100, 2)

        return {
            "total_pages": len(pages),
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "avg_ctr": avg_ctr,
            "avg_position": avg_position,
            "top_pages": pages[:10],
        }

    # =========================================================================
    # Agent Actions (audit log)
    # =========================================================================

    async def log_action(self, action_type: str, target_id: str = None,
                         previous_value: str = None, new_value: str = None,
                         reason: str = None):
        """Log an agent action for audit trail."""
        try:
            self.supabase.table("agent_actions").insert({
                "action_type": action_type,
                "target_id": target_id,
                "previous_value": previous_value,
                "new_value": new_value,
                "reason": reason,
                "status": "completed",
            }).execute()
        except Exception:
            pass


# Global client instance
abp_client = ABPClient()
