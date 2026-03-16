"""
Cold Email webhook router.

Exposes scripts/cold_email CLI commands via HTTP endpoints.
"""

from fastapi import APIRouter

from gateway.models import (
    WebhookRequest,
    WebhookResponse,
    AsyncJobResponse,
    WarmupStatusResponse,
)
from gateway.jobs import job_queue
from gateway.adapters.cold_email_adapter import ColdEmailAdapter

router = APIRouter()
adapter = ColdEmailAdapter()


@router.post("/warmup/status", response_model=WebhookResponse)
async def warmup_status(request: WebhookRequest):
    """
    Get warmup status for all accounts.

    Equivalent to: python -m scripts.cold_email warmup status
    """
    try:
        data = adapter.get_warmup_status()
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/warmup/ready", response_model=WebhookResponse)
async def warmup_ready(request: WebhookRequest):
    """
    Get accounts ready to send (14+ days warmup).

    Equivalent to: python -m scripts.cold_email warmup ready
    """
    try:
        data = adapter.get_accounts_ready()
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/accounts", response_model=WebhookResponse)
async def list_accounts(request: WebhookRequest):
    """
    List all Instantly accounts.

    Equivalent to: python -m scripts.cold_email instantly accounts
    """
    try:
        data = adapter.list_accounts()
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/campaigns", response_model=WebhookResponse)
async def list_campaigns(request: WebhookRequest):
    """
    List all Instantly campaigns.

    Equivalent to: python -m scripts.cold_email instantly campaigns
    """
    try:
        data = adapter.list_campaigns()
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/dashboard", response_model=WebhookResponse)
async def dashboard(request: WebhookRequest):
    """
    Get cold email infrastructure dashboard.

    Equivalent to: python -m scripts.cold_email dashboard
    """
    try:
        data = adapter.get_dashboard()
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/domain/check", response_model=WebhookResponse)
async def domain_check(request: WebhookRequest):
    """
    Check domain availability for a brand.

    Equivalent to: python -m scripts.cold_email domain check <brand>
    """
    brand = request.options.get("brand")
    count = request.options.get("count", 5)

    if not brand:
        return WebhookResponse(
            success=False,
            error="Missing 'brand' in options"
        )

    try:
        data = adapter.check_domain(brand=brand, count=count)
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/onboard", response_model=AsyncJobResponse)
async def onboard_domain(request: WebhookRequest):
    """
    Full domain onboarding (async).

    Equivalent to: python -m scripts.cold_email onboard-full <domain>
    """
    domain = request.options.get("domain")
    brand = request.options.get("brand")
    user = request.options.get("user")

    if not all([domain, brand, user]):
        return AsyncJobResponse(
            job_id="",
            status="failed",
            message="Missing required options: domain, brand, user"
        )

    job_id = job_queue.create_job(
        command="cold_email_onboard",
        client=request.client,
        options={
            "domain": domain,
            "brand": brand,
            "user": user,
            "first_name": request.options.get("first_name"),
            "last_name": request.options.get("last_name"),
        }
    )

    job_queue.submit_job(
        job_id,
        adapter.run_onboard,
        domain=domain,
        brand=brand,
        user=user,
        first_name=request.options.get("first_name"),
        last_name=request.options.get("last_name"),
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="pending",
        message=f"Domain onboarding job queued for {domain}"
    )


@router.post("/dns/setup", response_model=AsyncJobResponse)
async def dns_setup(request: WebhookRequest):
    """
    Setup DNS for a domain (async).

    Equivalent to: python -m scripts.cold_email dns setup <domain>
    """
    domain = request.options.get("domain")
    provider = request.options.get("provider", "google")

    if not domain:
        return AsyncJobResponse(
            job_id="",
            status="failed",
            message="Missing required option: domain"
        )

    job_id = job_queue.create_job(
        command="cold_email_dns_setup",
        client=request.client,
        options={"domain": domain, "provider": provider}
    )

    job_queue.submit_job(
        job_id,
        adapter.run_dns_setup,
        domain=domain,
        provider=provider,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="pending",
        message=f"DNS setup job queued for {domain}"
    )


@router.post("/spam-check", response_model=WebhookResponse)
async def spam_check(request: WebhookRequest):
    """
    Check email content for spam triggers.

    Equivalent to: python -m scripts.cold_email spam-check "<text>"
    """
    text = request.options.get("text")

    if not text:
        return WebhookResponse(
            success=False,
            error="Missing 'text' in options"
        )

    try:
        data = adapter.spam_check(text=text)
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/analytics/campaigns", response_model=WebhookResponse)
async def campaign_analytics(request: WebhookRequest):
    """
    Get analytics for all campaigns or a specific campaign.

    Returns: sent, opened, replied, bounced, unsubscribed counts and rates.
    """
    campaign_id = request.options.get("campaign_id")

    try:
        data = adapter.get_campaign_analytics(campaign_id=campaign_id)
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/analytics/summary", response_model=WebhookResponse)
async def analytics_summary(request: WebhookRequest):
    """
    Get summary analytics across all campaigns and accounts.

    Returns: total sent, open rate, reply rate, accounts warming, accounts ready.
    """
    try:
        data = adapter.get_analytics_summary()
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))
