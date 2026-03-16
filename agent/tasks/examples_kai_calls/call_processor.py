"""
Call Processor — reads every inbound Kai Calls transcript, analyzes the lead,
fills in their info, scores them, and decides next steps.

This is the sales/ops brain for the Kai Calls business itself.

Schedule: Every 5 minutes (*/5 * * * *)

Each tick:
1. Find calls we haven't processed yet
2. For each call: read transcript, extract who they are, what they need
3. Update lead record with enriched info
4. Score the lead (hot/warm/cold)
5. Decide next action and notify
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from ...llm import llm_router
from .client import kai_client


CALL_ANALYSIS_PROMPT = """You are the ops manager for Kai Calls, an AI voice agent platform for businesses.
Someone just called us. Read this transcript and tell me everything about this lead.

TRANSCRIPT:
{transcript}

CALL SUMMARY (from Vapi):
{summary}

EXISTING LEAD INFO (what we already know):
{existing_info}

Return a JSON object:
{{
  "caller": {{
    "first_name": "their first name or null",
    "last_name": "their last name or null",
    "company": "their business/company name or null",
    "role": "their job title or role or null",
    "phone": "phone number if mentioned or null",
    "email": "email if mentioned or null",
    "city": "city/location if mentioned or null",
    "state": "state if mentioned or null",
    "industry": "what industry they're in or null"
  }},
  "intent": {{
    "what_they_want": "1-2 sentence summary of what they're looking for",
    "use_case": "how they'd use Kai Calls (e.g. 'receptionist for law firm', 'appointment booking for dentist')",
    "current_solution": "what they're using now if mentioned or null",
    "pain_points": ["list of problems they mentioned"],
    "timeline": "how urgent - immediate/this_month/exploring/unknown",
    "budget_signals": "any pricing discussion or budget hints or null"
  }},
  "assessment": {{
    "score": 1-10,
    "temperature": "hot|warm|cold|spam",
    "reasoning": "why this score in 1 sentence",
    "next_action": "what we should do next (e.g. 'send pricing info', 'schedule demo', 'follow up in a week', 'not a fit')",
    "follow_up_message": "a short personalized message for the follow-up email or null if not needed"
  }},
  "notes": "anything else notable about this call - objections, questions asked, things we promised them"
}}

Be precise. Only fill in what was actually said, don't guess."""


