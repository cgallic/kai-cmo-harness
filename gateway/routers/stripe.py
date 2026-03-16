"""
Stripe analytics router - Read-only MRR and subscription tracking.
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


router = APIRouter()


class MRRResponse(BaseModel):
    """MRR response model."""
    success: bool
    mrr: Optional[float] = None
    currency: str = "usd"
    active_subscriptions: Optional[int] = None
    by_plan: Optional[dict] = None
    at_risk: Optional[dict] = None
    error: Optional[str] = None


class RevenueResponse(BaseModel):
    """Revenue response model."""
    success: bool
    period_days: Optional[int] = None
    revenue: Optional[dict] = None
    charges: Optional[dict] = None
    error: Optional[str] = None


def _get_stripe_client():
    """Get Stripe analytics client."""
    try:
        from scripts.analytics.stripe_analytics import StripeAnalytics
        return StripeAnalytics()
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stripe not configured: {e}"
        )
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stripe module error: {e}"
        )


@router.get("/mrr", response_model=MRRResponse)
async def get_mrr():
    """
    Get current MRR (Monthly Recurring Revenue).

    Returns:
        MRR breakdown by plan, total, and at-risk subscriptions.
    """
    try:
        stripe = _get_stripe_client()
        data = stripe.get_mrr()

        return MRRResponse(
            success=True,
            mrr=data["mrr"],
            currency=data["currency"],
            active_subscriptions=data["active_subscriptions"],
            by_plan=data["by_plan"],
            at_risk=data["at_risk"],
        )
    except HTTPException:
        raise
    except Exception as e:
        return MRRResponse(success=False, error=str(e))


@router.get("/revenue")
async def get_revenue(days: int = 30):
    """
    Get revenue summary for a period.

    Args:
        days: Number of days to look back (default 30)

    Returns:
        Gross revenue, refunds, net revenue, and charge counts.
    """
    try:
        stripe = _get_stripe_client()
        data = stripe.get_revenue_summary(days=days)

        return {
            "success": True,
            **data
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/subscriptions")
async def get_subscriptions(status: Optional[str] = None, limit: int = 100):
    """
    Get subscription list.

    Args:
        status: Filter by status (active, canceled, past_due, etc.)
        limit: Max subscriptions to return

    Returns:
        List of subscriptions with plan and customer info.
    """
    try:
        stripe = _get_stripe_client()
        subs = stripe.get_subscriptions(status=status, limit=limit)

        return {
            "success": True,
            "subscriptions": [
                {
                    "id": s.id,
                    "customer_email": s.customer_email,
                    "status": s.status,
                    "plan": s.plan_name,
                    "mrr": s.mrr,
                    "interval": s.interval,
                    "cancel_at_period_end": s.cancel_at_period_end,
                    "current_period_end": s.current_period_end.isoformat(),
                }
                for s in subs
            ],
            "count": len(subs),
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/customers")
async def get_customers(limit: int = 100):
    """
    Get customer list.

    Args:
        limit: Max customers to return

    Returns:
        List of customers with basic info.
    """
    try:
        stripe = _get_stripe_client()
        customers = stripe.get_customers(limit=limit)

        return {
            "success": True,
            "customers": customers,
            "count": len(customers),
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/overview")
async def get_overview():
    """
    Get complete Stripe overview.

    Returns:
        Combined MRR, revenue, and subscription data for dashboard.
    """
    try:
        stripe = _get_stripe_client()
        data = stripe.get_overview()

        return {
            "success": True,
            **data
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}
