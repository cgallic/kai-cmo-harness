"""MeetKai Daemon — autonomous marketing agent executor.

Usage:
    python -m daemon start          # Start the daemon (foreground)
    python -m daemon detect         # Detect available CLIs
    python -m daemon test-task      # Run a test task
"""

import asyncio
import logging
import platform
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from typing import Optional

from .config import DaemonConfig
from .executor import execute_task
from .models import AgentTask, Runtime, TaskStatus

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("meetkai.daemon")


def detect_runtimes() -> list[Runtime]:
    """Detect Claude Code CLI on PATH."""
    runtimes = []
    claude_path = shutil.which("claude")
    if claude_path:
        try:
            result = subprocess.run(
                [claude_path, "--version"],
                capture_output=True, text=True, timeout=10,
            )
            version = result.stdout.strip() or "unknown"
        except Exception:
            version = "unknown"

        runtimes.append(Runtime(
            name="Claude-Code",
            cmd=claude_path,
            version=version,
        ))
    return runtimes


def get_supabase_client(config: DaemonConfig):
    """Create a Supabase client with service_role key (bypasses RLS)."""
    from supabase import create_client
    return create_client(config.supabase_url, config.supabase_service_key)


def _verified_prior_session(
    supabase,
    *,
    session_id: Optional[str],
    brand_id: str,
    task_id: str,
) -> Optional[str]:
    """Return `session_id` only if it belongs to a run of the same brand.

    Claude sessions persist under one host user (persist_session=True), so
    `options.resume = <session_id>` replays whatever conversation carries that
    id -- including another tenant's. agent_runs.session_id is writable by
    callers, so an attacker-chosen value would have resumed, and then extended,
    a transcript belonging to someone else.

    Fails closed: any doubt and the run simply starts fresh, which costs a
    little context and leaks nothing.
    """
    if not session_id:
        return None

    try:
        owner = supabase.table("agent_runs").select("brand_id").eq(
            "session_id", session_id
        ).limit(50).execute()
    except Exception:
        logger.warning(
            "Could not verify ownership of session %s for run %s; starting fresh",
            session_id, task_id,
        )
        return None

    rows = owner.data or []
    if not rows:
        logger.warning(
            "Session %s for run %s matches no known run; starting fresh",
            session_id, task_id,
        )
        return None

    foreign = {r.get("brand_id") for r in rows} - {brand_id}
    if foreign:
        logger.error(
            "Run %s asked to resume session %s owned by another brand; refusing",
            task_id, session_id,
        )
        return None

    return session_id


async def register_runtime(config: DaemonConfig, runtime: Runtime, supabase):
    """Register this daemon as a runtime in Supabase."""
    data = {
        "daemon_id": config.daemon_id,
        "name": config.daemon_name,
        "host_info": {
            "hostname": platform.node(),
            "os": platform.system(),
            "python": platform.python_version(),
            "claude_version": runtime.version,
            "capabilities": runtime.capabilities,
        },
        "status": "online",
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }

    # runtimes.brand_id has existed since migration 006 and the dashboard's
    # status route already filters on it -- but nothing ever wrote it, so it was
    # always NULL and claim_agent_task had nothing to scope by. Writing it here
    # is what actually binds this daemon to one tenant; migration 009 enforces
    # the binding in SQL.
    if config.brand_id:
        data["brand_id"] = config.brand_id

    # Upsert — if daemon_id already exists, update it
    result = supabase.table("runtimes").upsert(
        data, on_conflict="daemon_id"
    ).execute()

    if result.data:
        runtime_id = result.data[0]["id"]
        config.runtime_id = runtime_id
        if config.brand_id:
            logger.info(
                "Registered runtime: %s (id=%s, brand=%s)",
                config.daemon_name, runtime_id, config.brand_id,
            )
        else:
            logger.warning(
                "Registered runtime: %s (id=%s) UNSCOPED — it may claim tasks "
                "for any brand. Set MEETKAI_BRAND_ID before serving more than "
                "one tenant.",
                config.daemon_name, runtime_id,
            )
        return runtime_id

    raise RuntimeError("Failed to register runtime")


async def heartbeat_loop(config: DaemonConfig, supabase, shutdown_event: asyncio.Event):
    """Send heartbeats every N seconds."""
    while not shutdown_event.is_set():
        try:
            supabase.table("runtimes").update({
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "status": "online",
            }).eq("id", config.runtime_id).execute()
        except Exception as e:
            logger.warning("Heartbeat failed: %s", e)

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=config.heartbeat_interval)
            break
        except asyncio.TimeoutError:
            pass


