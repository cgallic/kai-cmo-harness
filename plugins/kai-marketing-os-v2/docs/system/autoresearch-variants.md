# AutoResearch & Goal-Reinforced Learning: Literature Analysis & Marketing Optimization Architectures

**Date**: 2026-05-22  
**Status**: Research & Architecture Specification  
**Context**: Kai Marketing OS (`E:\Dev2\kai-cmo-harness-work`)  

---

## Executive Summary

This report explores the integration of **AutoResearch** and **Goal-Reinforced Learning** within the Kai Marketing OS. Originating in machine learning code optimization (Karpathy, 2026), the AutoResearch framework utilizes a closed-loop "propose $\rightarrow$ evaluate $\rightarrow$ commit/revert" cycle (known as the **ratchet loop**). 

By studying academic and open-source implementations, we identify four primary variants of AutoResearch:
1. **Minimalist Ratchet Loop** (single-track code optimization)
2. **Parallel Branching** (evolutionary multi-environment exploration)
3. **Bilevel Autoresearch** (meta-prompt optimization)
4. **Sandboxed Verification** (strict compliance and QA-guarded mutation)

We examine how these variants, alongside outcome-supervised reinforcement learning (RLAIF, Reinforcement Fine-Tuning/RFT), can be implemented inside Kai to optimize real-world marketing goals (such as cost-per-acquisition, conversion rate, and click-through rate) autonomously, while maintaining strict policy bounds and human safety gates.

---

## 1. The Core AutoResearch Paradigm

Traditionally, AI agents are used as "one-shot" generation tools (e.g., generating a blog post or writing an ad copy). In contrast, **AutoResearch** treats software development, model training, and content optimization as a continuous search problem over a mutable space.

```
                  ┌──────────────────────────────┐
                  │      Goal & Score Spec       │
                  │        (program.md)          │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │      Propose Modification    │◄──────────┐
                  │         (LLM Agent)          │           │
                  └──────────────┬───────────────┘           │
                                 │                           │
                                 ▼                           │
                  ┌──────────────────────────────┐           │ Revert
                  │      Run Evaluation/Loss     │           │ (Git Reset)
                  │         (prepare.py)         │           │
                  └──────────────┬───────────────┘           │
                                 │                           │
                                 ├───────────────────────────┤
                   Improvement?  │                           │ No
                                 ▼ Yes                       │
                  ┌──────────────────────────────┐           │
                  │      Commit to Version       │───────────┘
                  │       (Git Commit)           │
                  └──────────────────────────────┘
```

The framework consists of three key architectural roles:
*   **The Spec (`program.md`)**: Defines the goals, bounds, and optimization target (e.g., maximizing bits-per-byte/BPB or minimizing validation loss).
*   **The Sandbox (`train.py`)**: The only file the agent is allowed to edit, isolating modifications.
*   **The Evaluator (`prepare.py`)**: An immutable, automated testing script that runs the target file, measures performance, and returns a concrete, quantitative score.

If the evaluator reports a metric improvement, the agent commits the change to git; if the change fails to improve performance, or crashes the environment, the system executes `git revert` and prompts the agent to try a different approach.

---

## 2. AutoResearch Variants

Reviewing open-source developments (including `karpathy/autoresearch`, `OpenAGS`, `AutoResearchClaw`, and bilevel optimization papers) reveals distinct architectural variants that expand this concept:

### 2.1 Minimalist Ratchet Loop
*   **Mechanism**: A sequential, single-file mutation loop. The agent acts on a single sandbox file in a linear sequence of attempts.
*   **Strengths**: Extremely low resource requirements, easy to debug, and maintains a clean git history.
*   **Weaknesses**: Prone to getting stuck in local minima (if the agent cannot discover a sequence of changes that show immediate incremental improvement).

