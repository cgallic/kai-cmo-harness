"""
WhatsApp webhook router for the CMO Gateway.

Handles incoming Twilio WhatsApp webhooks and routes messages to the agent.
"""

import hashlib
import hmac
from typing import Optional

from fastapi import APIRouter, Form, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.channels.whatsapp import whatsapp_channel
from agent.config import agent_config


router = APIRouter()


def verify_twilio_signature(
    signature: str,
    url: str,
    params: dict
) -> bool:
    """
    Verify that a request came from Twilio.

    Uses HMAC-SHA1 to verify the X-Twilio-Signature header.
    """
    if not agent_config.twilio_auth_token:
        # Skip verification if token not configured (dev mode)
        return True

    # Build the data string
    data = url
    for key in sorted(params.keys()):
        data += key + params[key]

    # Calculate expected signature
    expected = hmac.new(
        agent_config.twilio_auth_token.encode(),
        data.encode(),
        hashlib.sha1
    ).digest()

    import base64
    expected_b64 = base64.b64encode(expected).decode()

    return hmac.compare_digest(signature, expected_b64)


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(default=""),
    From: str = Form(default=""),
    To: str = Form(default=""),
    MessageSid: Optional[str] = Form(default=None),
    AccountSid: Optional[str] = Form(default=None),
    x_twilio_signature: Optional[str] = Header(default=None, alias="X-Twilio-Signature")
):
    """
    Handle incoming WhatsApp messages from Twilio.

    This endpoint receives webhook calls from Twilio when a WhatsApp message
    is received. It processes the message and returns a TwiML response.
    """
    # Extract phone number (remove 'whatsapp:' prefix)
    sender = From.replace("whatsapp:", "")
    message = Body.strip()

    # TODO: Fix signature validation with reverse proxy URL
    # Disabled temporarily - Caddy proxy changes the URL which breaks validation
    # if agent_config.twilio_auth_token and x_twilio_signature:
    #     form_data = await request.form()
    #     params = {k: v for k, v in form_data.items()}
    #     url = str(request.url)
    #     if not verify_twilio_signature(x_twilio_signature, url, params):
    #         raise HTTPException(status_code=403, detail="Invalid signature")

    # Check if sender is authorized (owner phone or allowed list)
    if not _is_authorized(sender):
        response_text = "Unauthorized. This agent only responds to authorized users."
    else:
        # Process the message
        try:
            response_text = await whatsapp_channel.process_incoming(
                sender=sender,
                message=message,
                raw_data={
                    "message_sid": MessageSid,
                    "account_sid": AccountSid,
                    "to": To
                }
            )
        except Exception as e:
            response_text = f"Error processing message: {str(e)}"

    # Return TwiML response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{_escape_xml(response_text)}</Message>
</Response>"""

    return PlainTextResponse(content=twiml, media_type="application/xml")


@router.get("/status")
async def whatsapp_status():
    """
    Get WhatsApp channel status.
    """
    from agent.state import state_manager

    agent_state = state_manager.get_agent_state()

    return {
        "channel": "whatsapp",
        "enabled": agent_config.whatsapp_enabled,
        "configured": bool(agent_config.twilio_account_sid),
        "agent_status": "paused" if agent_state.paused else "running",
        "running_tasks": len(agent_state.current_tasks)
    }


@router.post("/send")
async def send_whatsapp(
    recipient: str,
    message: str
):
    """
    Send a WhatsApp message (for testing/internal use).
    """
    if not agent_config.twilio_account_sid:
        return {
            "success": False,
            "error": "Twilio not configured"
        }

    success = await whatsapp_channel.send_message(recipient, message)

    return {
        "success": success,
        "recipient": recipient,
        "message_length": len(message)
    }


def _is_authorized(phone_number: str) -> bool:
    """Check if a phone number is authorized to use the agent."""
    # Always allow the owner
    if phone_number == agent_config.agent_owner_phone:
        return True

    # Check allowed list from state/config
    from agent.state import state_manager
    allowed = state_manager.get("allowed_phones", [])

    return phone_number in allowed


def _escape_xml(text: str) -> str:
    """Escape special characters for XML/TwiML."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
