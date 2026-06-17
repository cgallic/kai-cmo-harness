"""
OpenAI Ads webhook router.

Exposes scripts/ads/openai_ads*.py CLI commands via HTTP.
Reads, writes (campaigns/adgroups/ads + state), and Conversions API.
"""

from fastapi import APIRouter

from gateway.adapters.openai_ads_adapter import OpenAIAdsAdapter
from gateway.models import (
    OpenAIAdsAdCreate,
    OpenAIAdsAdGroupCreate,
    OpenAIAdsCampaignCreate,
    OpenAIAdsConversionRequest,
    OpenAIAdsRequest,
    OpenAIAdsStateRequest,
    OpenAIAdsUploadRequest,
    WebhookResponse,
)

router = APIRouter()
adapter = OpenAIAdsAdapter()


# ----------------------------------------------------------------------- reads

@router.post("/account", response_model=WebhookResponse)
async def account(_: OpenAIAdsRequest):
    """Ad account summary. Equivalent to: openai_ads.py account"""
    try:
        return WebhookResponse(success=True, data=adapter.account())
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/campaigns", response_model=WebhookResponse)
async def campaigns(req: OpenAIAdsRequest):
    """List campaigns. Equivalent to: openai_ads.py campaigns"""
    try:
        return WebhookResponse(success=True, data=adapter.campaigns(limit=req.limit))
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/campaign", response_model=WebhookResponse)
async def campaign(req: OpenAIAdsRequest):
    """Get one campaign. Equivalent to: openai_ads.py campaign --campaign_id=…"""
    if not req.campaign_id:
        return WebhookResponse(success=False, error="campaign_id required")
    try:
        return WebhookResponse(success=True, data=adapter.campaign(req.campaign_id))
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/adgroups", response_model=WebhookResponse)
async def adgroups(req: OpenAIAdsRequest):
    """Ad groups for a campaign. Equivalent to: openai_ads.py adgroups --campaign_id=…"""
    if not req.campaign_id:
        return WebhookResponse(success=False, error="campaign_id required")
    try:
        return WebhookResponse(success=True, data=adapter.adgroups(req.campaign_id, limit=req.limit))
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/ads", response_model=WebhookResponse)
async def ads(req: OpenAIAdsRequest):
    """Ads in an ad group. Equivalent to: openai_ads.py ads --ad_group_id=…"""
    if not req.ad_group_id:
        return WebhookResponse(success=False, error="ad_group_id required")
    try:
        return WebhookResponse(success=True, data=adapter.ads(req.ad_group_id, limit=req.limit))
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/insights", response_model=WebhookResponse)
async def insights(req: OpenAIAdsRequest):
    """Performance insights — scope by ad/adgroup/campaign or omit for account."""
    try:
        data = adapter.insights(
            ad_id=req.ad_id, ad_group_id=req.ad_group_id, campaign_id=req.campaign_id,
            granularity=req.granularity,
            fields=req.fields or "impressions,clicks,spend,ctr,cpc,cpm",
            time_ranges=req.time_ranges, aggregation_level=req.aggregation_level,
            limit=req.limit,
        )
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/spend", response_model=WebhookResponse)
async def spend(req: OpenAIAdsRequest):
    """Account spend rollup over last N days."""
    try:
        return WebhookResponse(success=True, data=adapter.spend(days=req.days))
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/dashboard", response_model=WebhookResponse)
async def dashboard(req: OpenAIAdsRequest):
    """Account + campaigns + recent spend snapshot."""
    try:
        return WebhookResponse(success=True, data=adapter.dashboard(days=req.days))
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


# ---------------------------------------------------------------------- writes

@router.post("/upload-image", response_model=WebhookResponse)
async def upload_image(req: OpenAIAdsUploadRequest):
    """Upload creative image — by file_path OR image_url. Returns {file_id}."""
    if not (req.file_path or req.image_url):
        return WebhookResponse(success=False, error="file_path or image_url required")
    try:
        if req.file_path:
            data = adapter.upload_image(req.file_path)
        else:
            data = adapter.upload_url(req.image_url)  # type: ignore[arg-type]
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/create-campaign", response_model=WebhookResponse)
async def create_campaign(req: OpenAIAdsCampaignCreate):
    try:
        data = adapter.create_campaign(name=req.name, budget_usd=req.budget_usd, status=req.status)
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/create-adgroup", response_model=WebhookResponse)
async def create_adgroup(req: OpenAIAdsAdGroupCreate):
    try:
        data = adapter.create_adgroup(
            campaign_id=req.campaign_id, name=req.name, bid_usd=req.bid_usd,
            status=req.status, context_hints=req.context_hints,
        )
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/create-ad", response_model=WebhookResponse)
async def create_ad(req: OpenAIAdsAdCreate):
    try:
        data = adapter.create_ad(
            ad_group_id=req.ad_group_id, name=req.name,
            headline=req.headline, description=req.description,
            link=req.link, file_id=req.file_id, status=req.status,
        )
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/state", response_model=WebhookResponse)
async def state(req: OpenAIAdsStateRequest):
    """Activate/pause/archive a campaign, adgroup, or ad."""
    try:
        return WebhookResponse(success=True, data=adapter.state(req.type, req.id, req.action))
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


# ----------------------------------------------------------------- conversions

@router.post("/conversion", response_model=WebhookResponse)
async def conversion(req: OpenAIAdsConversionRequest):
    """Send a single server-side conversion event."""
    try:
        data = adapter.conversion(
            event_id=req.event_id, type_=req.event_type,
            amount=req.amount, currency=req.currency,
            source_url=req.source_url, action_source=req.action_source,
            timestamp_ms=req.timestamp_ms, validate_only=req.validate_only,
        )
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))
