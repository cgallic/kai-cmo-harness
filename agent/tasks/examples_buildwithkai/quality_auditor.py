"""
Quality Auditor — LLM spot-checks completed products for issues.

Schedule: Every 12 hours (0 */12 * * *)

Checks 3-5 recently completed products for:
- Broken HTML / malformed output
- Placeholder text ("Lorem ipsum", "[Your Name]", etc.)
- Empty sections
- Truncated content
"""

import json
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from ...llm import llm_router
from .client import bwk_client


QUALITY_AUDIT_PROMPT = """You are a QA auditor for an AI product generation platform.
A user created a digital product (e-book, course, template, etc.) using our AI.
Review this product data and check for quality issues.

PRODUCT DATA:
{product_data}

Check for these issues:
1. PLACEHOLDER TEXT: "Lorem ipsum", "[Your Name]", "[Insert X]", "TODO", "FIXME", generic filler
2. BROKEN HTML: Unclosed tags, malformed elements, raw HTML visible where it shouldn't be
3. EMPTY SECTIONS: Sections with no meaningful content, just headers
4. TRUNCATED CONTENT: Abruptly cut-off text, incomplete sentences at the end
5. REPETITIVE CONTENT: Same paragraph or section repeated multiple times
6. QUALITY: Overall impression — would a customer be satisfied?

Return JSON:
{{
  "score": 1-10,
  "issues": [
    {{"type": "placeholder|broken_html|empty_section|truncated|repetitive|other", "description": "what's wrong", "severity": "critical|warning|minor"}}
  ],
  "summary": "1-2 sentence overall assessment",
  "publishable": true/false
}}

Be strict but fair. Minor formatting issues are warnings, not critical."""


class QualityAuditorTask(BaseTask):
    """LLM-powered quality auditor for BWK products."""

    @property
    def task_type(self) -> str:
        return "bwk_quality_auditor"

    @property
    def description(self) -> str:
        return "BWK: LLM spot-check completed products for quality issues"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            # Get recent completed products (skip ones we already audited)
            audited_ids = set(state_manager.get("bwk_audited_products") or [])
            products = await bwk_client.get_completed_products_for_audit(limit=10)

            # Filter to unaudited
            to_audit = [p for p in products if p["id"] not in audited_ids][:5]

            if not to_audit:
                return {
                    "success": True,
                    "summary": "Quality audit: no new products to check",
                    "data": {"audited": 0},
                }

            results = []
            critical_issues = []

            for product in to_audit:
                audit = await self._audit_product(product)
                if audit:
                    results.append(audit)
                    # Track audited
                    audited_ids.add(product["id"])

                    # Collect critical issues
                    for issue in audit.get("issues", []):
                        if issue.get("severity") == "critical":
                            critical_issues.append({
                                "product_id": product["id"][:8],
                                "issue": issue["description"],
                            })

            # Keep last 200 audited IDs
            state_manager.set("bwk_audited_products", list(audited_ids)[-200:])

            # Alert on critical issues
            if critical_issues:
                lines = ["*BWK Quality Alert*\n"]
                for ci in critical_issues[:5]:
                    lines.append(f"- Product {ci['product_id']}: {ci['issue']}")
                await self.send_notification("\n".join(lines))

            # Store audit summary
            avg_score = sum(r.get("score", 0) for r in results) / max(len(results), 1)
            state_manager.set_task_context("bwk_quality_audit", {
                "audited": len(results),
                "avg_score": round(avg_score, 1),
                "critical_count": len(critical_issues),
                "publishable_count": sum(1 for r in results if r.get("publishable")),
            })

            return {
                "success": True,
                "summary": f"Audited {len(results)} products, avg score {avg_score:.1f}/10, {len(critical_issues)} critical",
                "data": {"results": results, "critical": critical_issues},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _audit_product(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run LLM quality audit on a single product."""
        # Prepare product data for review (limit size)
        product_str = json.dumps({
            k: v for k, v in product.items()
            if k not in ("id", "user_id") and v is not None
        }, indent=2, default=str)[:6000]

        prompt = QUALITY_AUDIT_PROMPT.format(product_data=product_str)

        try:
            response = await llm_router.complete(
                prompt=prompt,
                task_type="bwk_quality_auditor",
                max_tokens=1000,
                temperature=0.2,
            )
            return self._parse_json(response)
        except Exception as e:
            print(f"[QualityAuditor] LLM error for product {product['id'][:8]}: {e}")
            return None

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
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        return None