class CallProcessorTask(BaseTask):
    """Processes inbound Kai Calls transcripts and works the lead."""

    @property
    def task_type(self) -> str:
        return "kai_call_processor"

    @property
    def description(self) -> str:
        return "Kai Calls: Process new call transcripts, enrich leads, decide next steps"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            # 1. Find unprocessed calls
            new_calls = await self._get_unprocessed_calls()

            if not new_calls:
                return {
                    "success": True,
                    "summary": "No new calls to process",
                    "data": {"processed": 0},
                }

            # 2. Process each call
            processed = 0
            hot_leads = []
            actions_taken = []

            for call in new_calls:
                result = await self._process_call(call)
                if result:
                    processed += 1
                    self._mark_processed(call["id"])

                    if result.get("temperature") in ("hot", "warm"):
                        hot_leads.append(result)

                    if result.get("action_taken"):
                        actions_taken.append(result["action_taken"])

            # 3. Notify about hot leads
            if hot_leads:
                msg = self._format_lead_alert(hot_leads)
                await self.send_notification(msg)

            return {
                "success": True,
                "summary": f"Processed {processed} calls, {len(hot_leads)} hot/warm leads",
                "data": {
                    "processed": processed,
                    "hot_leads": len(hot_leads),
                    "actions": actions_taken,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_unprocessed_calls(self) -> List[Dict[str, Any]]:
        """Get recent calls that we haven't analyzed yet."""
        # Track which calls we've processed in agent state
        processed_ids = set(state_manager.get("kai_processed_calls") or [])

        # Get calls from last 24h with transcripts
        calls = await kai_client.get_call_transcripts(hours=24, limit=30)

        # Filter to unprocessed, non-trivial calls (>10s)
        new_calls = [
            c for c in calls
            if c["id"] not in processed_ids
            and (c.get("duration") or 0) > 10
            and c.get("transcript")
        ]

        return new_calls

    async def _process_call(self, call: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single call — analyze transcript, update lead, decide action."""
        call_id = call["id"]
        lead_id = call.get("lead_id")

        # Get existing lead info if we have one
        existing_info = "No existing lead info"
        if lead_id:
            lead_data = await self._get_lead(lead_id)
            if lead_data:
                existing_info = json.dumps({
                    k: v for k, v in lead_data.items()
                    if v is not None and k in (
                        "name", "first_name", "last_name", "email", "phone",
                        "city", "state", "status", "notes", "source",
                    )
                }, indent=2)

        # Format transcript
        transcript_text = self._format_transcript(call.get("transcript"))
        if not transcript_text or len(transcript_text) < 50:
            return None

        # Analyze with LLM
        prompt = CALL_ANALYSIS_PROMPT.format(
            transcript=transcript_text[:4000],
            summary=call.get("summary") or "No summary available",
            existing_info=existing_info,
        )

        try:
            response = await llm_router.complete(
                prompt=prompt,
                task_type="kai_call_processor",
                max_tokens=1500,
                temperature=0.2,
            )
            analysis = self._parse_json(response)
        except Exception as e:
            print(f"[CallProcessor] LLM error for call {call_id[:8]}: {e}")
            return None

        if not analysis:
            return None

        # Update the lead with extracted info
        action_taken = None
        if lead_id:
            action_taken = await self._update_lead_from_analysis(lead_id, analysis, call)

        # Store analysis in agent state for reference
        state_manager.set_task_context(f"kai_call_{call_id[:8]}", {
            "call_id": call_id,
            "analysis": analysis,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })

        assessment = analysis.get("assessment", {})
        caller = analysis.get("caller", {})
        intent = analysis.get("intent", {})

        return {
            "call_id": call_id,
            "lead_id": lead_id,
            "name": f"{caller.get('first_name', '')} {caller.get('last_name', '')}".strip() or "Unknown",
            "company": caller.get("company"),
            "temperature": assessment.get("temperature", "unknown"),
            "score": assessment.get("score", 0),
            "what_they_want": intent.get("what_they_want", ""),
            "next_action": assessment.get("next_action", ""),
            "action_taken": action_taken,
        }

    async def _update_lead_from_analysis(
        self, lead_id: str, analysis: Dict[str, Any], call: Dict[str, Any]
    ) -> Optional[str]:
        """Push extracted info back into the lead record."""
        caller = analysis.get("caller", {})
        intent = analysis.get("intent", {})
        assessment = analysis.get("assessment", {})

        update: Dict[str, Any] = {}

        # Fill in missing fields — don't overwrite existing data with nulls
        lead = await self._get_lead(lead_id)
        if not lead:
            return None

        if caller.get("first_name") and not lead.get("first_name"):
            update["first_name"] = caller["first_name"]
        if caller.get("last_name") and not lead.get("last_name"):
            update["last_name"] = caller["last_name"]
        if caller.get("first_name") and caller.get("last_name") and not lead.get("name"):
            update["name"] = f"{caller['first_name']} {caller['last_name']}"
        if caller.get("email") and not lead.get("email"):
            update["email"] = caller["email"]
        if caller.get("phone") and not lead.get("phone"):
            update["phone"] = caller["phone"]
        if caller.get("city") and not lead.get("city"):
            update["city"] = caller["city"]
        if caller.get("state") and not lead.get("state"):
            update["state"] = caller["state"]

        # Build rich notes
        notes_parts = []
        if lead.get("notes"):
            notes_parts.append(lead["notes"])

        call_date = (call.get("created_at") or "")[:10]
        notes_parts.append(f"\n--- Agent Analysis ({call_date}) ---")

        if caller.get("company"):
            notes_parts.append(f"Company: {caller['company']}")
        if caller.get("role"):
            notes_parts.append(f"Role: {caller['role']}")
        if caller.get("industry"):
            notes_parts.append(f"Industry: {caller['industry']}")
        if intent.get("what_they_want"):
            notes_parts.append(f"Looking for: {intent['what_they_want']}")
        if intent.get("use_case"):
            notes_parts.append(f"Use case: {intent['use_case']}")
        if intent.get("current_solution"):
            notes_parts.append(f"Current solution: {intent['current_solution']}")
        if intent.get("pain_points"):
            notes_parts.append(f"Pain points: {', '.join(intent['pain_points'])}")
        if intent.get("timeline"):
            notes_parts.append(f"Timeline: {intent['timeline']}")
        if intent.get("budget_signals"):
            notes_parts.append(f"Budget: {intent['budget_signals']}")
        if assessment.get("next_action"):
            notes_parts.append(f"Next action: {assessment['next_action']}")
        if analysis.get("notes"):
            notes_parts.append(f"Notes: {analysis['notes']}")

        update["notes"] = "\n".join(notes_parts)

        # Update status based on temperature
        temp = assessment.get("temperature", "")
        if temp == "hot" and lead.get("status") not in ("contacted", "converted", "won"):
            update["status"] = "hot"
        elif temp == "warm" and lead.get("status") in (None, "new"):
            update["status"] = "warm"

        if not update:
            return None

        # Write to Supabase
        try:
            kai_client.supabase.table("leads").update(update).eq("id", lead_id).execute()
            return f"Updated lead {lead_id[:8]}: {', '.join(update.keys())}"
        except Exception as e:
            print(f"[CallProcessor] Failed to update lead {lead_id[:8]}: {e}")
            return None

    async def _get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a lead by ID."""
        result = (
            kai_client.supabase.table("leads")
            .select("*")
            .eq("id", lead_id)
            .single()
            .execute()
        )
        return result.data

    def _format_transcript(self, transcript: Any) -> str:
        """Convert transcript to readable text."""
        if not transcript:
            return ""
        if isinstance(transcript, str):
            return transcript
        if isinstance(transcript, list):
            lines = []
            for msg in transcript:
                role = msg.get("role", "unknown")
                content = msg.get("message", msg.get("content", ""))
                if content:
                    lines.append(f"{role}: {content}")
            return "\n".join(lines)
        return str(transcript)

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response."""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        return None

    def _mark_processed(self, call_id: str):
        """Mark a call as processed so we don't re-analyze it."""
        processed = state_manager.get("kai_processed_calls") or []
        processed.append(call_id)
        # Keep last 500 to prevent unbounded growth
        state_manager.set("kai_processed_calls", processed[-500:])

    def _format_lead_alert(self, leads: List[Dict[str, Any]]) -> str:
        """Format WhatsApp alert for hot/warm leads."""
        lines = [f"*New Leads ({len(leads)})*", ""]

        for lead in leads:
            temp_icon = {"hot": "!!", "warm": ""}.get(lead["temperature"], "")
            name = lead.get("name") or "Unknown"
            company = lead.get("company")
            score = lead.get("score", 0)

            header = f"*{name}*"
            if company:
                header += f" ({company})"
            header += f" — {lead['temperature']} {temp_icon} [{score}/10]"
            lines.append(header)

            if lead.get("what_they_want"):
                lines.append(f"  {lead['what_they_want']}")
            if lead.get("next_action"):
                lines.append(f"  Next: {lead['next_action']}")
            lines.append("")

        return "\n".join(lines)
