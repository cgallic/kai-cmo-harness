"""
Lead outreach task - manages lead generation and email warmup.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..llm import llm_router, TaskPrompts
from ..models import ScheduledTask
from .base import BaseTask

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class LeadOutreachTask(BaseTask):
    """
    Lead outreach and email warmup task.

    Handles:
    - Checking email warmup status
    - Lead list prioritization
    - Outreach email generation
    """

    @property
    def task_type(self) -> str:
        return "lead_outreach"

    @property
    def description(self) -> str:
        return "Manage lead outreach and email warmup"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute the lead outreach task."""
        # Determine if this is warmup check or full outreach
        if task.task_type == "warmup_check":
            return await self._check_warmup()

        client_id = task.client
        if not client_id:
            return await self._check_warmup()

        return await self._run_outreach(task, client_id)

    async def _check_warmup(self) -> Dict[str, Any]:
        """Check email warmup status across all accounts."""
        try:
            from scripts.cold_email.warmup_manager import WarmupManager
            manager = WarmupManager()
            status = manager.get_status()

            accounts = status.get("accounts", [])
            warming = sum(1 for a in accounts if a.get("status") == "warming")
            ready = sum(1 for a in accounts if a.get("status") == "ready")

            summary_lines = [
                f"Email Warmup Status:",
                f"  Warming: {warming}",
                f"  Ready to send: {ready}",
            ]

            # Alert if any accounts need attention
            problem_accounts = [
                a for a in accounts
                if a.get("status") in ("paused", "error")
            ]
            if problem_accounts:
                summary_lines.append(f"  ⚠️ Issues: {len(problem_accounts)} accounts need attention")

            return {
                "success": True,
                "summary": "\n".join(summary_lines),
                "data": status
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _run_outreach(
        self,
        task: ScheduledTask,
        client_id: str
    ) -> Dict[str, Any]:
        """Run lead outreach for a client."""
        from gateway.config import config
        client = config.get_client(client_id)

        if not client:
            return {"success": False, "error": f"Unknown client: {client_id}"}

        # Load leads
        leads = self._load_leads(client_id)
        if not leads:
            return {
                "success": True,
                "summary": f"No leads available for {client_id}",
                "data": {"leads": []}
            }

        # Prioritize leads
        prioritized = await self._prioritize_leads(client, leads)

        # Generate outreach emails for top leads
        emails = await self._generate_emails(client, prioritized[:5])

        return {
            "success": True,
            "summary": f"Prepared {len(emails)} outreach emails for {client_id}",
            "data": {
                "prioritized_leads": prioritized[:10],
                "generated_emails": emails
            }
        }

    def _load_leads(self, client_id: str) -> List[Dict]:
        """Load leads from client's leads directory."""
        import csv

        client_dir = Path(__file__).parent.parent.parent / "clients" / client_id
        leads_dir = client_dir / "leads"

        if not leads_dir.exists():
            return []

        leads = []
        for csv_file in leads_dir.glob("*.csv"):
            try:
                with open(csv_file, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        leads.append(dict(row))
            except Exception:
                pass

        return leads

    async def _prioritize_leads(
        self,
        client: Dict,
        leads: List[Dict]
    ) -> List[Dict]:
        """Prioritize leads using LLM analysis."""
        if len(leads) <= 5:
            return leads

        # Get value proposition
        value_prop = client.get("value_proposition", "")
        persona = client.get("target_persona", "")

        # Use LLM to prioritize
        system, template = TaskPrompts.get_prompt("lead_outreach")
        lead_summary = "\n".join([
            f"- {l.get('name', 'Unknown')}, {l.get('title', 'N/A')} at {l.get('company', 'N/A')}"
            for l in leads[:50]
        ])

        prompt = f"""Prioritize these leads for outreach.

Target Persona: {persona}
Value Proposition: {value_prop}

Leads:
{lead_summary}

Return the top 10 leads as a numbered list with brief reasoning."""

        try:
            response = await llm_router.complete(
                prompt=prompt,
                task_type=self.task_type,
                max_tokens=1024
            )

            # For now, just return the original list
            # In production, parse LLM response to reorder
            return leads[:10]
        except Exception:
            return leads[:10]

    async def _generate_emails(
        self,
        client: Dict,
        leads: List[Dict]
    ) -> List[Dict]:
        """Generate personalized outreach emails."""
        emails = []

        for lead in leads:
            email = await self._generate_single_email(client, lead)
            if email:
                emails.append(email)

        return emails

    async def _generate_single_email(
        self,
        client: Dict,
        lead: Dict
    ) -> Optional[Dict]:
        """Generate a single personalized email."""
        name = lead.get("name", "")
        company = lead.get("company", "")
        title = lead.get("title", "")

        value_prop = client.get("value_proposition", "Our solution helps businesses grow.")

        prompt = f"""Write a cold outreach email:

Recipient: {name}, {title} at {company}
Value Proposition: {value_prop}

Requirements:
- Subject line (compelling, not salesy)
- Short intro (1-2 sentences, personalized)
- Value proposition (2-3 sentences)
- Soft CTA (question or offer)
- Under 100 words total

Format as:
SUBJECT: [subject line]
---
[email body]"""

        try:
            response = await llm_router.complete(
                prompt=prompt,
                task_type=self.task_type,
                max_tokens=512
            )

            # Parse response
            if "SUBJECT:" in response:
                parts = response.split("---", 1)
                subject = parts[0].replace("SUBJECT:", "").strip()
                body = parts[1].strip() if len(parts) > 1 else ""
            else:
                subject = "Quick question"
                body = response

            return {
                "lead": lead,
                "subject": subject,
                "body": body,
                "status": "draft"
            }
        except Exception as e:
            return {"lead": lead, "error": str(e)}
