---
name: manus-prime
description: Central orchestration intelligence for an autonomous software
  ecosystem. Plans, delegates, monitors, and verifies work across Igor OS,
  Dreamweaver, Ralph5, and Pocket OS. Use for multi-agent coordinat
triggers:
  - orchestrate this
  - coordinate my agents
  - manus prime
  - break this goal down
  - delegate across subsystems
  - run the orchestration
---

## When to use

The user wants to coordinate work across their autonomous software ecosystem. They have a high-level goal ("build a user auth system", "refactor the payment module", "design and deploy the new dashboard") and need Manus Prime to break it into tasks, delegate to the right subsystem, track progress, handle failures, and produce a dashboard. Use this skill for any multi-step software goal that spans design, implementation, execution, and memory.

## Inputs

- **goal_title** (required): Short name for the goal (e.g. "Build user authentication").
- **goal_description** (required): Full description of what needs to be accomplished. Include enough detail for the decomposition engine to identify which subsystems are needed. Mention keywords like "design", "code", "deploy", "remember", "test" to trigger the right task phases.
- **project_id** (optional): A project identifier for scoping memory and context.
- **approval_required** (optional): Set to true if any tasks need human sign-off before execution.

## Steps

### 1. Initialize Manus Prime

Run `scripts/manus_prime_core.py` to import the orchestrator, or import it directly:

```python
import sys
sys.path.insert(0, '<workspace_root>/scripts/')
from manus_prime_core import ManusPrime, TaskStatus, Subsystem, Priority

mp = ManusPrime()
```

The orchestrator auto-registers all four subsystem agents (Igor OS, Dreamweaver, Ralph5, Pocket OS) and initializes the append-only activity log.

### 2. Decompose the goal

```python
goal = mp.decompose_goal(goal_title, goal_description)
```

This produces 2-5 tasks depending on the description keywords:
- **Pocket OS** task if context/memory/knowledge keywords present
- **Dreamweaver** task if design/architecture/scaffold keywords present
- **Ralph5** task if code/implement/build/test keywords present
- **Igor OS** task if run/deploy/execute/schedule keywords present
- **Pocket OS** final task to persist results (always included)

Tasks are sequential by default (each depends on the previous). Report the task breakdown to the user.

### 3. Delegate all pending tasks

```python
delegated = mp.delegate_all_pending(goal.id)
for t in delegated:
    print(f"  {t.goal} → {t.assigned_subsystem.value}")
```

Each task is assigned to the best-matching subsystem based on capability keyword matching. Show the user the delegation plan.

### 4. Execute tasks in order

For each task in the goal's task list:

a. Mark it in progress:
```python
mp.update_task_status(task_id, TaskStatus.IN_PROGRESS)
```

b. If the task requires human approval (high-impact decisions like deployment, destructive operations, external spend):
```python
mp.request_approval(task_id, "Brief reason for approval")
```
Pause and ask the user to approve before continuing.

c. Execute the task using the appropriate Fig tooling:
- **Dreamweaver tasks**: Use `write_file`, `use_skill("website")`, or `use_skill("mobile-app")` for architecture and scaffolding.
- **Ralph5 tasks**: Write code, run tests via `shell`, refactor with `edit_file`.
- **Igor OS tasks**: Run commands via `shell`, publish via `publish_project`, schedule via `create_scheduled_task`.
- **Pocket OS tasks**: Store results with `remember_fact`, `save_instruction`, or `save_skill`. Query context with `search_facts`, `convo_search`, `artifact_search`.

d. On success:
```python
mp.update_task_status(task_id, TaskStatus.COMPLETED, result={"summary": "what happened"})
```

e. On failure:
```python
mp.handle_failure(task_id, "error message")
```
The orchestrator auto-retries up to 3 times, then reroutes to a fallback subsystem.

### 5. Produce the dashboard

After all tasks complete (or when the user asks for status):

```python
dash = mp.dashboard()
risks = mp.risks_and_blockers()
opts = mp.suggest_optimizations()
```

Present the user with:
- Goal progress (completed / total tasks, percentage)
- Active, blocked, and failed task counts
- Any risks or blockers with recommended actions
- Suggested workflow optimizations

### 6. Persist learnings

After the orchestration run, store durable takeaways:

```python
# Store project-level context
mp.store_memory("last_build_result", "success", project_id="my-project")
mp.store_memory("architecture_decision", "microservices with gRPC", project_id="my-project")

# Store cross-project learnings
mp.store_memory("preferred_test_framework", "pytest")
```

Also call `remember_fact` and `save_instruction` on the Fig platform for durable cross-session memory.

## Gotchas

- The decomposition engine is keyword-driven. If tasks are misassigned, manually override by passing `subsystem=Subsystem.RALPH5` (or another) to `mp.delegate(task_id, subsystem=...)`.
- The activity log is in-memory for a single session. For persistent audit trails, serialize `mp.activity_log.to_dicts()` to a file and upload it.
- Tasks are sequential by default. To parallelize, clear dependencies manually: `task.dependencies = []` before delegation.
- The orchestrator does not call external APIs — it produces the plan and tracks state. You (Fig) execute the actual subsystem work using your tools.
- `scripts/manus_prime_core.py` is the canonical engine. Stage it in your workspace under `scripts/` before importing.
