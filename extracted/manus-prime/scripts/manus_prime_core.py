"""
Manus Prime — Central Orchestration Intelligence
==================================================
Executive coordinator for an autonomous software ecosystem.
Plans, delegates, monitors, and verifies work across specialized subsystems.

Subsystems coordinated:
  - Igor OS     : runtime / execution / scheduling / automation
  - Dreamweaver : architecture / design / project scaffolding
  - Ralph5      : engineering / implementation / testing / refactoring
  - Pocket OS   : memory / knowledge graph / documents / context

Architecture: Hierarchical Orchestrator with Event-Driven Delegation
- Append-only activity log for full auditability
- Deterministic execution where possible
- Human approval gates for high-impact decisions
- Plugin-extensible agent registry
"""

from __future__ import annotations

import json
import hashlib
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
from collections import defaultdict
import threading


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------

class TaskStatus(Enum):
    PENDING = "pending"
    DELEGATED = "delegated"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    REROUTED = "rerouted"
    CANCELLED = "cancelled"


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class Subsystem(Enum):
    IGOR_OS = "igor_os"
    DREAMWEAVER = "dreamweaver"
    RALPH5 = "ralph5"
    POCKET_OS = "pocket_os"
    HUMAN = "human"  # for approval-required steps


class LogLevel(Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    DELEGATE = "delegate"
    APPROVAL = "approval"
    RETRY = "retry"


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ActivityLogEntry:
    """A single immutable entry in the append-only activity log."""
    id: str
    timestamp: str
    level: str
    subsystem: str
    task_id: str | None
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    hash: str = ""  # chained hash for tamper-evidence

    def __post_init__(self):
        if not self.hash:
            self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = f"{self.id}{self.timestamp}{self.level}{self.subsystem}{self.task_id}{self.message}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class Task:
    """A unit of work in the orchestration system."""
    id: str
    goal: str
    description: str
    assigned_subsystem: Subsystem | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    parent_goal_id: str | None = None
    dependencies: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = ""
    completed_at: str | None = None
    result: Any = None
    retry_count: int = 0
    max_retries: int = 3
    requires_approval: bool = False
    approved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class Goal:
    """A high-level objective broken into tasks."""
    id: str
    title: str
    description: str
    tasks: list[str] = field(default_factory=list)  # task IDs
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapability:
    """Describes what a subsystem agent can do."""
    subsystem: Subsystem
    name: str
    description: str
    capabilities: list[str]  # natural-language capability tags
    accepts: list[str]       # input types
    produces: list[str]      # output types
    endpoint: str | None = None  # future: API endpoint


# ---------------------------------------------------------------------------
# Activity Log (Append-Only, Tamper-Evident)
# ---------------------------------------------------------------------------

class ActivityLog:
    """
    Append-only, hash-chained activity log.
    Every action Manus Prime takes is recorded immutably.
    """

    def __init__(self):
        self._entries: list[ActivityLogEntry] = []
        self._previous_hash: str = "0" * 16  # genesis hash
        self._lock = threading.Lock()

    def append(
        self,
        level: LogLevel,
        subsystem: Subsystem | str,
        message: str,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ActivityLogEntry:
        entry = ActivityLogEntry(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.value,
            subsystem=subsystem if isinstance(subsystem, str) else subsystem.value,
            task_id=task_id,
            message=message,
            metadata=metadata or {},
        )
        # Chain the hash
        entry.hash = hashlib.sha256(
            f"{self._previous_hash}{entry.id}{entry.timestamp}{entry.message}".encode()
        ).hexdigest()[:16]
        with self._lock:
            self._entries.append(entry)
            self._previous_hash = entry.hash
        return entry

    def query(
        self,
        task_id: str | None = None,
        subsystem: str | None = None,
        level: str | None = None,
        limit: int = 50,
    ) -> list[ActivityLogEntry]:
        results = self._entries
        if task_id:
            results = [e for e in results if e.task_id == task_id]
        if subsystem:
            results = [e for e in results if e.subsystem == subsystem]
        if level:
            results = [e for e in results if e.level == level]
        return results[-limit:]

    def verify_integrity(self) -> bool:
        """Verify the hash chain is intact."""
        prev = "0" * 16
        for entry in self._entries:
            expected = hashlib.sha256(
                f"{prev}{entry.id}{entry.timestamp}{entry.message}".encode()
            ).hexdigest()[:16]
            if entry.hash != expected:
                return False
            prev = entry.hash
        return True

    def to_dicts(self) -> list[dict]:
        return [asdict(e) for e in self._entries]

    @property
    def count(self) -> int:
        return len(self._entries)


# ---------------------------------------------------------------------------
# Agent Registry (Plugin-Extensible)
# ---------------------------------------------------------------------------

class AgentRegistry:
    """
    Registry of all subsystem agents and their capabilities.
    New agents can be registered without modifying the core orchestrator.
    """

    def __init__(self):
        self._agents: dict[str, AgentCapability] = {}
        self._default_agents()

    def _default_agents(self):
        """Register the four core subsystem agents."""
        self.register(AgentCapability(
            subsystem=Subsystem.IGOR_OS,
            name="Igor OS",
            description="Runtime operating system for execution, services, workflows, scheduling, automation, and system state.",
            capabilities=[
                "execute_command", "schedule_task", "manage_service",
                "run_workflow", "monitor_system", "automate_process",
                "manage_state", "handle_events",
            ],
            accepts=["execution_plan", "workflow_definition", "schedule_spec"],
            produces=["execution_result", "system_status", "workflow_output"],
        ))
        self.register(AgentCapability(
            subsystem=Subsystem.DREAMWEAVER,
            name="Dreamweaver",
            description="Architect and builder that designs new applications, generates code, creates project structures, and evolves software designs.",
            capabilities=[
                "design_architecture", "scaffold_project", "generate_structure",
                "evolve_design", "create_spec", "review_architecture",
                "design_system", "api_design",
            ],
            accepts=["requirements", "design_brief", "existing_codebase"],
            produces=["architecture_doc", "project_scaffold", "design_spec"],
        ))
        self.register(AgentCapability(
            subsystem=Subsystem.RALPH5,
            name="Ralph5",
            description="Engineering and implementation specialist that writes, refactors, tests, debugs, and improves code.",
            capabilities=[
                "write_code", "refactor", "write_tests", "debug",
                "improve_performance", "code_review", "fix_bug",
                "implement_feature", "optimize",
            ],
            accepts=["design_spec", "codebase", "bug_report", "feature_request"],
            produces=["code", "test_results", "refactored_code", "fix"],
        ))
        self.register(AgentCapability(
            subsystem=Subsystem.POCKET_OS,
            name="Pocket OS",
            description="Personal memory, knowledge graph, second brain, document management, project context, and long-term memory.",
            capabilities=[
                "store_memory", "query_knowledge", "manage_documents",
                "build_context", "link_concepts", "retrieve_history",
                "index_project", "search_memory",
            ],
            accepts=["document", "memory_fragment", "query", "context_request"],
            produces=["memory_result", "document_list", "context_bundle", "knowledge_graph"],
        ))

    def register(self, agent: AgentCapability):
        self._agents[agent.subsystem.value] = agent

    def get(self, subsystem: Subsystem | str) -> AgentCapability | None:
        key = subsystem if isinstance(subsystem, str) else subsystem.value
        return self._agents.get(key)

    def find_best_agent(self, task_description: str) -> Subsystem | None:
        """
        Match a task description to the best-suited subsystem.
        Uses keyword matching against capability tags.
        """
        desc_lower = task_description.lower()
        scores: dict[str, int] = defaultdict(int)

        keyword_map = {
            Subsystem.IGOR_OS: [
                "run", "execute", "schedule", "workflow", "automate",
                "service", "deploy", "monitor", "system", "process",
                "pipeline", "ci/cd", "infrastructure", "ops",
            ],
            Subsystem.DREAMWEAVER: [
                "design", "architecture", "scaffold", "structure",
                "blueprint", "plan", "spec", "system design",
                "component", "interface", "api design", "pattern",
            ],
            Subsystem.RALPH5: [
                "code", "implement", "write", "refactor", "test",
                "debug", "fix", "build", "develop", "program",
                "function", "class", "module", "bug", "feature",
            ],
            Subsystem.POCKET_OS: [
                "remember", "memory", "knowledge", "document", "context",
                "history", "recall", "store", "retrieve", "search",
                "note", "reference", "learn", "index",
            ],
        }

        for subsystem, keywords in keyword_map.items():
            for kw in keywords:
                if kw in desc_lower:
                    scores[subsystem.value] += 1

        if not scores:
            return None

        best = max(scores, key=scores.get)
        return Subsystem(best)

    def list_all(self) -> list[AgentCapability]:
        return list(self._agents.values())


# ---------------------------------------------------------------------------
# Core Orchestrator
# ---------------------------------------------------------------------------

class ManusPrime:
    """
    Central orchestration intelligence.

    Responsibilities:
    - Break high-level goals into executable plans
    - Decide which subsystem should perform each task
    - Maintain shared memory across projects
    - Track project status and dependencies
    - Coordinate multiple agents working simultaneously
    - Validate outputs before accepting them
    - Detect failures and retry or reroute work
    - Produce progress dashboards and summaries
    - Keep an append-only activity log for auditing
    - Surface risks, blockers, and recommended next actions
    """

    def __init__(self):
        self.activity_log = ActivityLog()
        self.registry = AgentRegistry()
        self.goals: dict[str, Goal] = {}
        self.tasks: dict[str, Task] = {}
        self._shared_memory: dict[str, Any] = {}  # cross-project memory
        self._project_contexts: dict[str, dict] = {}  # per-project context
        self._lock = threading.Lock()

        self.activity_log.append(
            LogLevel.INFO, "manus_prime",
            "Manus Prime orchestration intelligence initialized."
        )

    # --- Goal Decomposition ---

    def decompose_goal(self, title: str, description: str) -> Goal:
        """
        Break a high-level goal into executable tasks.
        Uses heuristic decomposition based on the description.
        """
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        goal = Goal(id=goal_id, title=title, description=description)

        self.activity_log.append(
            LogLevel.INFO, "manus_prime",
            f"New goal registered: '{title}'",
            metadata={"goal_id": goal_id, "description": description[:200]},
        )

        # Heuristic task decomposition based on goal analysis
        tasks = self._decompose(goal)
        for task in tasks:
            task.parent_goal_id = goal_id
            self.tasks[task.id] = task
            goal.tasks.append(task.id)

        self.goals[goal_id] = goal
        return goal

    def _decompose(self, goal: Goal) -> list[Task]:
        """
        Heuristic decomposition engine.
        Analyzes the goal description and produces a sequence of tasks.
        """
        desc = goal.description.lower()
        tasks: list[Task] = []

        # Phase 1: Context & Memory (Pocket OS)
        if any(w in desc for w in ["remember", "context", "knowledge", "history", "document"]):
            tasks.append(Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                goal="Gather context and relevant knowledge",
                description="Query Pocket OS for project context, relevant documents, and knowledge graph entries.",
                assigned_subsystem=Subsystem.POCKET_OS,
                priority=Priority.HIGH,
            ))

        # Phase 2: Design (Dreamweaver)
        if any(w in desc for w in ["design", "build", "create", "architecture", "scaffold", "app", "system", "feature"]):
            tasks.append(Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                goal="Design architecture and specifications",
                description="Dreamweaver creates the architecture design, specifications, and project structure.",
                assigned_subsystem=Subsystem.DREAMWEAVER,
                priority=Priority.HIGH,
            ))

        # Phase 3: Implementation (Ralph5)
        if any(w in desc for w in ["code", "implement", "develop", "build", "write", "refactor", "fix", "feature"]):
            tasks.append(Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                goal="Implement the solution",
                description="Ralph5 writes, tests, and refines the implementation based on the design spec.",
                assigned_subsystem=Subsystem.RALPH5,
                priority=Priority.HIGH,
            ))

        # Phase 4: Execution / Deployment (Igor OS)
        if any(w in desc for w in ["run", "deploy", "execute", "schedule", "workflow", "automate", "pipeline"]):
            tasks.append(Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                goal="Execute and deploy",
                description="Igor OS handles execution, scheduling, and deployment of the completed work.",
                assigned_subsystem=Subsystem.IGOR_OS,
                priority=Priority.HIGH,
            ))

        # Phase 5: Store Results (Pocket OS)
        tasks.append(Task(
            id=f"task_{uuid.uuid4().hex[:8]}",
            goal="Persist results and update memory",
            description="Store outcomes, lessons learned, and updated context in Pocket OS.",
            assigned_subsystem=Subsystem.POCKET_OS,
            priority=Priority.MEDIUM,
        ))

        # Set dependencies (sequential by default)
        for i in range(1, len(tasks)):
            tasks[i].dependencies = [tasks[i - 1].id]

        return tasks

    # --- Delegation ---

    def delegate(self, task_id: str, subsystem: Subsystem | None = None) -> Task:
        """
        Assign a task to the best-suited subsystem (or a specified one).
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        if subsystem:
            task.assigned_subsystem = subsystem
        elif not task.assigned_subsystem:
            # Auto-assign based on capability matching
            best = self.registry.find_best_agent(task.description)
            task.assigned_subsystem = best or Subsystem.RALPH5  # default to Ralph5

        task.status = TaskStatus.DELEGATED
        task.updated_at = datetime.now(timezone.utc).isoformat()

        self.activity_log.append(
            LogLevel.DELEGATE, task.assigned_subsystem.value,
            f"Task delegated: '{task.goal}' → {task.assigned_subsystem.value}",
            task_id=task_id,
            metadata={"subsystem": task.assigned_subsystem.value, "priority": task.priority.name},
        )

        return task

    def delegate_all_pending(self, goal_id: str) -> list[Task]:
        """Delegate all pending tasks for a goal."""
        goal = self.goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found.")

        delegated = []
        for task_id in goal.tasks:
            task = self.tasks[task_id]
            if task.status == TaskStatus.PENDING:
                delegated.append(self.delegate(task_id))
        return delegated

    # --- Status Tracking ---

    def update_task_status(
        self, task_id: str, status: TaskStatus, result: Any = None
    ) -> Task:
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        old_status = task.status
        task.status = status
        task.updated_at = datetime.now(timezone.utc).isoformat()

        if status == TaskStatus.COMPLETED:
            task.completed_at = task.updated_at
            task.result = result
        elif status == TaskStatus.FAILED:
            task.retry_count += 1

        self.activity_log.append(
            LogLevel.INFO, task.assigned_subsystem.value if task.assigned_subsystem else "manus_prime",
            f"Task status: {old_status.value} → {status.value}: '{task.goal}'",
            task_id=task_id,
            metadata={"old_status": old_status.value, "new_status": status.value},
        )

        return task

    def get_goal_progress(self, goal_id: str) -> dict:
        """Return a progress summary for a goal."""
        goal = self.goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found.")

        task_statuses = []
        for tid in goal.tasks:
            t = self.tasks[tid]
            task_statuses.append({
                "id": t.id,
                "goal": t.goal,
                "status": t.status.value,
                "subsystem": t.assigned_subsystem.value if t.assigned_subsystem else "unassigned",
                "retries": t.retry_count,
            })

        total = len(task_statuses)
        completed = sum(1 for t in task_statuses if t["status"] == "completed")
        failed = sum(1 for t in task_statuses if t["status"] == "failed")

        return {
            "goal_id": goal_id,
            "title": goal.title,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "pending": total - completed - failed,
            "progress_pct": round((completed / total) * 100, 1) if total else 0,
            "tasks": task_statuses,
        }

    # --- Failure Handling ---

    def handle_failure(self, task_id: str, error_message: str) -> Task:
        """Handle a task failure: retry, reroute, or escalate."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        self.activity_log.append(
            LogLevel.ERROR, task.assigned_subsystem.value if task.assigned_subsystem else "unknown",
            f"Task failed: '{task.goal}' — {error_message}",
            task_id=task_id,
            metadata={"error": error_message, "retry_count": task.retry_count},
        )

        if task.retry_count < task.max_retries:
            # Retry with same subsystem
            task.status = TaskStatus.PENDING
            task.updated_at = datetime.now(timezone.utc).isoformat()
            self.activity_log.append(
                LogLevel.RETRY, task.assigned_subsystem.value if task.assigned_subsystem else "unknown",
                f"Retrying task (attempt {task.retry_count + 1}/{task.max_retries}): '{task.goal}'",
                task_id=task_id,
            )
        else:
            # Reroute: try a different subsystem
            task.status = TaskStatus.REROUTED
            task.updated_at = datetime.now(timezone.utc).isoformat()
            # Try Ralph5 as fallback for most things, or Dreamweaver for design
            fallback = Subsystem.RALPH5
            if task.assigned_subsystem == Subsystem.RALPH5:
                fallback = Subsystem.DREAMWEAVER
            task.assigned_subsystem = fallback
            task.retry_count = 0  # reset for new subsystem
            task.status = TaskStatus.PENDING

            self.activity_log.append(
                LogLevel.RETRY, "manus_prime",
                f"Rerouting task to {fallback.value}: '{task.goal}'",
                task_id=task_id,
            )

        return task

    # --- Human Approval Gate ---

    def request_approval(self, task_id: str, reason: str) -> Task:
        """Flag a task as requiring human approval before proceeding."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        task.requires_approval = True
        task.status = TaskStatus.AWAITING_APPROVAL
        task.updated_at = datetime.now(timezone.utc).isoformat()

        self.activity_log.append(
            LogLevel.APPROVAL, "manus_prime",
            f"Approval requested: '{task.goal}' — {reason}",
            task_id=task_id,
            metadata={"reason": reason},
        )

        return task

    def approve(self, task_id: str) -> Task:
        """Approve a task awaiting human sign-off."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")
        task.approved = True
        task.status = TaskStatus.PENDING  # ready to proceed
        task.updated_at = datetime.now(timezone.utc).isoformat()
        self.activity_log.append(
            LogLevel.APPROVAL, "human",
            f"Task approved: '{task.goal}'",
            task_id=task_id,
        )
        return task

    # --- Shared Memory ---

    def store_memory(self, key: str, value: Any, project_id: str | None = None):
        """Store a value in shared (cross-project) or project-scoped memory."""
        with self._lock:
            if project_id:
                if project_id not in self._project_contexts:
                    self._project_contexts[project_id] = {}
                self._project_contexts[project_id][key] = value
            else:
                self._shared_memory[key] = value

        self.activity_log.append(
            LogLevel.INFO, "pocket_os",
            f"Memory stored: '{key}' {'(project: ' + project_id + ')' if project_id else '(shared)'}",
        )

    def recall_memory(self, key: str, project_id: str | None = None) -> Any:
        """Recall a value from shared or project-scoped memory."""
        if project_id:
            return self._project_contexts.get(project_id, {}).get(key)
        return self._shared_memory.get(key)

    # --- Dashboards & Reporting ---

    def dashboard(self) -> dict:
        """Generate a full status dashboard."""
        goals_summary = []
        for g in self.goals.values():
            goals_summary.append(self.get_goal_progress(g.id))

        active_tasks = sum(
            1 for t in self.tasks.values()
            if t.status in (TaskStatus.PENDING, TaskStatus.DELEGATED, TaskStatus.IN_PROGRESS)
        )
        blocked_tasks = sum(
            1 for t in self.tasks.values()
            if t.status == TaskStatus.AWAITING_APPROVAL
        )
        failed_tasks = sum(
            1 for t in self.tasks.values()
            if t.status == TaskStatus.FAILED
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_goals": len(self.goals),
            "total_tasks": len(self.tasks),
            "active_tasks": active_tasks,
            "blocked_tasks": blocked_tasks,
            "failed_tasks": failed_tasks,
            "activity_log_entries": self.activity_log.count,
            "log_integrity": self.activity_log.verify_integrity(),
            "goals": goals_summary,
            "agents": [
                {
                    "name": a.name,
                    "subsystem": a.subsystem.value,
                    "capabilities": a.capabilities,
                }
                for a in self.registry.list_all()
            ],
        }

    def risks_and_blockers(self) -> list[dict]:
        """Surface risks, blockers, and recommended next actions."""
        items = []
        for task in self.tasks.values():
            if task.status == TaskStatus.AWAITING_APPROVAL:
                items.append({
                    "type": "blocker",
                    "task_id": task.id,
                    "goal": task.goal,
                    "detail": "Awaiting human approval.",
                    "recommendation": "Review and approve or reject the task.",
                })
            elif task.status == TaskStatus.FAILED:
                items.append({
                    "type": "risk",
                    "task_id": task.id,
                    "goal": task.goal,
                    "detail": f"Failed after {task.retry_count} retries.",
                    "recommendation": "Investigate root cause or manually reassign.",
                })
            elif task.status == TaskStatus.REROUTED:
                items.append({
                    "type": "risk",
                    "task_id": task.id,
                    "goal": task.goal,
                    "detail": f"Rerouted to {task.assigned_subsystem.value if task.assigned_subsystem else 'unknown'}.",
                    "recommendation": "Monitor the new subsystem's progress.",
                })
        return items

    # --- Workflow Optimization ---

    def suggest_optimizations(self) -> list[str]:
        """Analyze past executions and suggest workflow improvements."""
        suggestions = []
        subsystem_failures: dict[str, int] = defaultdict(int)

        for entry in self.activity_log._entries:
            if entry.level == "error" and entry.task_id:
                task = self.tasks.get(entry.task_id)
                if task and task.assigned_subsystem:
                    subsystem_failures[task.assigned_subsystem.value] += 1

        for sub, count in subsystem_failures.items():
            if count >= 3:
                suggestions.append(
                    f"Subsystem '{sub}' has {count} failures — consider reviewing its capability mapping or adding a fallback agent."
                )

        # Check for sequential bottlenecks
        for goal in self.goals.values():
            if len(goal.tasks) > 3:
                sequential = all(
                    len(self.tasks[tid].dependencies) > 0
                    for tid in goal.tasks[1:]
                )
                if sequential:
                    suggestions.append(
                        f"Goal '{goal.title}' is fully sequential — consider parallelizing independent tasks."
                    )

        return suggestions


