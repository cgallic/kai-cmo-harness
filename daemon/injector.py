"""Skill + knowledge injection into isolated workdirs.

Before spawning Claude Code, we create a workdir with:
- .claude/skills/ — relevant Kai skills (native Claude Code discovery)
- knowledge/ — relevant frameworks and checklists
- CLAUDE.md — task-specific instructions
- context/task.md — task description, brand info
"""

import json
import shutil
from pathlib import Path
from typing import List

from .config import DaemonConfig
from .models import AgentTask


# Map task_type → skills to inject
SKILL_MAP: dict[str, list[str]] = {
    "audit": ["kai-audit", "kai-seo-audit", "kai-cro"],
    "content": ["kai-write", "kai-brief", "kai-gate", "kai-repurpose"],
    "seo": ["kai-seo-audit", "kai-surround-sound", "kai-topical-map"],
    "ads": ["kai-ad-campaign", "kai-daily-ad-review", "kai-retarget"],
    "email": ["kai-email-system", "kai-newsletter"],
    "social": ["kai-social", "kai-video", "kai-video-production"],
    "analytics": ["kai-analytics"],
    "competitors": ["kai-competitors", "kai-surround-sound"],
    "landing_page": ["kai-landing-page", "kai-cro", "kai-gate"],
    "brand": ["kai-brand", "kai-growth-plan", "kai-growth-hacker"],
    "growth": ["kai-growth-plan", "kai-growth-hacker", "kai-analytics", "kai-gate"],
    "outreach": ["kai-cold-outreach", "kai-influencer", "kai-partnership"],
    "launch": ["kai-launch", "kai-landing-page", "kai-email-system", "kai-ad-campaign"],
}

# Map task_type → knowledge files to include
KNOWLEDGE_MAP: dict[str, list[str]] = {
    "audit": [
        "checklists/seo-checklist.md",
        "checklists/content-checklist.md",
        "checklists/technical-seo-audit-sop.md",
    ],
    "content": [
        "frameworks/content-copywriting/algorithmic-authorship.md",
        "frameworks/content-copywriting/four-us-framework.md",
        "frameworks/content-copywriting/perception-engineering.md",
        "channels/content-writing.md",
    ],
    "seo": [
        "frameworks/content-copywriting/algorithmic-authorship.md",
        "frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md",
        "channels/seo-content.md",
        "checklists/seo-checklist.md",
    ],
    "ads": [
        "channels/paid-acquisition.md",
        "channels/meta-advertising.md",
        "checklists/paid-acquisition-checklist.md",
        "checklists/meta-advertising-checklist.md",
    ],
    "email": [
        "channels/email-lifecycle.md",
        "checklists/email-checklist.md",
    ],
    "social": [
        "channels/tiktok-shop.md",
        "channels/tiktok-algorithm.md",
        "checklists/tiktok-checklist.md",
    ],
    "competitors": [
        "playbooks/business-model-marketing.md",
    ],
    "growth": [
        "playbooks/growth-hacker-first-hire-os.md",
        "playbooks/growth-loops-applied.md",
        "playbooks/demand-generation.md",
        "playbooks/social-media-strategy.md",
        "playbooks/influencer-marketing.md",
        "playbooks/event-webinar-marketing.md",
        "playbooks/paid-media-launch-playbook.md",
        "checklists/growth-hacker-first-hire-checklist.md",
    ],
    "landing_page": [
        "frameworks/content-copywriting/perception-engineering.md",
        "frameworks/content-copywriting/headline-formulas.md",
        "checklists/perception-engineering-checklist.md",
    ],
}


def prepare_workdir(task: AgentTask, config: DaemonConfig) -> Path:
    """Create an isolated workdir with skills, knowledge, and task context.

    Returns the workdir path (this becomes Claude Code's cwd).
    """
    run_id_short = task.id[:8]
    brand_id_short = task.brand_id[:8]
    base = Path(config.workspaces_root) / brand_id_short / run_id_short
    workdir = base / "workdir"

    # Create directory structure
    workdir.mkdir(parents=True, exist_ok=True)
    (base / "output").mkdir(exist_ok=True)
    (base / "logs").mkdir(exist_ok=True)

    # 1. Inject skills into .claude/skills/ (native discovery)
    _inject_skills(workdir, task, config)

    # 2. Inject relevant knowledge files
    _inject_knowledge(workdir, task, config)

    # 3. Write task context
    _write_task_context(workdir, task)

    # 4. Write CLAUDE.md with task-specific instructions
    _write_claude_md(workdir, task)

    return workdir


