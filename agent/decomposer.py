"""
Goal Decomposer - decomposes brand goals into a validated, cycle-free Directed Acyclic Graph (DAG) of tasks.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from kai.runtime.models import KaiGoal, TaskGraph, TaskNode
from .llm.router import llm_router

DECOMPOSER_SYSTEM_PROMPT = """You are a strategic marketing operations planner for the Kai Marketing OS.
Your task is to take a business goal (KaiGoal) and decompose it into a sequence of actionable task nodes structured as a Directed Acyclic Graph (DAG).

Available Task Types that the runtime can execute:
- 'daily_analytics': For compiling traffic, lead, and campaign reports.
- 'seo_optimization': For optimizing pages, fixing technical issues, identifying keywords.
- 'content_pipeline': For drafting blog posts, articles, landing pages.
- 'ad_management': For adjusting budgets, testing creatives, running campaigns.
- 'lead_outreach': For cold email campaigns, warmup checks, lead lists.
- 'weekly_report': For preparing strategic weekly summaries.
- 'creative_assets': For generating images, creative briefs.

You must respond ONLY with a valid JSON object. No commentary, no markdown code block wrapper, just raw JSON.
The JSON object must follow this structure:
{
  "nodes": [
    {
      "node_id": "unique_node_identifier_e.g_seo_audit",
      "task_type": "one of the available task types listed above",
      "inputs": {
        "key": "value description or argument expected by the task handler"
      }
    }
  ],
  "edges": [
    ["from_node_id", "to_node_id"]
  ]
}

Ensure there are NO cycles in the graph (i.e. if A depends on B, B cannot depend on A directly or indirectly). Keep the plan minimal, logical, and focused on bridging the specific goal discrepancy. Use the provided Historical Performance Context to guide your strategy decisions (Exploitation vs Exploration)."""


def clean_json_text(text: str) -> str:
    """Strip markdown code block wrappers from JSON string."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[len("```json"):]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def has_cycle(nodes: List[str], edges: List[List[str]]) -> bool:
    """Return True if the directed graph defined by nodes and edges contains a cycle."""
    adj = {node: [] for node in nodes}
    for edge in edges:
        if len(edge) != 2:
            continue
        u, v = edge[0], edge[1]
        if u in adj and v in adj:
            adj[u].append(v)
            
    visited = set()
    rec_stack = set()
    
    def dfs(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False
        
    for node in nodes:
        if node not in visited:
            if dfs(node):
                return True
    return False


from kai.analytics.rewards import get_average_rewards_by_action_type


class GoalDecomposer:
    """Decomposes brand goals into a cycle-free DAG of TaskNodes."""

    async def decompose(self, goal: KaiGoal, rewards_filepath: Optional[str] = None) -> TaskGraph:
        """Decompose a goal discrepancy into a structured TaskGraph using LLM routing."""
        # Load historical rewards
        avg_rewards = get_average_rewards_by_action_type(rewards_filepath)
        
        rewards_context = ""
        if avg_rewards:
            rewards_context = "\nHistorical Performance Context (Average Reward Score per Action Type & Metric):\n"
            for action_type, metrics in avg_rewards.items():
                rewards_context += f"- Action Type '{action_type}':\n"
                for metric, avg_score in metrics.items():
                    rewards_context += f"  - KPI '{metric}': average reward = {avg_score:+.4f}\n"
            rewards_context += "\nStrategic Guideline:\n"
            rewards_context += f"- Prioritize action types with positive average rewards for target KPI '{goal.kpi_name}'.\n"
            rewards_context += f"- Avoid or redesign action types with negative average rewards for target KPI '{goal.kpi_name}'.\n"
            rewards_context += f"- If no data is shown for an action type on KPI '{goal.kpi_name}', you may explore it to test performance.\n"
        else:
            rewards_context = (
                "\nHistorical Performance Context: No historical reward records exist yet. "
                "Propose a standard exploratory strategy using available task types to establish performance baselines.\n"
            )

        prompt = f"""Decompose this marketing goal:
Goal ID: {goal.goal_id}
Brand ID: {goal.brand_id}
Name: {goal.name}
KPI: {goal.kpi_name}
Target Value: {goal.target_value}
Current Value: {goal.current_value}
Direction: {goal.target_direction}
Deadline: {goal.deadline}
Metadata: {json.dumps(goal.metadata)}

{rewards_context}

Please generate a DAG to achieve this goal."""

        # Call LLM router with strategy_analysis task type for smart routing
        response_text = await llm_router.complete(
            prompt,
            task_type="strategy_analysis",
            system=DECOMPOSER_SYSTEM_PROMPT,
            temperature=0.2,
        )
        
        cleaned = clean_json_text(response_text)
        try:
            data = json.loads(cleaned)
        except Exception as e:
            raise ValueError(f"Failed to parse goal decomposer JSON output: {e}\nRaw response: {response_text}")

        nodes_data = data.get("nodes", [])
        edges_data = data.get("edges", [])
        
        node_ids = [n.get("node_id") for n in nodes_data if n.get("node_id")]
        
        # Cycle detection check
        if has_cycle(node_ids, edges_data):
            raise ValueError(f"Cycle detected in the generated task graph: edges={edges_data}")
            
        nodes = {}
        for n in nodes_data:
            n_id = n.get("node_id")
            if not n_id:
                continue
            nodes[n_id] = TaskNode(
                node_id=n_id,
                task_type=n.get("task_type", ""),
                status="pending",
                inputs=n.get("inputs") or {},
                outputs={},
            )
            
        now = datetime.now(timezone.utc).isoformat()
        
        return TaskGraph(
            graph_id=f"graph_{uuid.uuid4().hex[:8]}",
            goal_id=goal.goal_id,
            brand_id=goal.brand_id,
            status="pending",
            nodes=nodes,
            edges=edges_data,
            created_at=now,
            updated_at=now
        )
