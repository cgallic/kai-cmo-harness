"""
Shared command router for all communication channels.

All command parsing, routing, and handler logic lives here.
WhatsApp and Discord both delegate to this module.
"""

from ..config import agent_config
from ..state import state_manager


COMMANDS = {
    "status": "Show current agent status and pending tasks",
    "report": "Get full daily briefing (usage: report [client])",
    "mrr": "Show current MRR from Stripe",
    "analytics": "Get analytics summary (usage: analytics [client])",
    "email": "Cold email campaign stats",
    "generate": "Trigger content generation (usage: generate [client])",
    "leads": "Show lead pipeline status (usage: leads [client])",
    "approve": "Approve a pending action (usage: approve [task_id])",
    "pause": "Pause all scheduled tasks",
    "resume": "Resume scheduled tasks",
    "tasks": "List scheduled tasks",
    "help": "Show this help message",
    # Kai Calls commands
    "kaistatus": "Kai Calls system health + pending emails",
    "kaiqueue": "Show pending email queue",
    "kaisend": "Auto-send all approved pending emails",
    "kaicalls": "Full Kai Calls daily report on demand",
    "kaileads": "Show recent leads with scores and next actions",
    # BuildWithKai commands
    "bwkstatus": "BWK system health + generation stats",
    "bwkgens": "BWK product generation stats",
    "bwkusers": "BWK user activation funnel",
    "bwkrevenue": "BWK revenue and published products",
    "bwkreport": "Full BWK daily report on demand",
    # Amazing Backyard Parties commands
    "abpstatus": "ABP system health + lead/vendor stats",
    "abpleads": "ABP recent leads and match rates",
    "abpvendors": "ABP vendor coverage and pipeline",
    "abpreport": "Full ABP daily report on demand",
}


async def route(command: str, args: str, sender: str) -> str:
    """
    Route a command string to its handler and return the response.

    Args:
        command: The command name (e.g. "status", "kaileads")
        args: Any arguments after the command
        sender: User identifier (phone number, Discord user, etc.)

    Returns:
        Formatted response string
    """
    handlers = {
        "status": _handle_status,
        "report": _handle_report,
        "mrr": _handle_mrr,
        "analytics": _handle_analytics,
        "email": _handle_email,
        "generate": _handle_generate,
        "leads": _handle_leads,
        "approve": _handle_approve,
        "pause": _handle_pause,
        "resume": _handle_resume,
        "tasks": _handle_tasks,
        "help": _handle_help,
        # Kai Calls
        "kaistatus": _handle_kaistatus,
        "kaiqueue": _handle_kaiqueue,
        "kaisend": _handle_kaisend,
        "kaicalls": _handle_kaicalls,
        "kaileads": _handle_kaileads,
        # BuildWithKai
        "bwkstatus": _handle_bwkstatus,
        "bwkgens": _handle_bwkgens,
        "bwkusers": _handle_bwkusers,
        "bwkrevenue": _handle_bwkrevenue,
        "bwkreport": _handle_bwkreport,
        # Amazing Backyard Parties
        "abpstatus": _handle_abpstatus,
        "abpleads": _handle_abpleads,
        "abpvendors": _handle_abpvendors,
        "abpreport": _handle_abpreport,
    }

    handler = handlers.get(command)
    if handler:
        return await handler(args, sender)

    return f"Unknown command: {command}\n\nType 'help' to see available commands."


async def route_text(text: str, sender: str) -> str:
    """
    Parse raw text into command + args, then route.

    Handles special prefixes (todo:, done:, fix:, approve:).
    """
    text = text.strip().lower()
    parts = text.split(maxsplit=1)
    command = parts[0] if parts else ""
    args = parts[1] if len(parts) > 1 else ""

    # Special prefixes
    if text.startswith("todo:"):
        return await _handle_kai_todo(text[5:].strip(), sender)
    if text.startswith("fix:"):
        return await _handle_kai_todo(text[4:].strip(), sender, priority="P1")
    if text.startswith("done:"):
        return await _handle_kai_done(text[5:].strip(), sender)
    if text.startswith("approve:"):
        return await _handle_approve(text[8:].strip(), sender)

    return await route(command, args, sender)


# =============================================================================
# Core commands
# =============================================================================

async def _handle_help(args: str, sender: str) -> str:
    lines = ["*CMO Agent Commands*\n"]
    for cmd, desc in COMMANDS.items():
        lines.append(f"• *{cmd}*: {desc}")
    return "\n".join(lines)


