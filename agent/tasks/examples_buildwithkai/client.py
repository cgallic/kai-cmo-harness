"""
BuildWithKai Supabase client.

READ-only observer — connects to BWK's Supabase with service role key.
No writes to the production app; agent_actions table logs what we observe.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from supabase import create_client, Client


class BWKClient:
    """
    Client for reading BuildWithKai data.

    All operations are READ via Supabase service role key.
    Writes only go to the agent_actions audit table.
    """

    def __init__(self):
        self._supabase: Optional[Client] = None

    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            url = os.getenv("BWK_SUPABASE_URL", "")
            key = os.getenv("BWK_SUPABASE_KEY", "")
            if not url or not key:
                raise RuntimeError("BWK_SUPABASE_URL and BWK_SUPABASE_KEY must be set")
            self._supabase = create_client(url, key)
        return self._supabase

    # =========================================================================
    # Product Generations
    # =========================================================================

    async def get_recent_generations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get product generations from the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("instant_products")
            .select("id, user_id, status, progress, error_message, is_published, created_at, updated_at")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_stuck_generations(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """Get generations stuck in processing for over N minutes."""
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        result = (
            self.supabase.table("instant_products")
            .select("id, user_id, status, progress, error_message, created_at, updated_at")
            .in_("status", ["processing", "generating", "pending"])
            .lt("updated_at", cutoff)
            .execute()
        )
        return result.data or []

    async def get_failed_generations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failed product generations in the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("instant_products")
            .select("id, user_id, status, progress, error_message, created_at")
            .eq("status", "error")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_generation_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated generation metrics."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("instant_products")
            .select("id, status, is_published, created_at")
            .gte("created_at", cutoff)
            .execute()
        )
        products = result.data or []

        by_status: Dict[str, int] = {}
        for p in products:
            status = p.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        published = sum(1 for p in products if p.get("is_published"))

        return {
            "total": len(products),
            "by_status": by_status,
            "completed": by_status.get("completed", 0),
            "failed": by_status.get("error", 0),
            "processing": by_status.get("processing", 0) + by_status.get("generating", 0) + by_status.get("pending", 0),
            "published": published,
            "error_rate": round((by_status.get("error", 0) / max(len(products), 1)) * 100, 1),
        }

    # =========================================================================
    # Users & Activation
    # =========================================================================

    async def get_user_profiles(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get user profiles created in the last N days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("user_profiles")
            .select("id, onboarding_step, subscription_plan, engagement_level, created_at, updated_at")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_user_funnel_data(self) -> Dict[str, Any]:
        """Get activation funnel metrics across all users."""
        # Total users
        users_result = (
            self.supabase.table("user_profiles")
            .select("id, onboarding_step, subscription_plan, engagement_level, created_at")
            .execute()
        )
        users = users_result.data or []

        # Business plans created
        plans_result = (
            self.supabase.table("business_plans")
            .select("id, user_id, status, created_at")
            .execute()
        )
        plans = plans_result.data or []

        # Products created
        products_result = (
            self.supabase.table("instant_products")
            .select("id, user_id, status, is_published, created_at")
            .execute()
        )
        products = products_result.data or []

        users_with_plans = len(set(p["user_id"] for p in plans if p.get("user_id")))
        users_with_products = len(set(p["user_id"] for p in products if p.get("user_id")))
        users_with_published = len(set(
            p["user_id"] for p in products
            if p.get("user_id") and p.get("is_published")
        ))

        return {
            "total_users": len(users),
            "users_with_plans": users_with_plans,
            "users_with_products": users_with_products,
            "users_with_published": users_with_published,
            "plans_total": len(plans),
            "products_total": len(products),
            "by_subscription": _count_by(users, "subscription_plan"),
            "by_engagement": _count_by(users, "engagement_level"),
        }

    async def get_inactive_users(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get users with no activity in the last N days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("user_profiles")
            .select("id, onboarding_step, subscription_plan, engagement_level, created_at, updated_at")
            .lt("updated_at", cutoff)
            .execute()
        )
        return result.data or []

    async def get_stuck_users(self, hours: int = 48) -> List[Dict[str, Any]]:
        """Get users who signed up but haven't progressed past onboarding."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("user_profiles")
            .select("id, onboarding_step, subscription_plan, created_at, updated_at")
            .lt("created_at", cutoff)
            .in_("onboarding_step", ["signed_up", "profile_created", "plan_selected"])
            .execute()
        )
        return result.data or []

    # =========================================================================
    # Revenue & Products
    # =========================================================================

    async def get_published_products(self) -> List[Dict[str, Any]]:
        """Get all published products with revenue data."""
        result = (
            self.supabase.table("instant_products")
            .select("id, user_id, status, is_published, total_revenue, stripe_product_id, created_at")
            .eq("is_published", True)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_product_sales(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent product sales."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("product_sales")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_product_downloads(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent product downloads."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("product_downloads")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_revenue_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get revenue metrics for the last N days."""
        published = await self.get_published_products()
        sales = await self.get_product_sales(days=days)
        downloads = await self.get_product_downloads(days=days)

        total_revenue = sum(p.get("total_revenue") or 0 for p in published)
        products_with_stripe = sum(1 for p in published if p.get("stripe_product_id"))
        products_without_stripe = sum(1 for p in published if not p.get("stripe_product_id"))

        # Products with downloads but no Stripe (missed money)
        download_product_ids = set(d.get("product_id") for d in downloads if d.get("product_id"))
        products_by_id = {p["id"]: p for p in published}
        missed_revenue = [
            pid for pid in download_product_ids
            if pid in products_by_id and not products_by_id[pid].get("stripe_product_id")
        ]

        return {
            "total_published": len(published),
            "total_revenue": total_revenue,
            "products_with_stripe": products_with_stripe,
            "products_without_stripe": products_without_stripe,
            "recent_sales": len(sales),
            "recent_downloads": len(downloads),
            "missed_revenue_products": len(missed_revenue),
            "missed_revenue_ids": missed_revenue[:10],
        }

    # =========================================================================
    # Conversations & Activity
    # =========================================================================

    async def get_recent_conversations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent chat conversations."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("conversations")
            .select("id, user_id, created_at, updated_at")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    # =========================================================================
    # Business Plans
    # =========================================================================

    async def get_business_plan_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get business plan generation stats."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("business_plans")
            .select("id, status, progress, error_message, created_at")
            .gte("created_at", cutoff)
            .execute()
        )
        plans = result.data or []

        by_status: Dict[str, int] = {}
        for p in plans:
            status = p.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total": len(plans),
            "by_status": by_status,
            "failed": sum(1 for p in plans if p.get("error_message")),
        }

    # =========================================================================
    # Funnels
    # =========================================================================

    async def get_funnel_stats(self) -> Dict[str, Any]:
        """Get funnel generation stats."""
        result = (
            self.supabase.table("funnels")
            .select("id, status, progress, created_at")
            .execute()
        )
        funnels = result.data or []

        by_status: Dict[str, int] = {}
        for f in funnels:
            status = f.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total": len(funnels),
            "by_status": by_status,
        }

    # =========================================================================
    # Quality Checks
    # =========================================================================

    async def get_completed_products_for_audit(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recently completed products for quality audit."""
        result = (
            self.supabase.table("instant_products")
            .select("*")
            .eq("status", "completed")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

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
            pass  # Non-critical — don't fail tasks over audit logging


def _count_by(items: List[Dict], key: str) -> Dict[str, int]:
    """Count items by a field value."""
    counts: Dict[str, int] = {}
    for item in items:
        val = item.get(key) or "none"
        counts[val] = counts.get(val, 0) + 1
    return counts


# Global client instance
bwk_client = BWKClient()