### 2.2 Parallel Branching (Multi-Branch Exploration)
*   **Mechanism**: The agent forks multiple git branches (or Docker containers) in parallel, proposing distinct mutations (e.g., Variant A, Variant B, Variant C) simultaneously. Each branch runs its evaluation asynchronously. The coordinator merges the branch with the highest performance delta.
*   **Strengths**: Employs genetic and evolutionary search principles, avoiding local minima. Highly suited for cloud/containerized scaling.
*   **Weaknesses**: High resource/compute overhead. Requires complex git merging and conflict resolution logic.

### 2.3 Bilevel Autoresearch (Meta-Optimization)
*   **Mechanism**: The agent operates on two layers:
    1.  *Inner Loop*: Mutating code or content to improve a metric.
    2.  *Outer Loop*: Mutating the system prompt, instructions, or evaluation criteria based on how quickly the inner loop converges.
*   **Strengths**: Self-improving agent capabilities. The agent learns how to research better over time by reflecting on historical run summaries.
*   **Weaknesses**: High prompt complexity and susceptibility to drift or "reward hacking" (where the outer loop relaxes constraints to make the inner loop appear more successful).

### 2.4 Sandboxed Verification
*   **Mechanism**: Before any mutation is evaluated for its core metric, it is run through static analysis, linter checks, and safety compilation gates. If it fails compliance (e.g., security flaws, syntax errors, or policy violations), it is rejected immediately without wasting execution budget.
*   **Strengths**: Enforces absolute safety, preventing code injection or platform violations.
*   **Weaknesses**: Requires robust local sandbox setups (e.g., Docker, restricted namespaces).

---

## 3. Goal-Reinforced Learning Around Outcomes

Standard Reinforcement Learning from Human Feedback (RLHF) is bottle-necked by human labeling costs. To achieve autonomous operation, agents leverage **outcome-supervised feedback** and **Reinforcement Learning from AI Feedback (RLAIF)**.

### 3.1 Verifiable Rewards vs. LLM Preference
Instead of asking an LLM "Is this copy good?" (which introduces model bias and reward hacking), outcome-supervised systems feed real-world metrics (CTR, conversions, CPA) directly back to the agent as reinforcement signals.

| Learning Framework | Reward Source | Optimization Loop | Best Use Case |
| :--- | :--- | :--- | :--- |
| **RLAIF (AI Feedback)** | Critic LLM Scoring | Policy optimization via preference labeling | Style alignment, readability, compliance check |
| **RFT (Reinforcement Fine-Tuning)** | Code execution, test success | PPO / DPO on reasoning paths | Code correctness, math, syntax validation |
| **Outcome-Supervised RL** | Real-world analytics (GSC, Meta API) | Multi-armed bandits / Tabular Q-learning | Landing page CVR, Ad spend optimization, CPA tuning |

### 3.2 Nous Research's AutoReason vs. Direct Outcome Learning
We integrate **AutoReason** (`scripts/ads/autoreason/loop.py`) into the ad copy generation step. 
*   **AutoReason** is a *game-theoretic tournament* (Incumbent, Critic, Author, Synthesizer, Judge) that operates entirely in the **reasoning space** before deployment. It aims to maximize the *predicted quality* and *brand alignment* of the copy.
*   **Outcome-Supervised Loops** operate in the **execution space** after deployment. They capture actual traffic behavior over weeks to evaluate if the deployed copy succeeded.

An ideal architecture combines both:
1.  **AutoReason** acts as the *Pre-Deployment Filter*: Refining copy and rejecting low-quality variants before they reach the public.
2.  **AutoResearch** acts as the *Post-Deployment Optimizer*: Iteratively mutating settings/copy, deploying them to A/B testing, observing conversions, and committing or reverting changes based on traffic outcomes.

---

## 4. Mapping AutoResearch to the Kai Marketing OS