def _inject_skills(workdir: Path, task: AgentTask, config: DaemonConfig):
    """Copy relevant Kai skills into .claude/skills/ for native discovery."""
    skills_dest = workdir / ".claude" / "skills"
    skills_dest.mkdir(parents=True, exist_ok=True)

    # Determine which skills to inject
    skill_names = _get_skills_for_task(task)
    skills_src = Path(config.skills_path)

    for skill_name in skill_names:
        src = skills_src / skill_name
        dest = skills_dest / skill_name
        if src.exists() and not dest.exists():
            shutil.copytree(src, dest)


def _inject_knowledge(workdir: Path, task: AgentTask, config: DaemonConfig):
    """Symlink relevant knowledge files into workdir."""
    knowledge_dest = workdir / "knowledge"
    knowledge_dest.mkdir(exist_ok=True)

    files = KNOWLEDGE_MAP.get(task.task_type, [])
    knowledge_src = Path(config.knowledge_path)

    for rel_path in files:
        src = knowledge_src / rel_path
        dest = knowledge_dest / Path(rel_path).name
        if src.exists() and not dest.exists():
            try:
                dest.symlink_to(src)
            except OSError:
                # Symlinks may not work on all platforms — fall back to copy
                shutil.copy2(src, dest)


def _write_task_context(workdir: Path, task: AgentTask):
    """Write task description and metadata."""
    context_dir = workdir / "context"
    context_dir.mkdir(exist_ok=True)

    context = {
        "task_id": task.id,
        "brand_id": task.brand_id,
        "task_type": task.task_type,
        "skill": task.skill,
        "trigger": task.trigger,
        "risk_tier": task.risk_tier,
        "input": task.input or {},
    }

    (context_dir / "task.json").write_text(json.dumps(context, indent=2))

    # Also write a human-readable version
    md = f"""# Task Context

- **Task ID**: {task.id}
- **Brand ID**: {task.brand_id}
- **Type**: {task.task_type}
- **Skill**: {task.skill or 'auto'}
- **Trigger**: {task.trigger}
- **Risk Tier**: {task.risk_tier}

## Input

```json
{json.dumps(task.input or {}, indent=2)}
```
"""
    (context_dir / "task.md").write_text(md)


def _write_claude_md(workdir: Path, task: AgentTask):
    """Write CLAUDE.md with task-specific instructions."""
    skill_names = _get_skills_for_task(task)
    skills_list = "\n".join(f"- `{s}`" for s in skill_names)

    claude_md = f"""# MeetKai Agent Task

You are an autonomous marketing agent executing a task for a brand.

## Your Task

**Type**: {task.task_type}
**Skill**: {task.skill or 'Use the most appropriate skill for this task type'}

Read `context/task.md` for full task details and input parameters.

## Available Skills

{skills_list}

## Available Knowledge

Check the `knowledge/` directory for frameworks, checklists, and guides relevant to this task.

## Rules

1. Complete the task fully — don't ask for clarification, make reasonable decisions
2. Write all output to the `../output/` directory
3. Apply quality gates (Four U's scoring, banned word check) to any content you produce
4. Be concise in your reasoning — focus on delivering the result
5. If the task involves content, apply Algorithmic Authorship rules from knowledge/
"""

    (workdir / "CLAUDE.md").write_text(claude_md)


def _get_skills_for_task(task: AgentTask) -> List[str]:
    """Determine which skills to inject based on task type and explicit skill."""
    skills = set()

    # Add skills for this task type
    if task.task_type in SKILL_MAP:
        skills.update(SKILL_MAP[task.task_type])

    # Add explicitly requested skill
    if task.skill:
        skills.add(task.skill)

    # Always include kai-gate for quality checks
    skills.add("kai-gate")

    return sorted(skills)
