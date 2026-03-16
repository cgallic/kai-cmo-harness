"""
Clients router.

Provides access to client configuration data.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from gateway.config import config
from gateway.models import ClientInfo, WebhookResponse

router = APIRouter()


@router.get("", response_model=WebhookResponse)
async def list_clients(category: Optional[str] = None):
    """
    List all configured clients.

    Optional query param: category (products, clients, leadgen, personal, internal)
    """
    clients = config.get_all_clients()

    if category:
        valid_categories = ["products", "clients", "leadgen", "personal", "internal"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        clients = [c for c in clients if c.get("category") == category]

    return WebhookResponse(
        success=True,
        data={
            "clients": [
                {
                    "id": c["id"],
                    "name": c.get("name", c["id"]),
                    "category": c.get("category"),
                    "description": c.get("description"),
                    "url": c.get("url"),
                    "status": c.get("status"),
                    "ga_property": c.get("ga_property"),
                    "gsc_site": c.get("gsc_site"),
                }
                for c in clients
            ],
            "total": len(clients)
        }
    )


@router.get("/{client_id}", response_model=WebhookResponse)
async def get_client(client_id: str):
    """
    Get details for a specific client.
    """
    client = config.get_client(client_id)

    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Client '{client_id}' not found"
        )

    return WebhookResponse(
        success=True,
        data={
            "client": client
        }
    )


@router.get("/{client_id}/analytics-config", response_model=WebhookResponse)
async def get_client_analytics_config(client_id: str):
    """
    Get analytics configuration for a client (GA property, GSC site, Supabase).
    """
    client = config.get_client(client_id)

    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Client '{client_id}' not found"
        )

    return WebhookResponse(
        success=True,
        data={
            "client_id": client_id,
            "ga_property": client.get("ga_property"),
            "gsc_site": client.get("gsc_site"),
            "supabase": client.get("supabase"),
            "has_ga": bool(client.get("ga_property")),
            "has_gsc": bool(client.get("gsc_site")),
            "has_supabase": bool(client.get("supabase")),
        }
    )