# ---------------------------------------------------------------------------
# Demo / Smoke Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mp = ManusPrime()

    # Decompose a goal
    goal = mp.decompose_goal(
        "Build user authentication system",
        "Design and implement a complete authentication system with login, registration, and password reset. Deploy to staging."
    )
    print(f"\nGoal created: {goal.title} ({len(goal.tasks)} tasks)")

    # Delegate all tasks
    delegated = mp.delegate_all_pending(goal.id)
    for t in delegated:
        print(f"  → {t.goal} assigned to {t.assigned_subsystem.value} [{t.status.value}]")

    # Simulate task completions
    for tid in goal.tasks[:3]:
        mp.update_task_status(tid, TaskStatus.COMPLETED, {"status": "ok"})

    # Simulate a failure
    last_task = goal.tasks[-1]
    mp.handle_failure(last_task, "Connection timeout to Pocket OS")
    mp.handle_failure(last_task, "Connection timeout to Pocket OS (retry 2)")
    mp.handle_failure(last_task, "Connection timeout to Pocket OS (retry 3)")
    mp.handle_failure(last_task, "Connection timeout to Pocket OS (final)")

    # Request approval on a critical task
    mp.request_approval(goal.tasks[2], "Deployment to production requires sign-off.")

    # Dashboard
    dash = mp.dashboard()
    print(f"\n--- DASHBOARD ---")
    print(f"Goals: {dash['total_goals']} | Tasks: {dash['total_tasks']}")
    print(f"Active: {dash['active_tasks']} | Blocked: {dash['blocked_tasks']} | Failed: {dash['failed_tasks']}")
    print(f"Log integrity: {dash['log_integrity']}")

    # Risks
    risks = mp.risks_and_blockers()
    print(f"\n--- RISKS & BLOCKERS ({len(risks)}) ---")
    for r in risks:
        print(f"  [{r['type'].upper()}] {r['goal']}: {r['recommendation']}")

    # Optimizations
    opts = mp.suggest_optimizations()
    print(f"\n--- SUGGESTED OPTIMIZATIONS ({len(opts)}) ---")
    for o in opts:
        print(f"  • {o}")

    # Activity log sample
    print(f"\n--- ACTIVITY LOG (last 5 of {mp.activity_log.count}) ---")
    for entry in mp.activity_log.query(limit=5):
        print(f"  [{entry.level}] {entry.subsystem}: {entry.message}")
