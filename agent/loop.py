"""
Main agent loop - the autonomous execution engine.

Watches the scheduler for due tasks and executes them.
Handles graceful shutdown and error recovery.
"""

import asyncio
import signal
import sys
import traceback
from datetime import datetime
from typing import Optional
from uuid import uuid4

from .config import agent_config
from .models import TaskExecution, TaskStatus, agent_db
from .scheduler import scheduler
from .state import state_manager
from .traces import SpanKind, SpanStatus, tracer


class AgentLoop:
    """
    Main autonomous agent loop.

    Responsibilities:
    - Poll scheduler for due tasks
    - Execute tasks with concurrency limits
    - Handle errors and retries
    - Maintain state across restarts
    """

    def __init__(self):
        self.running = False
        self.shutdown_event = asyncio.Event()
        self._current_executions: dict = {}

    async def start(self):
        """Start the agent loop."""
        print(f"[{datetime.now()}] Agent loop starting...")

        # Clear stale running tasks from previous session
        state_manager.clear_running_tasks()

        # Initialize default scheduled tasks if needed
        scheduler.create_default_tasks()

        self.running = True
        self.shutdown_event.clear()

        # Set up signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.stop())
            )

        # Start Discord bot if enabled (isolated — crash won't affect agent loop)
        if agent_config.discord_enabled and agent_config.discord_bot_token:
            from .channels.discord import discord_channel

            async def _run_discord():
                try:
                    await discord_channel.start()
                except Exception as e:
                    print(f"[{datetime.now()}] Discord bot crashed (isolated): {e}")

            asyncio.create_task(_run_discord())
            print(f"[{datetime.now()}] Discord bot starting in background...")

        print(f"[{datetime.now()}] Agent loop started. Press Ctrl+C to stop.")
        print(f"  Polling interval: {agent_config.polling_interval}s")
        print(f"  Max concurrent tasks: {agent_config.max_concurrent_tasks}")

        # Show upcoming tasks
        upcoming = scheduler.list_upcoming_tasks(limit=5)
        if upcoming:
            print("\nUpcoming tasks:")
            for task, time_str in upcoming:
                print(f"  - {task.name}: {time_str}")
        print()

        # Main loop
        try:
            while self.running:
                await self._tick()
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=agent_config.polling_interval
                    )
                    # If we get here, shutdown was requested
                    break
                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    pass
        except Exception as e:
            print(f"[{datetime.now()}] Fatal error in agent loop: {e}")
            traceback.print_exc()
        finally:
            await self._cleanup()

    async def stop(self):
        """Stop the agent loop gracefully."""
        print(f"\n[{datetime.now()}] Shutdown requested...")
        self.running = False
        self.shutdown_event.set()

    async def _process_active_graphs(self):
        """Evaluate active task graphs and start ready nodes."""
        active_graphs = agent_db.list_active_task_graphs()
        if not active_graphs:
            return

        running_tasks = state_manager.get_running_tasks()
        running_count = len(running_tasks)
        available_slots = agent_config.max_concurrent_tasks - running_count

        if available_slots <= 0:
            return

        for graph in active_graphs:
            nodes = graph.nodes

            for node_id, node in nodes.items():
                if available_slots <= 0:
                    break

                if node.status != "pending":
                    continue

                # Check dependencies
                parents = [edge[0] for edge in graph.edges if edge[1] == node_id]
                all_parents_completed = True
                for parent_id in parents:
                    parent_node = nodes.get(parent_id)
                    if not parent_node or parent_node.status != "completed":
                        all_parents_completed = False
                        break

                if all_parents_completed:
                    task_key = f"graph:{graph.graph_id}:{node_id}"
                    if task_key in running_tasks:
                        continue

                    print(f"[{datetime.now()}] Starting graph node: {graph.graph_id}:{node_id} ({node.task_type})")

                    # Update node status in db
                    agent_db.update_task_node(
                        graph.graph_id,
                        node_id,
                        status="running",
                        started_at=datetime.utcnow()
                    )

                    # Update graph status to running if it was pending
                    if graph.status == "pending":
                        agent_db.update_task_graph_status(graph.graph_id, "running")
                        graph.status = "running"

                    state_manager.add_running_task(task_key)
                    state_manager.record_activity()
                    available_slots -= 1

                    asyncio.create_task(self._execute_graph_node(graph, node_id))

    async def _execute_graph_node(self, graph, node_id: str):
        """Execute a single graph node using TaskOrchestrator."""
        from kai.execution import TaskOrchestrator
        task_key = f"graph:{graph.graph_id}:{node_id}"

        try:
            node = graph.nodes[node_id]
            orchestrator = TaskOrchestrator()
            result = await orchestrator.execute_node(graph.graph_id, node, graph.brand_id)

            success = result.get("success", True) if isinstance(result, dict) else True
            if success:
                agent_db.update_task_node(
                    graph.graph_id,
                    node_id,
                    status="completed",
                    outputs=result if isinstance(result, dict) else {},
                    completed_at=datetime.utcnow()
                )
                print(f"[{datetime.now()}] Graph node completed: {graph.graph_id}:{node_id}")
            else:
                error_msg = result.get("error") or result.get("summary") or "Node reported failure"
                await self._handle_graph_node_failure(graph, node_id, error_msg)
        except Exception as e:
            error_msg = str(e)
            print(f"[{datetime.now()}] Graph node failed with exception: {graph.graph_id}:{node_id} - {error_msg}")
            traceback.print_exc()
            await self._handle_graph_node_failure(graph, node_id, error_msg)
        finally:
            state_manager.remove_running_task(task_key)
            self._update_graph_status_if_done(graph.graph_id)

    async def _handle_graph_node_failure(self, graph, node_id: str, error_msg: str):
        """Handle execution failure for a node and skip its descendants recursively."""
        agent_db.update_task_node(
            graph.graph_id,
            node_id,
            status="failed",
            error=error_msg,
            completed_at=datetime.utcnow()
        )
        print(f"[{datetime.now()}] Graph node failed: {graph.graph_id}:{node_id} - {error_msg}")

        # Fetch fresh graph structure to skip descendants
        fresh_graph = agent_db.get_task_graph(graph.graph_id)
        if fresh_graph:
            self._skip_descendants(fresh_graph, node_id)

        # Replan instead of dead-end: flag the graph so the weekly CMO review
        # (agent/tasks/cmo_review.py) re-decomposes the remaining work with
        # this failure as context. needs_replan graphs are excluded from
        # list_active_task_graphs, so execution of this graph stops here.
        agent_db.update_task_graph_status(graph.graph_id, "needs_replan")
        print(f"[{datetime.now()}] Task graph {graph.graph_id} marked needs_replan after node {node_id} failed")

    def _skip_descendants(self, graph, node_id: str):
        """Recursively mark all downstream child nodes as skipped in the database."""
        children = [edge[1] for edge in graph.edges if edge[0] == node_id]
        for child_id in children:
            child_node = graph.nodes.get(child_id)
            if child_node and child_node.status in ("pending", "running"):
                agent_db.update_task_node(
                    graph.graph_id,
                    child_id,
                    status="skipped",
                    completed_at=datetime.utcnow()
                )
                print(f"[{datetime.now()}] Skipping downstream node: {graph.graph_id}:{child_id} because parent {node_id} failed/skipped")
                self._skip_descendants(graph, child_id)

    def _update_graph_status_if_done(self, graph_id: str):
        """Update overall graph status if all nodes are terminal."""
        fresh_graph = agent_db.get_task_graph(graph_id)
        if not fresh_graph:
            return

        # A graph flagged for replan keeps that status — the weekly CMO
        # review owns its next transition (needs_replan -> replanned).
        if fresh_graph.status == "needs_replan":
            return

        all_terminal = True
        has_failure = False
        for node in fresh_graph.nodes.values():
            if node.status in ("pending", "running"):
                all_terminal = False
                break
            if node.status == "failed":
                has_failure = True

        if all_terminal:
            new_status = "failed" if has_failure else "completed"
            agent_db.update_task_graph_status(graph_id, new_status)
            print(f"[{datetime.now()}] Task graph {graph_id} finished with status: {new_status}")

    async def _tick(self):
        """Single iteration of the agent loop."""
        if state_manager.is_paused():
            return

        # Process active graphs first
        await self._process_active_graphs()

        # Check for due tasks
        async with tracer.span(
            "scheduler.tick",
            kind=SpanKind.SCHEDULER,
        ) as scheduler_span:
            due_tasks = scheduler.get_due_tasks()
            running_count = len(state_manager.get_running_tasks())
            available_slots = agent_config.max_concurrent_tasks - running_count
            scheduler_span.add_attributes(
                due_count=len(due_tasks),
                running_count=running_count,
                available_slots=max(available_slots, 0),
            )

        if not due_tasks:
            return
        if available_slots <= 0:
            return

        # Execute due tasks up to available slots
        for task in due_tasks[:available_slots]:
            # Skip if already running
            if task.id in state_manager.get_running_tasks():
                continue

            # Create execution task
            asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task):
        """Execute a single scheduled task."""
        from .tasks import get_task_handler

        execution_id = str(uuid4())[:8]
        print(f"[{datetime.now()}] Starting task: {task.name} (exec: {execution_id})")

        # Mark task as started
        scheduler.mark_task_started(task)
        state_manager.add_running_task(task.id)
        state_manager.record_activity()

        # Create execution record
        execution = TaskExecution(
            id=execution_id,
            task_id=task.id,
            status=TaskStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        agent_db.create_execution(execution)

        async with tracer.trace(
            task_id=task.task_type,
            execution_id=execution_id,
            client=task.client,
            root_span_name=f"task:{task.task_type}",
            root_span_kind=SpanKind.TASK,
            inputs={
                "scheduled_task_id": task.id,
                "name": task.name,
                "cron": task.cron_expression,
                "config_extra": task.config.extra,
            },
        ) as trace_handle:
            try:
                # Get the task handler
                handler = get_task_handler(task.task_type)
                if handler is None:
                    raise ValueError(f"Unknown task type: {task.task_type}")

                # Execute with timeout
                timeout = task.config.timeout or agent_config.task_timeout
                async with tracer.span(
                    "task.execute",
                    kind=SpanKind.TASK,
                    inputs={"timeout_s": timeout},
                ) as exec_span:
                    result = await asyncio.wait_for(
                        handler.execute(task),
                        timeout=timeout,
                    )
                    exec_span.set_output(result)
                    exec_span.add_attributes(
                        success=bool(result and result.get("success", True)),
                    )

                # Success
                agent_db.update_execution(
                    execution_id,
                    status=TaskStatus.COMPLETED,
                    completed_at=datetime.utcnow(),
                    result=result or {}
                )
                state_manager.increment_stat("tasks_completed")

                print(f"[{datetime.now()}] Task completed: {task.name}")

                # Send notification if configured
                if task.config.notify_on_complete:
                    async with tracer.span(
                        "notification.send",
                        kind=SpanKind.NOTIFICATION,
                        inputs={"reason": "complete"},
                    ):
                        await self._notify_completion(task, result)

            except asyncio.TimeoutError:
                error = f"Task timed out after {timeout}s"
                print(f"[{datetime.now()}] Task timeout: {task.name}")
                async with tracer.span(
                    "task.timeout",
                    kind=SpanKind.RETRY,
                    attributes={"timeout_s": timeout},
                ) as timeout_span:
                    timeout_span.set_status(SpanStatus.TIMEOUT)
                await self._handle_task_failure(task, execution_id, error)

            except Exception as e:
                error = str(e)
                print(f"[{datetime.now()}] Task failed: {task.name} - {error}")
                traceback.print_exc()
                await self._handle_task_failure(task, execution_id, error)

            finally:
                state_manager.remove_running_task(task.id)

    async def _handle_task_failure(self, task, execution_id: str, error: str):
        """Handle a task failure with retry logic."""
        # Get current retry count
        executions = agent_db.get_recent_executions(task_id=task.id, limit=1)
        retry_count = executions[0].retry_count if executions else 0

        if task.config.retry_on_failure and retry_count < agent_config.retry_attempts:
            # Schedule retry
            agent_db.update_execution(
                execution_id,
                status=TaskStatus.PENDING,
                error=error,
                retry_count=retry_count + 1
            )
            state_manager.increment_stat("tasks_retried")
            print(f"[{datetime.now()}] Will retry task: {task.name} (attempt {retry_count + 1})")
        else:
            # Mark as failed
            agent_db.update_execution(
                execution_id,
                status=TaskStatus.FAILED,
                completed_at=datetime.utcnow(),
                error=error
            )
            state_manager.increment_stat("tasks_failed")

            # Send failure notification
            if agent_config.notify_on_failure:
                await self._notify_failure(task, error)

    async def _notify(self, message: str):
        """Send a notification via the best available channel."""
        # Try Discord first
        if agent_config.discord_enabled and agent_config.discord_channel_id:
            try:
                from .channels.discord import discord_channel
                if discord_channel.bot and discord_channel._ready.is_set():
                    await discord_channel.send_message(
                        agent_config.discord_channel_id,
                        message
                    )
                    return
            except Exception as e:
                print(f"Discord notification failed: {e}")

        # Fall back to WhatsApp
        if agent_config.whatsapp_enabled and agent_config.agent_owner_phone:
            try:
                from .channels.whatsapp import whatsapp_channel
                await whatsapp_channel.send_message(
                    agent_config.agent_owner_phone,
                    message
                )
            except Exception as e:
                print(f"WhatsApp notification failed: {e}")

    async def _notify_completion(self, task, result: Optional[dict]):
        """Send a notification about task completion."""
        message = f"✅ Task completed: {task.name}"
        if result and "summary" in result:
            message += f"\n\n{result['summary']}"
        await self._notify(message)

    async def _notify_failure(self, task, error: str):
        """Send a notification about task failure."""
        message = f"❌ Task failed: {task.name}\n\nError: {error}"
        await self._notify(message)

    async def _cleanup(self):
        """Clean up resources before shutdown."""
        print(f"[{datetime.now()}] Cleaning up...")

        # Stop Discord bot
        if agent_config.discord_enabled:
            try:
                from .channels.discord import discord_channel
                await discord_channel.stop()
            except Exception:
                pass

        # Wait for running tasks to complete (with timeout)
        running = state_manager.get_running_tasks()
        if running:
            print(f"  Waiting for {len(running)} running tasks...")
            # Give tasks 30 seconds to complete
            await asyncio.sleep(min(30, len(running) * 5))

        state_manager.clear_running_tasks()
        print(f"[{datetime.now()}] Agent loop stopped.")


# Global agent loop instance
agent_loop = AgentLoop()


async def run_agent():
    """Run the agent loop (async entry point)."""
    await agent_loop.start()


def main():
    """CLI entry point for the agent loop."""
    import argparse

    parser = argparse.ArgumentParser(description="CMO Agent Loop")
    parser.add_argument(
        "--test-schedule",
        action="store_true",
        help="Show scheduled tasks and exit"
    )
    parser.add_argument(
        "--init-tasks",
        action="store_true",
        help="Initialize default tasks and exit"
    )
    args = parser.parse_args()

    if args.test_schedule:
        print("Scheduled Tasks:")
        print("-" * 60)
        upcoming = scheduler.list_upcoming_tasks(limit=20)
        for task, time_str in upcoming:
            status = "enabled" if task.enabled else "disabled"
            print(f"  [{status}] {task.name}")
            print(f"          Cron: {task.cron_expression}")
            print(f"          Type: {task.task_type}")
            print(f"          Next: {time_str}")
            print()
        return

    if args.init_tasks:
        print("Initializing default tasks...")
        scheduler.create_default_tasks()
        print("Done.")
        return

    # Run the agent loop
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