To incorporate the AutoResearch pattern into Kai, we can define two specific optimization loops that utilize the existing codebase primitives (such as the `RuntimeStore` in [store.py](file:///e:/Dev2/kai-cmo-harness-work/kai/runtime/store.py) and `Attribution` in [attribution.py](file:///e:/Dev2/kai-cmo-harness-work/kai/analytics/attribution.py)).

### 4.1 Specification A: Autonomous Landing Page A/B Optimizer

This loop uses a **Parallel Branching** AutoResearch model to optimize landing page conversion rates.

```
                    ┌──────────────────────────────┐
                    │      GSC / Analytics State   │
                    │      (low CVR on /legal)     │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │    Fork Parallel Branches    │
                    │   (git branch lp-v1, lp-v2)  │
                    └──────────────┬───────────────┘
                                   │
                   ┌───────────────┴───────────────┐
                   ▼                               ▼
    ┌─────────────────────────────┐ ┌─────────────────────────────┐
    │     Variant A: UGC Copy     │ │   Variant B: Social Proof   │
    │   (Mutate templates/legal)  │ │   (Mutate templates/legal)  │
    └──────────────┬──────────────┘ └──────────────┬──────────────┘
                   │                               │
                   ▼                               ▼
    ┌─────────────────────────────┐ ┌─────────────────────────────┐
    │       Build & Verify        │ │       Build & Verify        │
    │     (npm run build / lint)  │ │     (npm run build / lint)  │
    └──────────────┬──────────────┘ └──────────────┬──────────────┘
                   │                               │
                   ▼                               ▼
    ┌─────────────────────────────┐ ┌─────────────────────────────┐
    │    Deploy to Traffic (50%)  │ │    Deploy to Traffic (50%)  │
    │       (A/B test route)      │ │       (A/B test route)      │
    └──────────────┬──────────────┘ └──────────────┬──────────────┘
                   │                               │
                   └───────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │    Attribution Window (7d)   │
                    │   (Track conversion shifts)  │
                    └──────────────┬───────────────┘
                                   │
                   ┌───────────────┴───────────────┐
      A Wins (+8% CVR)                             │ B Loses (-2% CVR)
                   ▼                               ▼
    ┌─────────────────────────────┐ ┌─────────────────────────────┐
    │     Merge lp-v1 to main     │ │    Discard lp-v2 branch     │
    │     (Commit & Lock In)      │ │       (Git branch -D)       │
    └─────────────────────────────┘ └─────────────────────────────┘
```

#### Code Integration Points
*   **State Detection**: A weekly cron task queries `scripts/analytics/conversions.py` and detects pages with high search impressions but low conversion rates.
*   **Sandbox**: Restricted to template files (e.g., `site/templates/landing-pages/{slug}.html`).
*   **Evaluator**: 
    1.  *Inner compliance*: Passes the proposed HTML through `scripts/quality/banned_word_check.py` and `scripts/quality_gates/seo_lint.py`.
    2.  *Live performance*: Uses `kai/analytics/attribution.py` to capture pre/post conversion deltas over a 7-day test window.
*   **Ratchet Action**: If the variant increases CVR with high confidence, the system runs `git commit` to merge it to `main`. If not, it runs `git checkout main -- templates/landing-pages/{slug}.html` to revert.

---

### 4.2 Specification B: Ad Set Bid & Budget experiment Loop

This loop uses a **Sequential Ratchet** AutoResearch model to optimize ad account cost-per-acquisition (CPA).

```
State (Weekly CPA is $45, target is $30) 
  --> Agent proposes modification to ad set settings: "Reduce target bid by 10%, narrow age targeting to 25-45"
  --> Execute change via scripts/ads/meta.py (Paused or live pending approval)
  --> Wait 3 days to gather performance data
  --> Query Meta API: measure conversion count and CPA
  --> Check CPA:
        ├── If CPA <= $35 (Improvement) --> Commit: save parameters to config.yaml as the new baseline
        └── If CPA > $45 (Worse) --> Revert: restore previous bid parameters via meta.py
```

#### Code Integration Points
*   **State Detection**: `scripts/ads/ad_loop.py` flags campaigns with high CPA.
*   **Sandbox**: The local configuration file (`config.yaml`) defining budget limits, bid caps, and targeting parameters.
*   **Evaluator**: Pulls ad set conversion metrics via `scripts/ads/meta.py:list-adsets`.
*   **Ratchet Action**: If the target parameters yield better CPA, the agent saves the new values to `config.yaml` and commits the config to the repo. Otherwise, it restores the git state of `config.yaml` and uploads the revert parameters back to the Meta Ads Manager.

---

## 5. Implementation Roadmap for AutoResearch inside Kai

To implement these loops pragmatically within the existing repository structure, we suggest a 3-step roll-out:

### Step 1: Create the Git Sandbox Helper
Write a utility script `kai/runtime/sandbox.py` that wraps git operations safely. This ensures the agent can easily stage, commit, and revert modifications to sandbox directories.

```python
import subprocess
from pathlib import Path

class GitSandbox:
    def __init__(self, repo_root: Path, allowed_paths: list[Path]):
        self.repo_root = repo_root
        self.allowed_paths = [Path(p).resolve() for p in allowed_paths]

    def _is_allowed(self, path: Path) -> bool:
        resolved = Path(path).resolve()
        return any(resolved == allowed or allowed in resolved.parents for allowed in self.allowed_paths)

    def commit_change(self, file_path: Path, message: str) -> bool:
        if not self._is_allowed(file_path):
            raise PermissionError(f"Access to path {file_path} is blocked by sandbox policy.")
        
        # Stage file
        subprocess.run(["git", "add", str(file_path)], cwd=str(self.repo_root), check=True)
        # Commit
        r = subprocess.run(["git", "commit", "-m", message], cwd=str(self.repo_root), capture_output=True)
        return r.returncode == 0

    def revert_change(self, file_path: Path):
        if not self._is_allowed(file_path):
            raise PermissionError(f"Access to path {file_path} is blocked by sandbox policy.")
        
        # Checkout file to discard changes
        subprocess.run(["git", "checkout", "HEAD", "--", str(file_path)], cwd=str(self.repo_root), check=True)
        # Clean untracked files
        subprocess.run(["git", "clean", "-fd", str(file_path)], cwd=str(self.repo_root), check=True)
```

### Step 2: Write the A/B Test Evaluator
Create `scripts/analytics/ab_evaluator.py` that hooks into search/conversion events and checks the performance difference between two variants.

*   Integrates with `kai/analytics/attribution.py` to compare conversion counts.
*   Outputs a simple JSON report containing:
    ```json
    {
      "variant_name": "lp-ugc-v1",
      "metric_delta": 0.12,
      "confidence": 0.94,
      "outcome": "improve"
    }
    ```

### Step 3: Implement the Loop Orchestrator
Add an autonomous runner (`scripts/ads/autoresearch_loop.py`) that initiates the loop:
1.  Loads underperforming pages/campaigns.
2.  Spawns a subagent to write a candidate mutation in the sandbox.
3.  Executes compliance checks (Four U's, banned words, Remotion compile).
4.  Deploys the candidate.
5.  Schedules an evaluation task in `agent.db` to check performance after the attribution window.
6.  Executes commit/revert based on the evaluation result.

---

## 6. Safety & Governance Guardrails

Running autonomous experimentation loops carries operational and brand risks. The following policies must be enforced at the runtime level:

1.  **Strict Sandbox Isolation**: The agent must only edit files in designated folders (e.g. `site/templates/` or `data/pending_ads/`). Editing system runner files (`kai/runtime/`, `agent/`, `scripts/`) is strictly blocked.
2.  **No Live Bidding Overrides Without Caps**: The agent cannot increase ad budgets beyond the absolute cap defined in the active `ActionMandate` (`kai/runtime/mandates.py`).
3.  **Mandatory Compile/Lint Gate**: Any code mutation (e.g. HTML/CSS changes) must successfully build (`npm run build` or similar compilation script) and pass static analysis. A compilation failure triggers an immediate `revert` without deployment.
4.  **Sequential Locking**: A resource (ad set, page, or sequence) can only be target to one active mutation loop at a time. The system locks the resource during its attribution window, preventing overlapping changes from polluting test results.
5.  **Manual Rollback Override**: Every proposal creates an offline backup in `RuntimeStore`. A human operator can trigger a manual rollback command at any time to instantly revert the system state to the last stable git commit.