async def _handle_status(args: str, sender: str) -> str:
    from ..scheduler import scheduler

    state = state_manager.get_agent_state()
    running = state_manager.get_running_tasks()
    stats = state.stats

    status = "⏸️ Paused" if state.paused else "✅ Running"
    lines = [
        f"*Agent Status*: {status}",
        "",
        f"*Running tasks*: {len(running)}",
    ]

    if running:
        for task_id in running:
            lines.append(f"  • {task_id}")

    lines.append("")
    lines.append("*Statistics*:")
    lines.append(f"  Completed: {stats.get('tasks_completed', 0)}")
    lines.append(f"  Failed: {stats.get('tasks_failed', 0)}")
    lines.append(f"  Retried: {stats.get('tasks_retried', 0)}")

    upcoming = scheduler.list_upcoming_tasks(limit=1)
    if upcoming:
        task, time_str = upcoming[0]
        lines.append("")
        lines.append(f"*Next task*: {task.name} ({time_str})")

    return "\n".join(lines)


async def _handle_mrr(args: str, sender: str) -> str:
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from scripts.analytics.stripe_analytics import StripeAnalytics
        stripe = StripeAnalytics()
        data = stripe.get_mrr()

        lines = [
            "*💰 Stripe MRR*\n",
            f"*MRR*: ${data.get('mrr', 0):,.2f}",
            f"*Active Subs*: {data.get('active_subscriptions', 0)}",
        ]

        at_risk = data.get("at_risk", {})
        if at_risk.get("count", 0) > 0:
            lines.append(f"*At-Risk*: ${at_risk.get('mrr', 0):,.2f} ({at_risk.get('count')} subs)")

        by_plan = data.get("by_plan", {})
        if by_plan:
            lines.append("\n*By Plan*:")
            for plan, info in list(by_plan.items())[:3]:
                plan_short = plan[:20] + "..." if len(plan) > 20 else plan
                lines.append(f"  • {plan_short}: {info.get('count')} @ ${info.get('mrr', 0):,.2f}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error fetching MRR: {str(e)}"


async def _handle_email(args: str, sender: str) -> str:
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from gateway.adapters.cold_email_adapter import ColdEmailAdapter
        adapter = ColdEmailAdapter()
        data = adapter.get_analytics_summary()

        if "error" in data:
            return f"Error: {data['error']}"

        accounts = data.get("accounts", {})
        totals = data.get("totals", {})
        rates = data.get("rates", {})
        health = data.get("health", {})

        lines = [
            "*📧 Cold Email Stats*\n",
            f"*Accounts*: {accounts.get('total', 0)} total, {accounts.get('ready_to_send', 0)} ready",
            f"*Warming*: {accounts.get('warming', 0)} accounts",
            "",
            f"*Sent*: {totals.get('sent', 0)}",
            f"*Opened*: {totals.get('opened', 0)} ({rates.get('open_rate', 0)}%)",
            f"*Replied*: {totals.get('replied', 0)} ({rates.get('reply_rate', 0)}%)",
            f"*Bounced*: {totals.get('bounced', 0)} ({rates.get('bounce_rate', 0)}%)",
            "",
            f"*Deliverability*: {health.get('deliverability', 0)}%",
        ]

        return "\n".join(lines)

    except Exception as e:
        return f"Error fetching email stats: {str(e)}"


async def _handle_report(args: str, sender: str) -> str:
    client = args.strip() if args else "kaicalls"

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        lines = [f"*📊 Daily Briefing: {client.title()}*\n"]

        try:
            from scripts.analytics.stripe_analytics import StripeAnalytics
            stripe = StripeAnalytics()
            mrr_data = stripe.get_mrr()
            lines.append(f"*💰 MRR*: ${mrr_data.get('mrr', 0):,.2f} ({mrr_data.get('active_subscriptions', 0)} subs)")
        except Exception:
            pass

        try:
            from scripts.analytics.google_analytics import GoogleAnalytics
            from scripts.analytics.sites_config import get_site
            site = get_site(client)
            if site:
                ga = GoogleAnalytics()
                overview = ga.get_overview(site.ga_property, days=7)
                if overview:
                    lines.append(f"*🌐 Traffic*: {overview.get('sessions', 0)} sessions, {overview.get('users', 0)} users (7d)")
        except Exception:
            pass

        try:
            from gateway.adapters.cold_email_adapter import ColdEmailAdapter
            adapter = ColdEmailAdapter()
            email_data = adapter.get_analytics_summary()
            totals = email_data.get("totals", {})
            rates = email_data.get("rates", {})
            if totals.get("sent", 0) > 0:
                lines.append(f"*📧 Outreach*: {totals.get('sent', 0)} sent, {rates.get('reply_rate', 0)}% reply rate")
        except Exception:
            pass

        lines.append("")
        lines.append("_Type 'mrr', 'analytics', or 'email' for details_")

        return "\n".join(lines)

    except Exception as e:
        return f"Error generating report: {str(e)}"


async def _handle_analytics(args: str, sender: str) -> str:
    client = args.strip() if args else None

    if not client:
        return "Usage: analytics [client]\n\nExample: analytics indexify"

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from scripts.analytics.google_analytics import GoogleAnalytics
        from scripts.analytics.sites_config import get_site

        site = get_site(client)
        if not site:
            return f"Unknown client: {client}"

        ga = GoogleAnalytics()
        overview = ga.get_overview(site.ga_property, days=7)

        if overview:
            return (
                f"*{client.title()} Analytics (7 days)*\n\n"
                f"Sessions: {overview.get('sessions', 'N/A')}\n"
                f"Users: {overview.get('users', 'N/A')}\n"
                f"Page Views: {overview.get('pageviews', 'N/A')}\n"
                f"Bounce Rate: {overview.get('bounce_rate', 'N/A')}%"
            )
        else:
            return f"Could not fetch analytics for {client}"

    except Exception as e:
        return f"Error fetching analytics: {str(e)}"


async def _handle_generate(args: str, sender: str) -> str:
    client = args.strip() if args else None

    if not client:
        return "Usage: generate [client]\n\nExample: generate indexify"

    state_manager.update_conversation_context(
        sender,
        current_command="generate",
        session_data={"client": client}
    )

    return (
        f"Content generation queued for {client}.\n\n"
        "I'll notify you when it's complete."
    )


async def _handle_leads(args: str, sender: str) -> str:
    client = args.strip() if args else None

    if not client:
        return "Usage: leads [client]\n\nExample: leads kaicalls"

    return f"Lead pipeline for {client}:\n\n(Lead data not yet implemented)"


async def _handle_approve(args: str, sender: str) -> str:
    task_id = args.strip() if args else None

    if not task_id:
        context = state_manager.get_conversation_context(sender)
        if context.pending_approval_id:
            task_id = context.pending_approval_id
        else:
            return "Usage: approve [task_id]"

    state_manager.update_conversation_context(
        sender,
        pending_approval_id=None
    )

    return f"✅ Task {task_id} approved."


async def _handle_pause(args: str, sender: str) -> str:
    state_manager.pause()
    return "⏸️ Agent paused. No scheduled tasks will run.\n\nType 'resume' to continue."


async def _handle_resume(args: str, sender: str) -> str:
    state_manager.resume()
    return "▶️ Agent resumed. Scheduled tasks will continue running."


async def _handle_tasks(args: str, sender: str) -> str:
    from ..scheduler import scheduler

    upcoming = scheduler.list_upcoming_tasks(limit=10)

    if not upcoming:
        return "No scheduled tasks."

    lines = ["*Scheduled Tasks*\n"]
    for task, time_str in upcoming:
        status = "✅" if task.enabled else "⏸️"
        lines.append(f"{status} *{task.name}*")
        lines.append(f"   {time_str}")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# Kai Calls commands
# =============================================================================

async def _handle_kaistatus(args: str, sender: str) -> str:
    try:
        from ..tasks.kai_calls.client import kai_client

        pending = await kai_client.get_pending_emails()
        stale = await kai_client.get_stale_emails(minutes=60)
        failed = await kai_client.get_failed_emails(hours=24)
        calls = await kai_client.get_recent_calls(hours=24)
        leads = await kai_client.get_new_leads(hours=24)

        lines = [
            "*KaiCalls Status*",
            "",
            f"*Email Queue*",
            f"  Pending: {len(pending)}",
            f"  Stale (>1h): {len(stale)}",
            f"  Failed (24h): {len(failed)}",
            "",
            f"*Activity (24h)*",
            f"  Calls: {len(calls)}",
            f"  New leads: {len(leads)}",
        ]

        if stale:
            lines.append("")
            lines.append("*Stale Emails:*")
            for e in stale[:3]:
                biz = e.get("businesses", {}).get("name", "?")
                lead = e.get("leads", {}).get("name", "?")
                lines.append(f"  - {biz}: {lead}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_kaiqueue(args: str, sender: str) -> str:
    try:
        from ..tasks.kai_calls.client import kai_client

        pending = await kai_client.get_pending_emails()

        if not pending:
            return "Email queue is empty. All caught up!"

        lines = [f"*Pending Emails ({len(pending)})*", ""]
        for e in pending[:10]:
            biz = e.get("businesses", {}).get("name", "?")
            lead = e.get("leads", {}).get("name", "?")
            subj = (e.get("subject") or "No subject")[:40]
            lines.append(f"- [{e['id'][:6]}] {biz} → {lead}")
            lines.append(f"  Subject: {subj}")

        if len(pending) > 10:
            lines.append(f"\n... and {len(pending) - 10} more")

        lines.append("\n_'kaisend' to auto-send approved_")
        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_kaisend(args: str, sender: str) -> str:
    try:
        from ..tasks.kai_calls.client import kai_client

        result = await kai_client.auto_send_queue()
        sent = result.get("sent", 0)
        failed = result.get("failed", 0)

        if sent == 0 and failed == 0:
            return "No emails to send (no auto-approve businesses or empty queue)."

        msg = f"Sent: {sent}"
        if failed > 0:
            msg += f", Failed: {failed}"
        return msg

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_kaicalls(args: str, sender: str) -> str:
    try:
        from ..tasks.kai_calls.business_ops import BusinessOpsTask
        from ..models import ScheduledTask, ScheduledTaskConfig

        task_obj = ScheduledTask(
            id="kaicalls_ondemand",
            name="KaiCalls On-Demand Report",
            cron_expression="0 8 * * *",
            task_type="kai_business_ops",
            client="kai-calls",
            config=ScheduledTaskConfig(),
            enabled=True,
        )

        handler = BusinessOpsTask()
        result = await handler.execute(task_obj)

        if result and result.get("success"):
            return result.get("data", {}).get("report", "Report generated (no content)")
        else:
            return f"Report failed: {result.get('error', 'unknown')}"

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_kaileads(args: str, sender: str) -> str:
    try:
        from ..tasks.kai_calls.client import kai_client

        leads = await kai_client.get_new_leads(hours=72)

        if not leads:
            return "No leads in the last 3 days."

        lines = [f"*Recent Leads ({len(leads)})*", ""]

        for lead in leads[:10]:
            name = lead.get("name") or lead.get("first_name") or "Unknown"
            status = lead.get("status") or "new"
            phone = lead.get("phone") or ""
            email = lead.get("email") or ""

            contact = phone or email or "no contact"

            lines.append(f"*{name}* [{status}]")
            lines.append(f"  {contact}")

            notes = lead.get("notes") or ""
            if "Looking for:" in notes:
                for line in notes.split("\n"):
                    if line.startswith("Looking for:"):
                        lines.append(f"  {line}")
                        break
            if "Next action:" in notes:
                for line in notes.split("\n"):
                    if line.startswith("Next action:"):
                        lines.append(f"  {line}")
                        break

            lines.append("")

        if len(leads) > 10:
            lines.append(f"... and {len(leads) - 10} more")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_kai_todo(text: str, sender: str, priority: str = "P2") -> str:
    if not text:
        return "Usage: todo: <description>"

    try:
        from ..tasks.kai_calls.task_board import add_task

        task = add_task(text, priority=priority)
        return f"Task added [{task['id'][:6]}]: {text} ({priority})"

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_kai_done(task_id: str, sender: str) -> str:
    if not task_id:
        return "Usage: done: <task-id>"

    try:
        from ..tasks.kai_calls.task_board import complete_task

        task = complete_task(task_id.strip())
        if task:
            return f"Done: {task['title']}"
        else:
            return f"Task not found: {task_id}"

    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# BuildWithKai commands
# =============================================================================

async def _handle_bwkstatus(args: str, sender: str) -> str:
    try:
        from ..tasks.buildwithkai.client import bwk_client

        gen_stats = await bwk_client.get_generation_stats(hours=24)
        stuck = await bwk_client.get_stuck_generations(minutes=30)
        funnel = await bwk_client.get_user_funnel_data()
        revenue = await bwk_client.get_revenue_stats(days=7)

        lines = [
            "*BWK Status*",
            "",
            "*Generations (24h)*",
            f"  Total: {gen_stats['total']}",
            f"  Completed: {gen_stats['completed']}",
            f"  Failed: {gen_stats['failed']}",
            f"  Error rate: {gen_stats['error_rate']}%",
            f"  Stuck (>30min): {len(stuck)}",
            "",
            "*Users*",
            f"  Total: {funnel['total_users']}",
            f"  With products: {funnel['users_with_products']}",
            f"  Published: {funnel['users_with_published']}",
            "",
            "*Revenue*",
            f"  Total: ${revenue['total_revenue']:.2f}",
            f"  Published: {revenue['total_published']}",
            f"  Sales (7d): {revenue['recent_sales']}",
        ]

        if len(stuck) > 0:
            lines.append("")
            lines.append(f"*Stuck jobs: {len(stuck)}*")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_bwkgens(args: str, sender: str) -> str:
    try:
        from ..tasks.buildwithkai.client import bwk_client

        stats = await bwk_client.get_generation_stats(hours=24)
        failed = await bwk_client.get_failed_generations(hours=24)
        plan_stats = await bwk_client.get_business_plan_stats(hours=24)

        lines = [
            f"*BWK Generations (24h)*",
            "",
            f"Products: {stats['total']} total",
            f"  Completed: {stats['completed']}",
            f"  Failed: {stats['failed']}",
            f"  Processing: {stats['processing']}",
            f"  Error rate: {stats['error_rate']}%",
            "",
            f"Business plans (24h): {plan_stats['total']}",
        ]

        if plan_stats.get("by_status"):
            for status, count in plan_stats["by_status"].items():
                lines.append(f"  {status}: {count}")

        if failed:
            lines.append("")
            lines.append("*Recent failures:*")
            for f_item in failed[:5]:
                err = (f_item.get("error_message") or "Unknown")[:60]
                lines.append(f"  - {f_item['id'][:8]}: {err}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_bwkusers(args: str, sender: str) -> str:
    try:
        from ..tasks.buildwithkai.client import bwk_client

        funnel = await bwk_client.get_user_funnel_data()
        stuck = await bwk_client.get_stuck_users(hours=48)
        inactive = await bwk_client.get_inactive_users(days=7)

        lines = [
            "*BWK User Funnel*",
            "",
            f"Total users: {funnel['total_users']}",
            f"  → With plans: {funnel['users_with_plans']}",
            f"  → With products: {funnel['users_with_products']}",
            f"  → Published: {funnel['users_with_published']}",
            "",
            f"Stuck in onboarding (>48h): {len(stuck)}",
            f"Inactive (>7d): {len(inactive)}",
        ]

        if funnel.get("by_subscription"):
            lines.append("")
            lines.append("*By plan:*")
            for plan, count in funnel["by_subscription"].items():
                lines.append(f"  {plan}: {count}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_bwkrevenue(args: str, sender: str) -> str:
    try:
        from ..tasks.buildwithkai.client import bwk_client

        revenue = await bwk_client.get_revenue_stats(days=7)

        lines = [
            "*BWK Revenue*",
            "",
            f"Published products: {revenue['total_published']}",
            f"  With Stripe: {revenue['products_with_stripe']}",
            f"  Without Stripe: {revenue['products_without_stripe']}",
            "",
            f"Total revenue: ${revenue['total_revenue']:.2f}",
            f"Sales (7d): {revenue['recent_sales']}",
            f"Downloads (7d): {revenue['recent_downloads']}",
        ]

        if revenue["missed_revenue_products"] > 0:
            lines.append("")
            lines.append(
                f"*{revenue['missed_revenue_products']} products with downloads but no Stripe!*"
            )

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_bwkreport(args: str, sender: str) -> str:
    try:
        from ..tasks.buildwithkai.business_ops import BWKBusinessOpsTask
        from ..models import ScheduledTask, ScheduledTaskConfig

        task_obj = ScheduledTask(
            id="bwk_ondemand",
            name="BWK On-Demand Report",
            cron_expression="0 8 * * *",
            task_type="bwk_business_ops",
            client="buildwithkai",
            config=ScheduledTaskConfig(),
            enabled=True,
        )

        handler = BWKBusinessOpsTask()
        result = await handler.execute(task_obj)

        if result and result.get("success"):
            return result.get("data", {}).get("report", "Report generated (no content)")
        else:
            return f"Report failed: {result.get('error', 'unknown')}"

    except Exception as e:
        return f"Error: {str(e)}"


# =============================================================================
# Amazing Backyard Parties commands
# =============================================================================

async def _handle_abpstatus(args: str, sender: str) -> str:
    try:
        from ..tasks.abp.client import abp_client

        lead_stats = await abp_client.get_lead_stats(days=1)
        vendors = await abp_client.get_vendors()
        coverage = await abp_client.get_vendor_coverage()
        funnel = await abp_client.get_vendor_funnel()

        lines = [
            "*ABP Status*",
            "",
            "*Leads (24h)*",
            f"  Total: {lead_stats['total']}",
            f"  Matched: {lead_stats['matched']}",
            f"  Unmatched: {lead_stats['unmatched']}",
            f"  Match rate: {lead_stats['match_rate']}%",
            "",
            "*Vendors*",
            f"  Active: {len(vendors)}",
            f"  ZIP coverage: {coverage['total_covered_zips']}",
            f"  Gaps: {coverage['gap_count']}",
            "",
            "*Pipeline*",
            f"  Discovered: {funnel['discovered']}",
            f"  Invited: {funnel['invited']}",
            f"  Signed up: {funnel['signed_up']}",
        ]

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_abpleads(args: str, sender: str) -> str:
    try:
        from ..tasks.abp.client import abp_client

        leads = await abp_client.get_recent_leads(hours=72)

        if not leads:
            return "No leads in the last 3 days."

        lines = [f"*ABP Recent Leads ({len(leads)})*", ""]

        for lead in leads[:10]:
            name = lead.get("name") or lead.get("email") or "Unknown"
            event = lead.get("event_type") or "N/A"
            date = lead.get("event_date") or "N/A"
            matched = "matched" if lead.get("vendor_id") else "UNMATCHED"
            services = lead.get("services") or []

            lines.append(f"*{name}* [{matched}]")
            lines.append(f"  {event} on {date}")
            if services:
                lines.append(f"  Services: {', '.join(services[:3])}")
            lines.append("")

        if len(leads) > 10:
            lines.append(f"... and {len(leads) - 10} more")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_abpvendors(args: str, sender: str) -> str:
    try:
        from ..tasks.abp.client import abp_client

        vendors = await abp_client.get_vendors()
        coverage = await abp_client.get_vendor_coverage()
        funnel = await abp_client.get_vendor_funnel()
        pending = await abp_client.get_pending_vendor_signups(hours=48)

        lines = [
            "*ABP Vendor Report*",
            "",
            f"Active vendors: {len(vendors)}",
            f"ZIP coverage: {coverage['total_covered_zips']}",
            f"Demand ZIPs: {coverage['total_demand_zips']}",
            f"Coverage gaps: {coverage['gap_count']}",
            "",
            "*Discovery Pipeline*",
            f"  Discovered: {funnel['discovered']}",
            f"  Invited: {funnel['invited']} ({funnel['invite_rate']}%)",
            f"  Signed up: {funnel['signed_up']} ({funnel['signup_rate']}%)",
            f"  Pending signup (>48h): {len(pending)}",
        ]

        if coverage.get("gap_zips"):
            lines.append("")
            lines.append("*Top coverage gaps:*")
            for zc, count in list(coverage["gap_zips"].items())[:5]:
                lines.append(f"  ZIP {zc}: {count} leads, 0 vendors")

        return "\n".join(lines)

    except Exception as e:
        return f"Error: {str(e)}"


async def _handle_abpreport(args: str, sender: str) -> str:
    try:
        from ..tasks.abp.business_ops import ABPBusinessOpsTask
        from ..models import ScheduledTask, ScheduledTaskConfig

        task_obj = ScheduledTask(
            id="abp_ondemand",
            name="ABP On-Demand Report",
            cron_expression="0 8 * * *",
            task_type="abp_business_ops",
            client="abp",
            config=ScheduledTaskConfig(),
            enabled=True,
        )

        handler = ABPBusinessOpsTask()
        result = await handler.execute(task_obj)

        if result and result.get("success"):
            return result.get("data", {}).get("report", "Report generated (no content)")
        else:
            return f"Report failed: {result.get('error', 'unknown')}"

    except Exception as e:
        return f"Error: {str(e)}"
