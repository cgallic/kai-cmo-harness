"""
Analytics webhook router.

Exposes scripts/analytics CLI commands via HTTP endpoints.
"""

from fastapi import APIRouter, HTTPException

from gateway.models import AnalyticsRequest, WebhookResponse
from gateway.adapters.analytics_adapter import AnalyticsAdapter

router = APIRouter()
adapter = AnalyticsAdapter()


@router.post("/summary", response_model=WebhookResponse)
async def analytics_summary(request: AnalyticsRequest):
    """
    Get executive summary of all analytics.

    Equivalent to: python -m analytics.cli summary
    """
    try:
        data = adapter.get_summary(
            client=request.client,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/ga/overview", response_model=WebhookResponse)
async def ga_overview(request: AnalyticsRequest):
    """
    Get Google Analytics overview metrics.

    Equivalent to: python -m analytics.cli ga overview
    """
    try:
        data = adapter.get_ga_overview(
            client=request.client,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/ga/pages", response_model=WebhookResponse)
async def ga_pages(request: AnalyticsRequest):
    """
    Get top pages from Google Analytics.

    Equivalent to: python -m analytics.cli ga pages
    """
    try:
        data = adapter.get_ga_pages(
            client=request.client,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit
        )
        return WebhookResponse(success=True, data={"pages": data})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/ga/sources", response_model=WebhookResponse)
async def ga_sources(request: AnalyticsRequest):
    """
    Get traffic sources from Google Analytics.

    Equivalent to: python -m analytics.cli ga sources
    """
    try:
        data = adapter.get_ga_sources(
            client=request.client,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit
        )
        return WebhookResponse(success=True, data={"sources": data})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/ga/channels", response_model=WebhookResponse)
async def ga_channels(request: AnalyticsRequest):
    """
    Get channel breakdown from Google Analytics.

    Equivalent to: python -m analytics.cli ga channels
    """
    try:
        data = adapter.get_ga_channels(
            client=request.client,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return WebhookResponse(success=True, data={"channels": data})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/gsc/queries", response_model=WebhookResponse)
async def gsc_queries(request: AnalyticsRequest):
    """
    Get top search queries from Search Console.

    Equivalent to: python -m analytics.cli gsc queries
    """
    try:
        data = adapter.get_gsc_queries(
            client=request.client,
            limit=request.limit
        )
        return WebhookResponse(success=True, data={"queries": data})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/gsc/opportunities", response_model=WebhookResponse)
async def gsc_opportunities(request: AnalyticsRequest):
    """
    Get SEO keyword opportunities from Search Console.

    Equivalent to: python -m analytics.cli gsc opportunities
    """
    try:
        data = adapter.get_gsc_opportunities(client=request.client)
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/db/leads", response_model=WebhookResponse)
async def db_leads(request: AnalyticsRequest):
    """
    Get recent leads from database.

    Equivalent to: python -m analytics.cli db leads
    """
    try:
        status = request.options.get("status")
        data = adapter.get_db_leads(
            client=request.client,
            limit=request.limit,
            status=status
        )
        return WebhookResponse(success=True, data={"leads": data})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/db/calls", response_model=WebhookResponse)
async def db_calls(request: AnalyticsRequest):
    """
    Get recent calls from database.

    Equivalent to: python -m analytics.cli db calls
    """
    try:
        data = adapter.get_db_calls(
            client=request.client,
            limit=request.limit
        )
        return WebhookResponse(success=True, data={"calls": data})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/db/funnel", response_model=WebhookResponse)
async def db_funnel(request: AnalyticsRequest):
    """
    Get conversion funnel from database.

    Equivalent to: python -m analytics.cli db funnel
    """
    try:
        data = adapter.get_db_funnel(client=request.client)
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/report/{report_type}", response_model=WebhookResponse)
async def generate_report(report_type: str, request: AnalyticsRequest):
    """
    Generate a specific report type.

    Report types: traffic, seo, content, leads, full

    Equivalent to: python -m analytics.cli report <type>
    """
    valid_types = ["traffic", "seo", "content", "leads", "full"]
    if report_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Must be one of: {', '.join(valid_types)}"
        )

    try:
        data = adapter.generate_report(
            report_type=report_type,
            client=request.client,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))
