"""
Kai Calls API client.

Wraps Supabase (direct DB reads) and Kai Calls API (action endpoints).
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from supabase import create_client, Client


class KaiCallsClient:
    """
    Client for interacting with the Kai Calls platform.

    READ operations go directly to Supabase (service role key).
    WRITE operations go through the Kai Calls API (X-API-Key auth).
    """

    def __init__(self):
        self._supabase: Optional[Client] = None
        self._api_url = os.getenv("KAICALLS_API_URL", "").rstrip("/")
        self._service_key = os.getenv("KAICALLS_SERVICE_KEY", "")

    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            url = os.getenv("KAICALLS_SUPABASE_URL", "")
            key = os.getenv("KAICALLS_SUPABASE_KEY", "")
            if not url or not key:
                raise RuntimeError("KAICALLS_SUPABASE_URL and KAICALLS_SUPABASE_KEY must be set")
            self._supabase = create_client(url, key)
        return self._supabase

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self._service_key,
            "Content-Type": "application/json",
        }

    # =========================================================================
    # READ — via Supabase service role
    # =========================================================================

    async def get_pending_emails(self) -> List[Dict[str, Any]]:
        """Get all emails in the approval queue with status='pending'."""
        result = (
            self.supabase.table("email_approval_queue")
            .select("*, businesses:business_id(id, name), leads:lead_id(id, name, email, phone)")
            .eq("status", "pending")
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []

    async def get_stale_emails(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get pending emails older than `minutes` minutes."""
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        result = (
            self.supabase.table("email_approval_queue")
            .select("*, businesses:business_id(id, name), leads:lead_id(id, name, email)")
            .eq("status", "pending")
            .lt("created_at", cutoff)
            .execute()
        )
        return result.data or []

    async def get_failed_emails(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get emails that failed to send in the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("email_approval_queue")
            .select("*, businesses:business_id(id, name), leads:lead_id(id, name, email)")
            .eq("status", "failed")
            .gte("created_at", cutoff)
            .execute()
        )
        return result.data or []

    async def get_recent_calls(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get calls from the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("calls")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_new_leads(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get leads created in the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("leads")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_businesses(self) -> List[Dict[str, Any]]:
        """Get all businesses with settings."""
        result = (
            self.supabase.table("businesses")
            .select("*")
            .execute()
        )
        return result.data or []

    async def get_agents(self) -> List[Dict[str, Any]]:
        """Get all Vapi agents."""
        result = (
            self.supabase.table("agents")
            .select("*")
            .execute()
        )
        return result.data or []

    async def get_call_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get aggregated call metrics for the last N days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        calls_result = (
            self.supabase.table("calls")
            .select("id, duration, status, created_at, business_id")
            .gte("created_at", cutoff)
            .execute()
        )
        calls = calls_result.data or []

        total = len(calls)
        total_duration = sum(c.get("duration", 0) or 0 for c in calls)
        avg_duration = total_duration / total if total > 0 else 0

        # Calls per day
        by_day: Dict[str, int] = {}
        for c in calls:
            day = c.get("created_at", "")[:10]
            by_day[day] = by_day.get(day, 0) + 1

        return {
            "total_calls": total,
            "total_duration_minutes": round(total_duration / 60, 1),
            "avg_duration_seconds": round(avg_duration, 1),
            "calls_per_day": by_day,
            "daily_average": round(total / max(days, 1), 1),
        }

    async def get_email_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get email queue stats for the last N days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("email_approval_queue")
            .select("id, status, created_at")
            .gte("created_at", cutoff)
            .execute()
        )
        emails = result.data or []

        by_status: Dict[str, int] = {}
        for e in emails:
            status = e.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total": len(emails),
            "by_status": by_status,
            "sent": by_status.get("sent", 0),
            "pending": by_status.get("pending", 0),
            "failed": by_status.get("failed", 0),
            "rejected": by_status.get("rejected", 0),
        }

    async def get_onboarding_status(self) -> List[Dict[str, Any]]:
        """Get businesses signed up in last 14 days with their setup status."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        result = (
            self.supabase.table("businesses")
            .select("*")
            .gte("created_at", cutoff)
            .execute()
        )
        businesses = result.data or []

        statuses = []
        for biz in businesses:
            biz_id = biz["id"]

            # Check agents
            agents = self.supabase.table("agents").select("id, phone_number").eq("business_id", biz_id).execute()
            agent_list = agents.data or []

            # Check email accounts
            emails = self.supabase.table("connected_email_accounts").select("id").eq("business_id", biz_id).eq("is_active", True).execute()

            # Check calls
            calls = self.supabase.table("calls").select("id").eq("business_id", biz_id).limit(1).execute()

            has_agent = len(agent_list) > 0
            has_phone = any(a.get("phone_number") for a in agent_list)
            has_email = len(emails.data or []) > 0
            has_calls = len(calls.data or []) > 0

            statuses.append({
                "business_id": biz_id,
                "business_name": biz.get("name", "Unknown"),
                "created_at": biz.get("created_at"),
                "profile_complete": bool(biz.get("name") and biz.get("category")),
                "has_agent": has_agent,
                "has_phone": has_phone,
                "has_email_account": has_email,
                "has_calls": has_calls,
            })

        return statuses

    async def get_call_transcripts(self, hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent call transcripts for quality analysis."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        result = (
            self.supabase.table("calls")
            .select("id, business_id, agent_id, transcript, summary, analysis, duration, status, created_at")
            .gte("created_at", cutoff)
            .not_.is_("transcript", "null")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    # =========================================================================
    # WRITE — via Kai Calls API with X-API-Key
    # =========================================================================

    async def _api_request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Kai Calls API."""
        if not self._api_url:
            raise RuntimeError("KAICALLS_API_URL not set")

        url = f"{self._api_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._headers(),
                json=json,
            )
            response.raise_for_status()
            return response.json()

    async def approve_email(self, email_id: str) -> Dict[str, Any]:
        """Approve and send a queued email."""
        return await self._api_request("POST", f"/api/email-approval/{email_id}/approve")

    async def send_email(self, lead_id: str, subject: str, body: str, business_id: str) -> Dict[str, Any]:
        """Send an email directly to a lead."""
        return await self._api_request("POST", f"/api/leads/{lead_id}/send-email", json={
            "businessId": business_id,
            "subject": subject,
            "emailBody": body,
        })

    async def update_lead(self, lead_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a lead's status/notes."""
        return await self._api_request("PATCH", f"/api/leads/{lead_id}", json=data)

    async def update_vapi_prompt(self, assistant_id: str, new_prompt: str, reason: str = "") -> Dict[str, Any]:
        """Update a Vapi assistant's system prompt."""
        return await self._api_request("POST", "/api/agent/vapi-update", json={
            "assistant_id": assistant_id,
            "system_prompt": new_prompt,
            "reason": reason,
        })

    async def auto_send_queue(self) -> Dict[str, Any]:
        """Batch approve and send all pending emails for auto-approve businesses."""
        return await self._api_request("POST", "/api/agent/email-queue/auto-send")

    async def get_system_status(self) -> Dict[str, Any]:
        """Get system health snapshot from the agent status endpoint."""
        return await self._api_request("GET", "/api/agent/status")


# Global client instance
kai_client = KaiCallsClient()
