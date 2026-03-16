"""
Supabase Analytics Module
Database queries and business intelligence
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import Counter
from .config import config

# Kai Calls business ID - filter all Kai Calls specific queries
KAI_CALLS_BUSINESS_ID = "15e7eca8-9e34-4ec7-9a3c-24a2dd69df79"


class SupabaseAnalytics:
    """Supabase database analytics client"""

    def __init__(self, url: str = None, key: str = None):
        self.url = url or config.supabase_url
        self.key = key or config.supabase_key
        self._client = None

    def _get_client(self):
        """Lazy load the Supabase client"""
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.url, self.key)
            except ImportError:
                raise ImportError("Install: pip install supabase")
        return self._client

    # ============ CORE DATA RETRIEVAL ============

    def get_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get users"""
        client = self._get_client()
        response = client.table("users").select("*").range(offset, offset + limit - 1).order("created_at", desc=True).execute()
        return response.data

    def get_businesses(self) -> List[Dict]:
        """Get all businesses"""
        client = self._get_client()
        response = client.table("businesses").select("*").execute()
        return response.data

    def get_leads(self, limit: int = 100, status: str = None, business_id: str = None,
                  date_from: str = None, date_to: str = None) -> List[Dict]:
        """Get leads with optional filters"""
        client = self._get_client()
        query = client.table("leads").select("*, businesses(name)").order("created_at", desc=True).limit(limit)

        if status:
            query = query.eq("status", status)
        if business_id:
            query = query.eq("business_id", business_id)
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)

        response = query.execute()
        return response.data

    def get_agents(self, active_only: bool = False) -> List[Dict]:
        """Get agents"""
        client = self._get_client()
        query = client.table("agents").select("*")
        if active_only:
            query = query.eq("is_active", True)
        response = query.execute()
        return response.data

    def get_calls(self, limit: int = 100, agent_id: str = None, status: str = None,
                  date_from: str = None, date_to: str = None) -> List[Dict]:
        """Get calls with optional filters"""
        client = self._get_client()
        query = client.table("calls").select("*").order("created_at", desc=True).limit(limit)

        if agent_id:
            query = query.eq("agent_id", agent_id)
        if status:
            query = query.eq("status", status)
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)

        response = query.execute()
        return response.data

    def get_call_logs(self, limit: int = 100, call_id: str = None) -> List[Dict]:
        """Get call logs"""
        client = self._get_client()
        query = client.table("call_logs").select("*").order("created_at", desc=True).limit(limit)

        if call_id:
            query = query.eq("call_id", call_id)

        response = query.execute()
        return response.data

    def get_proposals(self, limit: int = 100, status: str = None) -> List[Dict]:
        """Get proposals"""
        client = self._get_client()
        query = client.table("proposals").select("*, leads(name, email), businesses(name)").order("created_at", desc=True).limit(limit)

        if status:
            query = query.eq("status", status)

        response = query.execute()
        return response.data

    # ============ AGGREGATE STATISTICS ============

    def get_table_counts(self) -> Dict[str, int]:
        """Get counts for all main tables"""
        client = self._get_client()
        tables = ["users", "businesses", "leads", "agents", "calls", "call_logs", "proposals"]
        counts = {}

        for table in tables:
            try:
                response = client.table(table).select("id", count="exact").execute()
                counts[table] = response.count if response.count is not None else len(response.data)
            except Exception:
                counts[table] = "N/A"

        return counts

    def get_leads_by_status(self) -> Dict[str, int]:
        """Get lead counts by status"""
        client = self._get_client()
        response = client.table("leads").select("status").execute()
        return dict(Counter(lead.get("status", "unknown") for lead in response.data))

    def get_leads_by_source(self) -> Dict[str, int]:
        """Get lead counts by source"""
        client = self._get_client()
        response = client.table("leads").select("source").execute()
        return dict(Counter(lead.get("source", "unknown") for lead in response.data))

    def get_calls_by_status(self) -> Dict[str, int]:
        """Get call counts by status"""
        client = self._get_client()
        response = client.table("calls").select("status").execute()
        return dict(Counter(call.get("status", "unknown") for call in response.data))

    # ============ TRENDS ============

    def get_daily_lead_trend(self, days: int = 30) -> List[Dict]:
        """Get daily lead counts"""
        client = self._get_client()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        response = client.table("leads").select("created_at").gte("created_at", start_date).execute()

        daily_counts = Counter()
        for lead in response.data:
            if lead.get("created_at"):
                date = lead["created_at"].split("T")[0]
                daily_counts[date] += 1

        return sorted([
            {"date": date, "leads": count}
            for date, count in daily_counts.items()
        ], key=lambda x: x["date"])

    def get_daily_call_trend(self, days: int = 30) -> List[Dict]:
        """Get daily call counts"""
        client = self._get_client()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        response = client.table("calls").select("created_at").gte("created_at", start_date).execute()

        daily_counts = Counter()
        for call in response.data:
            if call.get("created_at"):
                date = call["created_at"].split("T")[0]
                daily_counts[date] += 1

        return sorted([
            {"date": date, "calls": count}
            for date, count in daily_counts.items()
        ], key=lambda x: x["date"])

    # ============ CONVERSION FUNNEL ============

    def get_conversion_funnel(self) -> Dict:
        """Get conversion funnel metrics"""
        client = self._get_client()

        leads_resp = client.table("leads").select("id", count="exact").execute()
        calls_resp = client.table("calls").select("id", count="exact").execute()
        proposals_resp = client.table("proposals").select("id", count="exact").execute()

        lead_count = leads_resp.count if leads_resp.count is not None else len(leads_resp.data)
        call_count = calls_resp.count if calls_resp.count is not None else len(calls_resp.data)
        proposal_count = proposals_resp.count if proposals_resp.count is not None else len(proposals_resp.data)

        def calc_rate(current, previous):
            if previous == 0:
                return "0%"
            return f"{(current / previous) * 100:.1f}%"

        stages = [
            {"stage": "Leads", "count": lead_count, "rate": "100%"},
            {"stage": "Calls", "count": call_count, "rate": calc_rate(call_count, lead_count)},
            {"stage": "Proposals", "count": proposal_count, "rate": calc_rate(proposal_count, call_count)},
        ]

        overall = f"{(proposal_count / lead_count) * 100:.2f}%" if lead_count > 0 else "0%"

        return {
            "stages": stages,
            "overall_conversion": overall
        }

    # ============ CUSTOM QUERIES ============

    def query(self, table: str, select: str = "*", filters: Dict = None,
              order_by: str = None, ascending: bool = False, limit: int = 50) -> List[Dict]:
        """Execute a custom query"""
        client = self._get_client()
        query = client.table(table).select(select)

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        if order_by:
            query = query.order(order_by, desc=not ascending)

        query = query.limit(limit)
        response = query.execute()
        return response.data

    # ============ AGENT PERFORMANCE ============

    def get_agent_performance(self) -> List[Dict]:
        """Get agent performance metrics"""
        client = self._get_client()

        agents = client.table("agents").select("*").execute().data
        calls = client.table("calls").select("agent_id, status, duration").execute().data

        agent_stats = {}
        for agent in agents:
            agent_stats[agent["id"]] = {
                "name": agent.get("name", "Unknown"),
                "type": agent.get("type", "Unknown"),
                "is_active": agent.get("is_active", False),
                "total_calls": 0,
                "completed_calls": 0,
                "total_duration": 0,
            }

        for call in calls:
            agent_id = call.get("agent_id")
            if agent_id in agent_stats:
                agent_stats[agent_id]["total_calls"] += 1
                if call.get("status") == "completed":
                    agent_stats[agent_id]["completed_calls"] += 1
                if call.get("duration"):
                    agent_stats[agent_id]["total_duration"] += call["duration"]

        return [
            {
                **stats,
                "avg_duration": f"{stats['total_duration'] / stats['total_calls']:.0f}s" if stats['total_calls'] > 0 else "0s",
                "completion_rate": f"{(stats['completed_calls'] / stats['total_calls']) * 100:.1f}%" if stats['total_calls'] > 0 else "0%",
            }
            for stats in agent_stats.values()
        ]

    # ============ KAI CALLS - TRANSCRIPTS ============

    def get_transcripts(self, limit: int = 50, call_id: str = None,
                        date_from: str = None, date_to: str = None,
                        kai_calls_only: bool = True) -> List[Dict]:
        """Get call transcripts with optional filters (defaults to Kai Calls business only)"""
        client = self._get_client()

        try:
            # Get transcripts from leads table (where call transcripts are stored)
            query = client.table("leads").select(
                "id, notes, created_at, source, agent_id, agent_name, phone, name, email, message"
            ).order("created_at", desc=True).limit(limit)

            # Filter to Kai Calls business
            if kai_calls_only:
                query = query.eq("business_id", KAI_CALLS_BUSINESS_ID)

            # Filter phone call sources (transcripts come from calls)
            query = query.ilike("source", "%phone%")

            if call_id:
                query = query.ilike("notes", f"%{call_id}%")
            if date_from:
                query = query.gte("created_at", date_from)
            if date_to:
                query = query.lte("created_at", date_to)

            response = query.execute()

            # Parse transcripts from notes field
            results = []
            for lead in response.data:
                notes = lead.get("notes", "")
                transcript = ""
                call_id_extracted = ""

                if "Transcript:" in notes:
                    transcript = notes.split("Transcript:")[-1].strip()
                if "Call ID:" in notes:
                    call_id_extracted = notes.split("Call ID:")[1].split("\n")[0].strip()

                results.append({
                    "lead_id": lead.get("id"),
                    "call_id": call_id_extracted,
                    "transcript": transcript,
                    "agent_name": lead.get("agent_name"),
                    "agent_id": lead.get("agent_id"),
                    "phone": lead.get("phone"),
                    "caller_name": lead.get("name"),
                    "source": lead.get("source"),
                    "created_at": lead.get("created_at"),
                })

            return results
        except Exception as e:
            return [{"error": str(e)}]

    def get_transcript_by_call_id(self, call_id: str) -> Dict:
        """Get full transcript for a specific call from Kai Calls"""
        client = self._get_client()

        try:
            # Search for call ID in leads notes field
            response = client.table("leads").select(
                "id, notes, created_at, source, agent_id, agent_name, phone, name, email"
            ).eq("business_id", KAI_CALLS_BUSINESS_ID).ilike("notes", f"%{call_id}%").execute()

            if response.data:
                lead = response.data[0]
                notes = lead.get("notes", "")
                transcript = notes.split("Transcript:")[-1].strip() if "Transcript:" in notes else ""

                return {
                    "call_id": call_id,
                    "lead_id": lead.get("id"),
                    "transcript": transcript,
                    "agent_name": lead.get("agent_name"),
                    "agent_id": lead.get("agent_id"),
                    "phone": lead.get("phone"),
                    "caller_name": lead.get("name"),
                    "caller_email": lead.get("email"),
                    "source": lead.get("source"),
                    "created_at": lead.get("created_at"),
                    "full_notes": notes,
                }
            return {}
        except Exception as e:
            return {"error": str(e)}

    def get_recent_transcripts_with_summary(self, limit: int = 20) -> List[Dict]:
        """Get recent Kai Calls transcripts with parsed details"""
        client = self._get_client()

        try:
            response = client.table("leads").select(
                "id, notes, created_at, source, agent_id, agent_name, phone, name, email"
            ).eq("business_id", KAI_CALLS_BUSINESS_ID).ilike("source", "%phone%").order("created_at", desc=True).limit(limit).execute()

            results = []
            for lead in response.data:
                notes = lead.get("notes", "")
                transcript = notes.split("Transcript:")[-1].strip() if "Transcript:" in notes else ""
                call_id = notes.split("Call ID:")[1].split("\n")[0].strip() if "Call ID:" in notes else ""

                results.append({
                    "call_id": call_id,
                    "lead_id": lead.get("id"),
                    "agent": lead.get("agent_name", "Unknown"),
                    "phone": lead.get("phone", "N/A"),
                    "caller_name": lead.get("name"),
                    "created_at": lead.get("created_at"),
                    "transcript_preview": transcript[:500] + "..." if len(transcript) > 500 else transcript,
                    "transcript_length": len(transcript),
                    "word_count": len(transcript.split()) if transcript else 0,
                    "has_transcript": len(transcript) > 10,
                })
            return results
        except Exception as e:
            return [{"error": str(e)}]

    def analyze_transcripts(self, days: int = 30) -> Dict:
        """Analyze Kai Calls transcript patterns and metrics"""
        client = self._get_client()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            response = client.table("leads").select(
                "notes, created_at, agent_name"
            ).eq("business_id", KAI_CALLS_BUSINESS_ID).ilike("source", "%phone%").gte("created_at", start_date).execute()

            leads = response.data

            # Parse transcripts and calculate metrics
            total_calls = len(leads)
            transcripts = []
            agents_used = Counter()

            for lead in leads:
                notes = lead.get("notes", "")
                if "Transcript:" in notes:
                    transcript = notes.split("Transcript:")[-1].strip()
                    if transcript:
                        transcripts.append(transcript)
                agent = lead.get("agent_name", "Unknown")
                agents_used[agent] += 1

            calls_with_transcript = len(transcripts)
            total_words = sum(len(t.split()) for t in transcripts)

            return {
                "period_days": days,
                "total_calls": total_calls,
                "calls_with_transcript": calls_with_transcript,
                "transcript_rate": f"{(calls_with_transcript / max(total_calls, 1)) * 100:.1f}%",
                "total_words_spoken": total_words,
                "avg_words_per_call": total_words // max(calls_with_transcript, 1),
                "agents_used": dict(agents_used),
                "top_agent": max(agents_used.items(), key=lambda x: x[1])[0] if agents_used else "N/A",
            }
        except Exception as e:
            return {"error": str(e)}

    # ============ KAI CALLS - PROMPTS & AGENTS ============

    def get_agent_prompts(self, agent_id: str = None) -> List[Dict]:
        """Get agent prompts/configurations"""
        client = self._get_client()

        try:
            query = client.table("agents").select("id, name, type, prompt, system_prompt, greeting, is_active, created_at, updated_at")

            if agent_id:
                query = query.eq("id", agent_id)

            response = query.execute()
            return response.data
        except Exception as e:
            return [{"error": str(e)}]

    def get_agent_configurations(self) -> List[Dict]:
        """Get full agent configurations with performance stats"""
        client = self._get_client()

        try:
            agents = client.table("agents").select("*").execute().data
            calls = client.table("calls").select("agent_id, status, duration").execute().data

            # Build stats per agent
            agent_call_stats = {}
            for call in calls:
                aid = call.get("agent_id")
                if aid not in agent_call_stats:
                    agent_call_stats[aid] = {"total": 0, "completed": 0, "duration": 0}
                agent_call_stats[aid]["total"] += 1
                if call.get("status") == "completed":
                    agent_call_stats[aid]["completed"] += 1
                agent_call_stats[aid]["duration"] += call.get("duration", 0)

            results = []
            for agent in agents:
                aid = agent.get("id")
                stats = agent_call_stats.get(aid, {"total": 0, "completed": 0, "duration": 0})

                prompt = agent.get("prompt", "") or agent.get("system_prompt", "")

                results.append({
                    "id": aid,
                    "name": agent.get("name"),
                    "type": agent.get("type"),
                    "is_active": agent.get("is_active"),
                    "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "prompt_length": len(prompt),
                    "greeting": agent.get("greeting", ""),
                    "total_calls": stats["total"],
                    "completed_calls": stats["completed"],
                    "completion_rate": f"{(stats['completed'] / max(stats['total'], 1)) * 100:.1f}%",
                    "total_duration_min": stats["duration"] // 60,
                    "created_at": agent.get("created_at"),
                })

            return results
        except Exception as e:
            return [{"error": str(e)}]

    def get_prompt_by_agent(self, agent_id: str) -> Dict:
        """Get full prompt for a specific agent"""
        client = self._get_client()

        try:
            response = client.table("agents").select("*").eq("id", agent_id).single().execute()
            if response.data:
                return {
                    "agent_id": response.data.get("id"),
                    "name": response.data.get("name"),
                    "type": response.data.get("type"),
                    "prompt": response.data.get("prompt") or response.data.get("system_prompt", ""),
                    "greeting": response.data.get("greeting", ""),
                    "voice": response.data.get("voice", ""),
                    "settings": response.data.get("settings", {}),
                }
            return {}
        except Exception as e:
            return {"error": str(e)}

    # ============ KAI CALLS - LEADS EXPORT ============

    def export_leads(self, business_id: str = None, status: str = None,
                     date_from: str = None, date_to: str = None,
                     format: str = "dict", kai_calls_only: bool = True) -> Any:
        """Export leads with full details for analysis (defaults to Kai Calls business)"""
        client = self._get_client()

        try:
            query = client.table("leads").select(
                "id, name, email, phone, status, source, created_at, notes, agent_name, agent_id"
            ).order("created_at", desc=True)

            # Default to Kai Calls business ID
            if kai_calls_only and not business_id:
                query = query.eq("business_id", KAI_CALLS_BUSINESS_ID)
            elif business_id:
                query = query.eq("business_id", business_id)

            if status:
                query = query.eq("status", status)
            if date_from:
                query = query.gte("created_at", date_from)
            if date_to:
                query = query.lte("created_at", date_to)

            response = query.execute()
            leads = response.data

            if format == "csv":
                if not leads:
                    return "No leads found"

                headers = ["id", "name", "email", "phone", "status", "source", "agent", "created_at", "has_transcript"]
                rows = [",".join(headers)]

                for lead in leads:
                    notes = lead.get("notes", "")
                    has_transcript = "Yes" if "Transcript:" in notes and len(notes.split("Transcript:")[-1].strip()) > 10 else "No"

                    row = [
                        str(lead.get("id", "")),
                        str(lead.get("name", "")).replace(",", ";"),
                        str(lead.get("email", "")),
                        str(lead.get("phone", "")),
                        str(lead.get("status") or "new"),
                        str(lead.get("source", "")).replace(",", ";"),
                        str(lead.get("agent_name", "")).replace(",", ";"),
                        str(lead.get("created_at", ""))[:19],
                        has_transcript,
                    ]
                    rows.append(",".join(row))

                return "\n".join(rows)

            return leads
        except Exception as e:
            return [{"error": str(e)}]

    def get_leads_summary(self, days: int = 30, kai_calls_only: bool = True) -> Dict:
        """Get leads summary with conversion metrics (defaults to Kai Calls business)"""
        client = self._get_client()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            query = client.table("leads").select(
                "status, source, created_at, agent_name"
            ).gte("created_at", start_date)

            if kai_calls_only:
                query = query.eq("business_id", KAI_CALLS_BUSINESS_ID)

            response = query.execute()
            leads = response.data

            by_status = Counter(l.get("status") or "new" for l in leads)
            by_source = Counter(l.get("source", "unknown") for l in leads)
            by_agent = Counter(l.get("agent_name") or "Unknown" for l in leads)

            # Daily trend
            daily = Counter()
            for lead in leads:
                if lead.get("created_at"):
                    date = lead["created_at"].split("T")[0]
                    daily[date] += 1

            return {
                "period_days": days,
                "total_leads": len(leads),
                "leads_per_day": round(len(leads) / max(days, 1), 1),
                "by_status": dict(by_status),
                "by_source": dict(by_source),
                "by_agent": dict(by_agent),
                "daily_trend": sorted([{"date": d, "count": c} for d, c in daily.items()], key=lambda x: x["date"]),
                "top_source": max(by_source.items(), key=lambda x: x[1])[0] if by_source else "N/A",
                "top_agent": max(by_agent.items(), key=lambda x: x[1])[0] if by_agent else "N/A",
            }
        except Exception as e:
            return {"error": str(e)}

    def get_hot_leads(self, limit: int = 20, kai_calls_only: bool = True) -> List[Dict]:
        """Get recent leads for follow-up (defaults to Kai Calls business)"""
        client = self._get_client()

        try:
            query = client.table("leads").select(
                "id, name, email, phone, status, source, created_at, notes, agent_name"
            ).order("created_at", desc=True).limit(limit)

            if kai_calls_only:
                query = query.eq("business_id", KAI_CALLS_BUSINESS_ID)

            response = query.execute()

            results = []
            for l in response.data:
                notes = l.get("notes", "")
                # Extract transcript preview if available
                transcript_preview = ""
                if "Transcript:" in notes:
                    transcript = notes.split("Transcript:")[-1].strip()
                    transcript_preview = transcript[:200] + "..." if len(transcript) > 200 else transcript

                results.append({
                    "id": l.get("id"),
                    "name": l.get("name"),
                    "email": l.get("email"),
                    "phone": l.get("phone"),
                    "status": l.get("status") or "new",
                    "source": l.get("source"),
                    "agent": l.get("agent_name"),
                    "created_at": l.get("created_at"),
                    "transcript_preview": transcript_preview,
                    "has_transcript": len(transcript_preview) > 10,
                })

            return results
        except Exception as e:
            return [{"error": str(e)}]

    # ============ KAI CALLS - BUSINESS INTELLIGENCE ============

    def get_kai_calls_dashboard(self, days: int = 30) -> Dict:
        """Complete Kai Calls business intelligence dashboard (filtered to Kai Calls business)"""
        client = self._get_client()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            # Get all Kai Calls leads
            response = client.table("leads").select(
                "id, name, email, phone, status, source, created_at, notes, agent_name, agent_id"
            ).eq("business_id", KAI_CALLS_BUSINESS_ID).gte("created_at", start_date).execute()

            leads = response.data

            # Split into phone calls vs other
            phone_leads = [l for l in leads if l.get("source", "").startswith("phone")]
            other_leads = [l for l in leads if not l.get("source", "").startswith("phone")]

            # Parse transcripts
            transcripts_count = 0
            total_words = 0
            for lead in phone_leads:
                notes = lead.get("notes", "")
                if "Transcript:" in notes:
                    transcript = notes.split("Transcript:")[-1].strip()
                    if transcript:
                        transcripts_count += 1
                        total_words += len(transcript.split())

            # By agent
            by_agent = Counter(l.get("agent_name") or "Unknown" for l in phone_leads)

            # Daily trend
            daily = Counter()
            for lead in phone_leads:
                if lead.get("created_at"):
                    date = lead["created_at"].split("T")[0]
                    daily[date] += 1

            return {
                "period_days": days,
                "total_leads": len(leads),
                "phone_calls": len(phone_leads),
                "other_leads": len(other_leads),
                "with_transcript": transcripts_count,
                "transcript_rate": f"{(transcripts_count / max(len(phone_leads), 1)) * 100:.1f}%",
                "total_words_spoken": total_words,
                "avg_words_per_call": total_words // max(transcripts_count, 1),
                "by_agent": dict(by_agent),
                "top_agent": max(by_agent.items(), key=lambda x: x[1])[0] if by_agent else "N/A",
                "daily_trend": sorted([{"date": d, "calls": c} for d, c in daily.items()], key=lambda x: x["date"]),
                "recent_calls": self.get_hot_leads(10),
            }
        except Exception as e:
            return {"error": str(e)}

    def get_business_performance(self, business_id: str = None) -> List[Dict]:
        """Get performance metrics per business"""
        client = self._get_client()

        try:
            businesses = client.table("businesses").select("*").execute().data
            leads = client.table("leads").select("business_id, status").execute().data
            calls = client.table("calls").select("business_id, status, duration").execute().data

            # Aggregate by business
            biz_stats = {}
            for biz in businesses:
                bid = biz.get("id")
                biz_stats[bid] = {
                    "id": bid,
                    "name": biz.get("name"),
                    "email": biz.get("email"),
                    "total_leads": 0,
                    "qualified_leads": 0,
                    "total_calls": 0,
                    "completed_calls": 0,
                    "total_duration": 0,
                }

            for lead in leads:
                bid = lead.get("business_id")
                if bid in biz_stats:
                    biz_stats[bid]["total_leads"] += 1
                    if lead.get("status") in ["qualified", "hot", "converted"]:
                        biz_stats[bid]["qualified_leads"] += 1

            for call in calls:
                bid = call.get("business_id")
                if bid in biz_stats:
                    biz_stats[bid]["total_calls"] += 1
                    if call.get("status") == "completed":
                        biz_stats[bid]["completed_calls"] += 1
                    biz_stats[bid]["total_duration"] += call.get("duration", 0)

            results = []
            for stats in biz_stats.values():
                stats["lead_to_call_rate"] = f"{(stats['total_calls'] / max(stats['total_leads'], 1)) * 100:.1f}%"
                stats["call_completion_rate"] = f"{(stats['completed_calls'] / max(stats['total_calls'], 1)) * 100:.1f}%"
                stats["avg_call_duration"] = f"{stats['total_duration'] // max(stats['total_calls'], 1)}s"
                results.append(stats)

            if business_id:
                return [r for r in results if r["id"] == business_id]

            return sorted(results, key=lambda x: x["total_leads"], reverse=True)
        except Exception as e:
            return [{"error": str(e)}]

    def get_call_outcomes_analysis(self, days: int = 30) -> Dict:
        """Analyze Kai Calls phone call patterns (filtered to Kai Calls business)"""
        client = self._get_client()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            response = client.table("leads").select(
                "status, created_at, agent_name, agent_id, notes, source"
            ).eq("business_id", KAI_CALLS_BUSINESS_ID).ilike("source", "%phone%").gte("created_at", start_date).execute()

            calls = response.data

            # By agent
            by_agent = Counter(c.get("agent_name") or "Unknown" for c in calls)

            # Transcript analysis
            with_transcript = 0
            word_counts = []
            for call in calls:
                notes = call.get("notes", "")
                if "Transcript:" in notes:
                    transcript = notes.split("Transcript:")[-1].strip()
                    if transcript:
                        with_transcript += 1
                        word_counts.append(len(transcript.split()))

            # Time of day analysis
            hours = Counter()
            for call in calls:
                if call.get("created_at"):
                    try:
                        hour = int(call["created_at"].split("T")[1][:2])
                        hours[hour] += 1
                    except:
                        pass

            return {
                "period_days": days,
                "total_calls": len(calls),
                "with_transcript": with_transcript,
                "transcript_rate": f"{(with_transcript / max(len(calls), 1)) * 100:.1f}%",
                "word_stats": {
                    "total_words": sum(word_counts),
                    "avg_words": sum(word_counts) // max(len(word_counts), 1),
                    "min_words": min(word_counts) if word_counts else 0,
                    "max_words": max(word_counts) if word_counts else 0,
                },
                "calls_by_agent": dict(by_agent),
                "calls_by_hour": dict(sorted(hours.items())),
                "peak_hour": max(hours.items(), key=lambda x: x[1])[0] if hours else "N/A",
            }
        except Exception as e:
            return {"error": str(e)}

    # ============ KAI CALLS - WEEKLY REPORT ============

    def get_kai_calls_weekly_report(self) -> Dict:
        """Generate weekly report for Kai Calls (filtered to Kai Calls business)"""
        return {
            "generated_at": datetime.now().isoformat(),
            "business_id": KAI_CALLS_BUSINESS_ID,
            "this_week": {
                "leads": self.get_leads_summary(7),
                "calls": self.get_call_outcomes_analysis(7),
                "transcripts": self.analyze_transcripts(7),
            },
            "last_14_days": {
                "leads": self.get_leads_summary(14),
                "calls": self.get_call_outcomes_analysis(14),
            },
            "recent_calls": self.get_hot_leads(10),
            "dashboard": self.get_kai_calls_dashboard(7),
        }
