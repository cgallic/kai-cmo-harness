"""
Stripe Analytics - Read-only MRR and subscription tracking.

Usage:
    from scripts.analytics.stripe_analytics import StripeAnalytics

    stripe = StripeAnalytics()
    mrr = stripe.get_mrr()
    subs = stripe.get_subscriptions()
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# Try to load dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


BASE_URL = "https://api.stripe.com/v1"


@dataclass
class StripeSubscription:
    """Stripe subscription data."""
    id: str
    customer_id: str
    customer_email: str
    status: str
    plan_name: str
    amount: int  # cents
    currency: str
    interval: str  # month, year
    created_at: datetime
    current_period_end: datetime
    cancel_at_period_end: bool

    @property
    def mrr(self) -> float:
        """Calculate MRR contribution (normalize annual to monthly)."""
        if self.interval == "year":
            return self.amount / 12 / 100
        return self.amount / 100


class StripeAnalytics:
    """
    Read-only Stripe analytics for MRR tracking.

    Requires: STRIPE_API_KEY (read-only key recommended: rk_live_xxx)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Stripe analytics.

        Args:
            api_key: Stripe API key (read-only recommended).
                     Falls back to STRIPE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("STRIPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Stripe API key required. "
                "Set STRIPE_API_KEY environment variable or pass api_key parameter. "
                "Use a read-only key (rk_live_xxx) for security."
            )

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a GET request to Stripe API."""
        url = f"{BASE_URL}{endpoint}"

        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            url = f"{url}?{query}"

        request = Request(url)
        # Stripe uses HTTP Basic Auth with API key as username
        import base64
        credentials = base64.b64encode(f"{self.api_key}:".encode()).decode()
        request.add_header("Authorization", f"Basic {credentials}")

        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode())
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            raise Exception(f"Stripe API error {e.code}: {error_body}")
        except URLError as e:
            raise Exception(f"Network error: {e.reason}")

    def get_subscriptions(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[StripeSubscription]:
        """
        Get all subscriptions.

        Args:
            status: Filter by status (active, canceled, past_due, etc.)
            limit: Max subscriptions to return

        Returns:
            List of StripeSubscription objects
        """
        params = {"limit": limit, "expand[]": "data.customer"}
        if status:
            params["status"] = status

        data = self._request("/subscriptions", params)
        subscriptions = []

        for sub in data.get("data", []):
            customer = sub.get("customer", {})
            if isinstance(customer, str):
                customer_id = customer
                customer_email = ""
            else:
                customer_id = customer.get("id", "")
                customer_email = customer.get("email", "")

            # Get plan info
            items = sub.get("items", {}).get("data", [])
            if items:
                plan = items[0].get("plan", {}) or items[0].get("price", {})
                amount = plan.get("amount", 0) or 0
                interval = plan.get("interval", "month")
                plan_name = plan.get("nickname") or plan.get("product", "Unknown")
            else:
                amount = 0
                interval = "month"
                plan_name = "Unknown"

            subscriptions.append(StripeSubscription(
                id=sub.get("id", ""),
                customer_id=customer_id,
                customer_email=customer_email,
                status=sub.get("status", ""),
                plan_name=plan_name,
                amount=amount,
                currency=sub.get("currency", "usd"),
                interval=interval,
                created_at=datetime.fromtimestamp(sub.get("created", 0)),
                current_period_end=datetime.fromtimestamp(sub.get("current_period_end", 0)),
                cancel_at_period_end=sub.get("cancel_at_period_end", False),
            ))

        return subscriptions

    def get_mrr(self) -> Dict[str, Any]:
        """
        Calculate current MRR.

        Returns:
            Dict with MRR breakdown by plan, total, and trends.
        """
        active_subs = self.get_subscriptions(status="active")

        total_mrr = sum(sub.mrr for sub in active_subs)

        # Group by plan
        by_plan = {}
        for sub in active_subs:
            plan = sub.plan_name
            if plan not in by_plan:
                by_plan[plan] = {"count": 0, "mrr": 0}
            by_plan[plan]["count"] += 1
            by_plan[plan]["mrr"] += sub.mrr

        # Count by status
        all_subs = self.get_subscriptions()
        by_status = {}
        for sub in all_subs:
            status = sub.status
            by_status[status] = by_status.get(status, 0) + 1

        # Churning (cancel at period end)
        churning = [s for s in active_subs if s.cancel_at_period_end]
        at_risk_mrr = sum(s.mrr for s in churning)

        return {
            "mrr": round(total_mrr, 2),
            "currency": "usd",
            "active_subscriptions": len(active_subs),
            "by_plan": {
                plan: {
                    "count": data["count"],
                    "mrr": round(data["mrr"], 2)
                }
                for plan, data in sorted(by_plan.items(), key=lambda x: -x[1]["mrr"])
            },
            "by_status": by_status,
            "at_risk": {
                "count": len(churning),
                "mrr": round(at_risk_mrr, 2),
            },
            "health": {
                "churn_risk_percent": round(at_risk_mrr / total_mrr * 100, 1) if total_mrr > 0 else 0,
            }
        }

    def get_revenue_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get revenue summary for a period.

        Args:
            days: Number of days to look back

        Returns:
            Revenue summary with charges and refunds.
        """
        # Get charges
        start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
        charges_data = self._request("/charges", {
            "limit": 100,
            "created[gte]": start_ts
        })

        charges = charges_data.get("data", [])

        total_charged = sum(c.get("amount", 0) for c in charges if c.get("paid"))
        total_refunded = sum(c.get("amount_refunded", 0) for c in charges)
        successful = len([c for c in charges if c.get("paid")])
        failed = len([c for c in charges if not c.get("paid")])

        return {
            "period_days": days,
            "charges": {
                "total": len(charges),
                "successful": successful,
                "failed": failed,
            },
            "revenue": {
                "gross": round(total_charged / 100, 2),
                "refunded": round(total_refunded / 100, 2),
                "net": round((total_charged - total_refunded) / 100, 2),
            },
            "currency": "usd",
        }

    def get_customers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get customer list.

        Args:
            limit: Max customers to return

        Returns:
            List of customer dicts with basic info.
        """
        data = self._request("/customers", {"limit": limit})

        return [
            {
                "id": c.get("id", ""),
                "email": c.get("email", ""),
                "name": c.get("name", ""),
                "created_at": datetime.fromtimestamp(c.get("created", 0)).isoformat(),
                "currency": c.get("currency", "usd"),
            }
            for c in data.get("data", [])
        ]

    def get_overview(self) -> Dict[str, Any]:
        """
        Get complete Stripe overview for dashboard.

        Returns:
            Combined MRR, revenue, and subscription data.
        """
        mrr_data = self.get_mrr()
        revenue_data = self.get_revenue_summary(days=30)

        return {
            "mrr": mrr_data,
            "revenue_30d": revenue_data,
            "generated_at": datetime.now().isoformat(),
        }


# CLI for testing
def main():
    """Test Stripe analytics."""
    import argparse

    parser = argparse.ArgumentParser(description="Stripe Analytics CLI")
    parser.add_argument("command", choices=["mrr", "subs", "revenue", "overview"])
    parser.add_argument("--days", type=int, default=30, help="Days for revenue lookup")
    args = parser.parse_args()

    try:
        stripe = StripeAnalytics()
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    if args.command == "mrr":
        data = stripe.get_mrr()
        print(f"\n💰 MRR: ${data['mrr']:,.2f}")
        print(f"   Active subscriptions: {data['active_subscriptions']}")
        print(f"   At-risk MRR: ${data['at_risk']['mrr']:,.2f} ({data['at_risk']['count']} subs)")
        print("\n   By Plan:")
        for plan, info in data['by_plan'].items():
            print(f"     - {plan}: {info['count']} subs, ${info['mrr']:,.2f}/mo")

    elif args.command == "subs":
        subs = stripe.get_subscriptions()
        print(f"\n📊 {len(subs)} Subscriptions:")
        for sub in subs[:10]:
            status_icon = "✅" if sub.status == "active" else "⚠️"
            print(f"   {status_icon} {sub.customer_email or sub.customer_id}: ${sub.mrr:.2f}/mo ({sub.status})")
        if len(subs) > 10:
            print(f"   ... and {len(subs) - 10} more")

    elif args.command == "revenue":
        data = stripe.get_revenue_summary(days=args.days)
        print(f"\n💵 Revenue ({args.days} days):")
        print(f"   Gross: ${data['revenue']['gross']:,.2f}")
        print(f"   Refunded: ${data['revenue']['refunded']:,.2f}")
        print(f"   Net: ${data['revenue']['net']:,.2f}")
        print(f"   Charges: {data['charges']['successful']} successful, {data['charges']['failed']} failed")

    elif args.command == "overview":
        data = stripe.get_overview()
        print(json.dumps(data, indent=2, default=str))

    return 0


if __name__ == "__main__":
    exit(main())