async def poll_loop(config: DaemonConfig, supabase, shutdown_event: asyncio.Event):
    """Poll for claimable tasks and execute them."""
    semaphore = asyncio.Semaphore(config.max_concurrent)

    while not shutdown_event.is_set():
        try:
            # Use the atomic claim function
            result = supabase.rpc("claim_agent_task", {
                "p_runtime_id": config.runtime_id,
            }).execute()

            task_id = result.data if result.data else None

            if task_id:
                # Fetch full task data
                task_row = supabase.table("agent_runs").select("*").eq(
                    "id", task_id
                ).single().execute()

                if task_row.data:
                    brand_id = task_row.data["brand_id"]
                    task = AgentTask(
                        id=task_row.data["id"],
                        brand_id=brand_id,
                        task_type=task_row.data["task_type"],
                        skill=task_row.data.get("skill"),
                        trigger=task_row.data.get("trigger", "daemon"),
                        status="running",
                        input=task_row.data.get("input"),
                        risk_tier=task_row.data.get("risk_tier", "low"),
                        prior_session_id=_verified_prior_session(
                            supabase,
                            session_id=task_row.data.get("session_id"),
                            brand_id=brand_id,
                            task_id=task_row.data["id"],
                        ),
                        schedule_id=task_row.data.get("schedule_id"),
                    )

                    logger.info("Claimed task: %s (type=%s, skill=%s)",
                                task.id[:8], task.task_type, task.skill)

                    # Execute in bounded concurrency
                    async def _run(t: AgentTask):
                        async with semaphore:
                            await _execute_and_report(t, config, supabase)

                    asyncio.create_task(_run(task))

        except Exception as e:
            logger.warning("Poll error: %s", e)

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=config.poll_interval)
            break
        except asyncio.TimeoutError:
            pass


async def _execute_and_report(task: AgentTask, config: DaemonConfig, supabase):
    """Execute a task and write results back to Supabase."""
    try:
        result = await execute_task(task, config, supabase)

        # Update agent_runs with result
        update = {
            "status": result.status.value,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "output": result.output,
            "error": result.error,
            "session_id": result.session_id,
            "work_dir": result.work_dir,
            "progress": {
                "cost_usd": result.cost_usd,
                "num_turns": result.num_turns,
            },
        }
        supabase.table("agent_runs").update(update).eq("id", task.id).execute()

        if result.status == TaskStatus.COMPLETED:
            logger.info("Task completed: %s (cost=$%.4f, turns=%d)",
                        task.id[:8], result.cost_usd, result.num_turns)
        else:
            logger.warning("Task failed: %s — %s", task.id[:8], result.error)

    except Exception as e:
        logger.exception("Fatal error executing task %s", task.id[:8])
        try:
            supabase.table("agent_runs").update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", task.id).execute()
        except Exception:
            pass


async def run_daemon():
    """Main daemon entry point."""
    config = DaemonConfig.from_env()

    # 1. Detect CLIs
    runtimes = detect_runtimes()
    if not runtimes:
        logger.error("No agent CLIs found on PATH. Install Claude Code first.")
        sys.exit(1)

    runtime = runtimes[0]
    logger.info("Detected: %s (version=%s)", runtime.name, runtime.version)

    # 2. Connect to Supabase
    if not config.supabase_url or not config.supabase_service_key:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        sys.exit(1)

    # An unscoped runtime can claim any tenant's task. That is acceptable with
    # one tenant and unacceptable with two, so the operator can make it fatal
    # rather than relying on noticing a warning in the log.
    if config.require_brand_scope and not config.brand_id:
        logger.error(
            "MEETKAI_REQUIRE_BRAND_SCOPE=true but MEETKAI_BRAND_ID is unset. "
            "Refusing to start unscoped."
        )
        sys.exit(1)

    supabase = get_supabase_client(config)

    # 3. Register runtime
    await register_runtime(config, runtime, supabase)

    # 4. Setup shutdown
    shutdown_event = asyncio.Event()

    def _shutdown(sig, frame):
        logger.info("Shutdown signal received (%s)", sig)
        shutdown_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Daemon ready — polling for tasks")
    logger.info("  Poll interval: %ds", config.poll_interval)
    logger.info("  Heartbeat interval: %ds", config.heartbeat_interval)
    logger.info("  Max concurrent: %d", config.max_concurrent)
    logger.info("  Max budget/task: $%.2f", config.max_budget_per_task)
    logger.info("  Model: %s", config.claude_model)

    # 5. Start concurrent loops
    try:
        await asyncio.gather(
            heartbeat_loop(config, supabase, shutdown_event),
            poll_loop(config, supabase, shutdown_event),
        )
    finally:
        # Mark runtime offline
        try:
            supabase.table("runtimes").update({
                "status": "offline",
            }).eq("id", config.runtime_id).execute()
        except Exception:
            pass
        logger.info("Daemon stopped.")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MeetKai Daemon")
    parser.add_argument("command", choices=["start", "detect", "test-task"],
                        help="Command to run")
    args = parser.parse_args()

    if args.command == "detect":
        runtimes = detect_runtimes()
        if runtimes:
            for r in runtimes:
                print(f"  {r.name} ({r.cmd}) — v{r.version}")
                print(f"    Capabilities: {', '.join(r.capabilities)}")
        else:
            print("  No agent CLIs found on PATH")
        return

    if args.command == "test-task":
        print("TODO: Insert a test task into Supabase and watch daemon execute it")
        return

    if args.command == "start":
        asyncio.run(run_daemon())


if __name__ == "__main__":
    main()
