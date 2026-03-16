"""
Lead Processor — analyzes new leads, checks vendor matching, alerts on high-value.

Schedule: Every 15 minutes (*/15 * * * *)

Each tick:
1. Check for new unprocessed leads
2. Analyze event type, urgency, services requested
3. Flag high-value leads (upcoming events, large parties)
4. Alert on unmatched leads in coverage gaps
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from ...llm import llm_router
from .client import abp_client


LEAD_ANALYSIS_PROMPT = """You are the ops manager for Amazing Backyard Parties, a marketplace connecting
party hosts with local vendors (bounce houses, catering, entertainment, etc.).

Analyze this new lead and provide a quick assessment:

LEAD DATA:
Name: {name}
Email: {email}
Phone: {phone}
ZIP: {zip_code}
Event Date: {event_date}
Event Type: {event_type}
Services Requested: {services}
Vendor Matched: {vendor_matched}

Return a JSON object:
{{
  "urgency": "immediate|this_week|this_month|future|unknown",
  "value": "high|medium|low",
  "reasoning": "1 sentence why this value/urgency",
  "suggested_action": "what we should do (e.g., 'priority vendor match', 'send options email', 'add to nurture')"
}}

Be brief and practical."""


class LeadProcessorTask(BaseTask):
    """Processes new leads for Amazing Backyard Parties."""

    @property
    def task_type(self) -> str:
        return "abp_lead_processor"

    @property
    def description(self) -> str:
        return "ABP: Process new leads, analyze urgency, alert on high-value"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            # Track which leads we've processed
            processed_ids = set(state_manager.get("abp_processed_leads") or [])

            # Get recent leads
            leads = await abp_client.get_recent_leads(hours=24)
            new_leads = [l for l in leads if l["id"] not in processed_ids]

            if not new_leads:
                return {
                    "success": True,
                    "summary": "No new leads to process",
                    "data": {"processed": 0},
                }

            processed = 0
            high_value = []
            unmatched = []
            alerts: List[str] = []

            for lead in new_leads[:20]:  # Cap at 20 per tick
                # Quick analysis — only use LLM for leads with enough data
                analysis = None
                if lead.get("event_type") or lead.get("services"):
                    analysis = await self._analyze_lead(lead)

                processed += 1
                processed_ids.add(lead["id"])

                # Track high-value
                if analysis and analysis.get("value") == "high":
                    high_value.append({
                        "lead": lead,
                        "analysis": analysis,
                    })

                # Track unmatched
                if not lead.get("vendor_id"):
                    unmatched.append(lead)

            # Keep last 500 IDs
            state_manager.set("abp_processed_leads", list(processed_ids)[-500:])

            # Alert on high-value leads
            if high_value:
                lines = [f"*ABP High-Value Leads ({len(high_value)})*\n"]
                for hv in high_value[:5]:
                    lead = hv["lead"]
                    analysis = hv["analysis"]
                    name = lead.get("name") or lead.get("email") or "Unknown"
                    lines.append(f"*{name}*")
                    lines.append(f"  Event: {lead.get('event_type', 'N/A')}")
                    lines.append(f"  Date: {lead.get('event_date', 'N/A')}")
                    lines.append(f"  Services: {', '.join(lead.get('services') or ['N/A'])}")
                    lines.append(f"  Urgency: {analysis.get('urgency', 'unknown')}")
                    lines.append(f"  Action: {analysis.get('suggested_action', 'N/A')}")
                    if not lead.get("vendor_id"):
                        lines.append("  NO VENDOR MATCHED")
                    lines.append("")
                await self.send_notification("\n".join(lines))

            # Alert on unmatched leads in bulk
            if len(unmatched) >= 3:
                alerts.append(f"{len(unmatched)} leads with no vendor match in last 24h")

            return {
                "success": True,
                "summary": f"Processed {processed} leads, {len(high_value)} high-value, {len(unmatched)} unmatched",
                "data": {
                    "processed": processed,
                    "high_value": len(high_value),
                    "unmatched": len(unmatched),
                    "alerts": alerts,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _analyze_lead(self, lead: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use LLM to quickly assess a lead."""
        prompt = LEAD_ANALYSIS_PROMPT.format(
            name=lead.get("name") or "N/A",
            email=lead.get("email") or "N/A",
            phone=lead.get("phone") or "N/A",
            zip_code=lead.get("zip_code") or "N/A",
            event_date=lead.get("event_date") or "N/A",
            event_type=lead.get("event_type") or "N/A",
            services=", ".join(lead.get("services") or []) or "N/A",
            vendor_matched="Yes" if lead.get("vendor_id") else "No",
        )

        try:
            response = await llm_router.complete(
                prompt=prompt,
                task_type="abp_lead_processor",
                max_tokens=300,
                temperature=0.2,
            )
            return self._parse_json(response)
        except Exception as e:
            print(f"[LeadProcessor] LLM error for lead {lead['id'][:8]}: {e}")
            return None

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        import json
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        return None
