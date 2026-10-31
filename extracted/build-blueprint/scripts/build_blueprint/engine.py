"""
build_blueprint.engine — Natural-language → governed implementation plan.

Pipeline:
    User Prompt → Intent Parser → Architecture Planner → Dependency Analyzer
    → Task Generator → Governance Review → Pocket OS / Manus Prime / Ledger

This is the front door into the Meta Software Factory. A single sentence
becomes a governed, executable build plan across the entire stack.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GovernanceStatus(str, Enum):
    PENDING = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


@dataclass
class Component:
    name: str
    kind: str  # api, worker, database, ui, service, cli, library, config
    description: str = ""
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Task:
    id: str
    description: str
    component: str
    subsystem: str  # dreamweaver, ralph5, igor_os, pocket_os
    estimated_minutes: int
    dependencies: list[str] = field(default_factory=list)
    priority: str = "medium"


@dataclass
class Architecture:
    stack: list[str]  # FastAPI, PostgreSQL, Redis, Neo4j, etc.
    pattern: str  # microservices, monolith, event-driven, serverless
    components: list[Component]
    diagram_mermaid: str = ""


@dataclass
class Blueprint:
    id: str
    prompt: str
    project_name: str
    architecture: Architecture
    tasks: list[Task]
    estimated_total_minutes: int
    risk_level: RiskLevel
    governance: GovernanceStatus
    created_at: str
    ecosystem_actions: list[dict]  # what gets dispatched to each subsystem


# ---------------------------------------------------------------------------
# Intent Parser
# ---------------------------------------------------------------------------

class IntentParser:
    """Map a natural-language prompt to a structured intent.

    Keyword-driven (deterministic). In production this would be an LLM call
    with a Pydantic schema, but for the skill context we use fast pattern
    matching that covers the common cases.
    """

    # Keyword → (stack, pattern, components)
    INTENT_MAP: list[tuple[list[str], dict]] = [
        # Memory / knowledge graph
        (
            ["memory engine", "knowledge graph", "neo4j", "graph database", "vector store"],
            {
                "stack": ["FastAPI", "Neo4j", "PostgreSQL", "Redis", "Qdrant"],
                "pattern": "microservices",
                "components": [
                    Component("api", "api", "REST API for memory operations"),
                    Component("graph-store", "database", "Neo4j knowledge graph"),
                    Component("vector-index", "database", "Qdrant vector embeddings"),
                    Component("cache-layer", "database", "Redis session and query cache"),
                    Component("worker", "worker", "Background indexing and sync"),
                    Component("admin-ui", "ui", "Graph visualization dashboard"),
                ],
            },
        ),
        # Auth service
        (
            ["auth", "authentication", "oauth", "login", "sso", "jwt"],
            {
                "stack": ["FastAPI", "PostgreSQL", "Redis", "SendGrid"],
                "pattern": "microservices",
                "components": [
                    Component("auth-api", "api", "OAuth2 / JWT authentication endpoints"),
                    Component("user-db", "database", "PostgreSQL user store"),
                    Component("session-store", "database", "Redis token blacklist and sessions"),
                    Component("email-service", "service", "SendGrid email verification and password reset"),
                    Component("admin-ui", "ui", "User management dashboard"),
                ],
            },
        ),
        # Dashboard / UI
        (
            ["dashboard", "ui", "frontend", "swiftui", "ios", "react", "vue"],
            {
                "stack": ["React", "TypeScript", "Tailwind CSS", "Vite"],
                "pattern": "microservices",
                "components": [
                    Component("web-ui", "ui", "Responsive dashboard application"),
                    Component("api-gateway", "api", "BFF layer for UI data aggregation"),
                    Component("component-library", "library", "Shared design system components"),
                ],
            },
        ),
        # API / backend service
        (
            ["api", "backend", "fastapi", "service", "endpoint", "rest", "graphql"],
            {
                "stack": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
                "pattern": "microservices",
                "components": [
                    Component("api", "api", "Core REST / GraphQL API"),
                    Component("database", "database", "PostgreSQL with Alembic migrations"),
                    Component("cache", "database", "Redis caching layer"),
                    Component("worker", "worker", "Background task processor"),
                ],
            },
        ),
        # CLI tool
        (
            ["cli", "command line", "terminal", "script"],
            {
                "stack": ["Python", "Click", "Rich"],
                "pattern": "monolith",
                "components": [
                    Component("cli", "cli", "Command-line interface"),
                    Component("core-lib", "library", "Shared business logic"),
                    Component("config", "config", "YAML-based configuration"),
                ],
            },
        ),
        # Database / schema
        (
            ["database", "schema", "postgres", "migration", "model"],
            {
                "stack": ["PostgreSQL", "Alembic", "SQLAlchemy"],
                "pattern": "monolith",
                "components": [
                    Component("models", "library", "SQLAlchemy ORM models"),
                    Component("migrations", "config", "Alembic migration chain"),
                    Component("seed-data", "config", "Development seed data"),
                ],
            },
        ),
    ]

    # Prompt → project name extraction
    NAME_PATTERNS = [
        r"(?:build|create|generate|make)\s+(?:a\s+|an\s+)?(.+?)(?:\s+with|\s+using|\s+for|\s*$)",
        r"add\s+(.+?)\s+to\s+",
        r"^(.+?)(?:\s*$)",
    ]

    @classmethod
    def parse(cls, prompt: str) -> dict:
        """Parse a prompt into structured intent."""
        lower = prompt.lower().strip()

        # Find best-matching intent
        best_match = None
        best_score = 0
        for keywords, intent in cls.INTENT_MAP:
            score = sum(1 for kw in keywords if kw in lower)
            if score > best_score:
                best_score = score
                best_match = intent

        if best_match is None:
            # Default: generic API service
            best_match = cls.INTENT_MAP[3][1]  # API/backend default

        # Extract project name
        project_name = cls._extract_name(prompt)

        return {
            "project_name": project_name,
            "stack": best_match["stack"],
            "pattern": best_match["pattern"],
            "components": [asdict(c) for c in best_match["components"]],
        }

    @classmethod
    def _extract_name(cls, prompt: str) -> str:
        """Extract a project name from the prompt."""
        # Try explicit patterns
        for pattern in cls.NAME_PATTERNS:
            m = re.search(pattern, prompt, re.IGNORECASE)
            if m:
                name = m.group(1).strip().rstrip(".")
                # Title-case it
                return name.strip().title()
        # Fallback: first 4 words, title-cased
        words = prompt.split()[:4]
        return " ".join(w.capitalize() for w in words)


# ---------------------------------------------------------------------------
# Architecture Planner
# ---------------------------------------------------------------------------

class ArchitecturePlanner:
    """Expand parsed intent into a full architecture specification.

    Adds dependency edges between components based on their kinds:
    - UI depends on API
    - API depends on database
    - Worker depends on database + cache
    """

    DEPENDENCY_RULES = {
        "ui": ["api"],
        "api": ["database", "cache"],
        "worker": ["database", "cache"],
        "service": ["api"],
        "library": [],
        "cli": ["library"],
        "config": [],
        "database": [],
    }

    @classmethod
    def plan(cls, intent: dict) -> Architecture:
        """Produce a full Architecture from parsed intent."""
        components = []
        for c in intent["components"]:
            kind = c.get("kind", "service")
            deps = cls.DEPENDENCY_RULES.get(kind, [])
            # Resolve deps to actual component names
            resolved_deps = []
            for dep_kind in deps:
                for other in intent["components"]:
                    if other.get("kind") == dep_kind:
                        resolved_deps.append(other["name"])
                        break
            components.append(Component(
                name=c["name"],
                kind=kind,
                description=c.get("description", ""),
                depends_on=resolved_deps,
            ))

        # Generate Mermaid diagram
        mermaid = cls._generate_mermaid(components, intent["project_name"])

        return Architecture(
            stack=intent["stack"],
            pattern=intent["pattern"],
            components=components,
            diagram_mermaid=mermaid,
        )

    @classmethod
    def _generate_mermaid(cls, components: list[Component], project_name: str) -> str:
        lines = ["graph TD"]
        lines.append(f'    title["{project_name}"]')
        for c in components:
            safe_name = c.name.replace("-", "_")
            icon = {"api": "🔌", "database": "🗄️", "ui": "🖥️", "worker": "⚙️",
                    "service": "📡", "cli": "💻", "library": "📦", "config": "⚙️"}.get(c.kind, "📋")
            lines.append(f'    {safe_name}["{icon} {c.name}<br/>{c.kind}"]')
        for c in components:
            safe_name = c.name.replace("-", "_")
            for dep in c.depends_on:
                safe_dep = dep.replace("-", "_")
                lines.append(f"    {safe_name} --> {safe_dep}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Dependency Analyzer
# ---------------------------------------------------------------------------

class DependencyAnalyzer:
    """Analyze component dependencies and detect cycles, orphans, and ordering.

    Produces a topological sort of components (Kahn's algorithm) so the
    task generator can create tasks in the correct build order.
    """

    @classmethod
    def analyze(cls, architecture: Architecture) -> dict:
        components = architecture.components
        name_to_idx = {c.name: i for i, c in enumerate(components)}

        # Build adjacency and in-degree
        in_degree = {c.name: 0 for c in components}
        adj = {c.name: [] for c in components}

        for c in components:
            for dep in c.depends_on:
                if dep in name_to_idx:
                    adj[dep].append(c.name)
                    in_degree[c.name] += 1

        # Kahn's topological sort
        queue = [name for name, deg in in_degree.items() if deg == 0]
        order = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Detect cycles
        has_cycle = len(order) != len(components)
        orphans = [c.name for c in components if not c.depends_on and not any(c.name in other.depends_on for other in components)]

        return {
            "build_order": order,
            "has_cycle": has_cycle,
            "orphans": orphans,
            "total_components": len(components),
        }


# ---------------------------------------------------------------------------
# Task Generator
# ---------------------------------------------------------------------------

class TaskGenerator:
    """Generate concrete implementation tasks from the architecture.

    Each component produces tasks mapped to the appropriate subsystem:
    - dreamweaver: architecture, design, scaffolding
    - ralph5: implementation, testing, refactoring
    - igor_os: deployment, CI/CD, scheduling
    - pocket_os: documentation, memory, knowledge graph
    """

    TASK_TEMPLATES = {
        "api": [
            ("Create project scaffold and directory structure", "dreamweaver", 30),
            ("Define Pydantic models and schemas", "ralph5", 45),
            ("Build API endpoints and route handlers", "ralph5", 90),
            ("Add input validation and error handling middleware", "ralph5", 45),
            ("Write API tests (unit + integration)", "ralph5", 60),
            ("Generate OpenAPI documentation", "pocket_os", 20),
        ],
        "database": [
            ("Design database schema and relationships", "dreamweaver", 30),
            ("Create Alembic migration chain", "ralph5", 30),
            ("Write seed data scripts", "ralph5", 20),
            ("Add database tests", "ralph5", 30),
        ],
        "ui": [
            ("Design component tree and layout", "dreamweaver", 30),
            ("Build core UI components", "ralph5", 90),
            ("Add state management and data fetching", "ralph5", 60),
            ("Implement responsive design and accessibility", "ralph5", 45),
            ("Add UI tests", "ralph5", 45),
        ],
        "worker": [
            ("Design worker architecture and queue schema", "dreamweaver", 30),
            ("Build worker process and job handlers", "ralph5", 60),
            ("Add retry logic and dead-letter queue", "ralph5", 45),
            ("Write worker tests", "ralph5", 30),
        ],
        "service": [
            ("Define service interface and contracts", "dreamweaver", 30),
            ("Implement service logic", "ralph5", 60),
            ("Add service tests", "ralph5", 30),
        ],
        "cli": [
            ("Design CLI command structure", "dreamweaver", 20),
            ("Implement CLI commands and flags", "ralph5", 45),
            ("Add CLI tests", "ralph5", 20),
        ],
        "library": [
            ("Define public API and interfaces", "dreamweaver", 20),
            ("Implement core library logic", "ralph5", 60),
            ("Add library tests", "ralph5", 30),
            ("Generate library documentation", "pocket_os", 15),
        ],
        "config": [
            ("Create configuration templates", "ralph5", 15),
            ("Add environment validation", "ralph5", 15),
        ],
    }

    # Cross-cutting tasks added to every project
    CROSS_CUTTING = [
        ("Initialize git repository", "igor_os", 10),
        ("Set up CI/CD pipeline", "igor_os", 30),
        ("Create project README and documentation", "pocket_os", 20),
        ("Record project in knowledge graph", "pocket_os", 10),
        ("Create governance approval request", "pocket_os", 5),
    ]

    @classmethod
    def generate(cls, architecture: Architecture, analysis: dict) -> list[Task]:
        """Generate all tasks for the blueprint."""
        tasks: list[Task] = []
        component_order = analysis.get("build_order", [c.name for c in architecture.components])
        name_to_component = {c.name: c for c in architecture.components}

        for comp_name in component_order:
            comp = name_to_component.get(comp_name)
            if comp is None:
                continue
            templates = cls.TASK_TEMPLATES.get(comp.kind, cls.TASK_TEMPLATES["service"])
            for desc, subsystem, minutes in templates:
                tasks.append(Task(
                    id=f"task_{uuid.uuid4().hex[:8]}",
                    description=f"[{comp.name}] {desc}",
                    component=comp.name,
                    subsystem=subsystem,
                    estimated_minutes=minutes,
                    dependencies=[t.id for t in tasks[-2:]] if len(tasks) >= 2 else [],
                    priority="high" if subsystem == "dreamweaver" else "medium",
                ))

        # Add cross-cutting tasks
        for desc, subsystem, minutes in cls.CROSS_CUTTING:
            tasks.append(Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                description=desc,
                component="project",
                subsystem=subsystem,
                estimated_minutes=minutes,
                dependencies=[],
                priority="medium",
            ))

        return tasks


# ---------------------------------------------------------------------------
# Governance Review
# ---------------------------------------------------------------------------

class GovernanceReview:
    """Assess risk and determine governance status.

    Rules:
    - Any project touching auth or payment → HIGH risk, needs review
    - Projects with >10 tasks → MEDIUM risk
    - Database-only changes → LOW risk
    - New service with external exposure → MEDIUM risk
    """

    @classmethod
    def review(cls, prompt: str, architecture: Architecture, tasks: list[Task]) -> tuple[RiskLevel, GovernanceStatus]:
        lower = prompt.lower()
        task_count = len(tasks)

        # High-risk triggers
        high_risk_keywords = ["auth", "authentication", "payment", "billing", "pii", "gdpr", "hipaa", "production"]
        if any(kw in lower for kw in high_risk_keywords):
            return RiskLevel.HIGH, GovernanceStatus.NEEDS_REVIEW

        # Medium-risk triggers
        medium_risk_keywords = ["deploy", "migration", "refactor", "public", "external"]
        if any(kw in lower for kw in medium_risk_keywords) or task_count > 10:
            return RiskLevel.MEDIUM, GovernanceStatus.PENDING

        # Critical: destructive operations
        critical_keywords = ["drop", "delete all", "truncate", "purge", "destroy"]
        if any(kw in lower for kw in critical_keywords):
            return RiskLevel.CRITICAL, GovernanceStatus.NEEDS_REVIEW

        return RiskLevel.LOW, GovernanceStatus.PENDING


# ---------------------------------------------------------------------------
# Blueprint Compiler (the main entry point)
# ---------------------------------------------------------------------------

class BlueprintCompiler:
    """Compile a natural-language prompt into a governed Blueprint.

    This is the single entry point. Call ``compile(prompt)`` and get back
    a fully populated Blueprint ready for ecosystem dispatch.
    """

    @classmethod
    def compile(cls, prompt: str) -> Blueprint:
        now = datetime.now(timezone.utc).isoformat()

        # Step 1: Intent parsing
        intent = IntentParser.parse(prompt)

        # Step 2: Architecture planning
        architecture = ArchitecturePlanner.plan(intent)

        # Step 3: Dependency analysis
        analysis = DependencyAnalyzer.analyze(architecture)

        # Step 4: Task generation
        tasks = TaskGenerator.generate(architecture, analysis)

        # Step 5: Governance review
        risk, governance = GovernanceReview.review(prompt, architecture, tasks)

        # Total estimate
        total_minutes = sum(t.estimated_minutes for t in tasks)

        # Ecosystem actions — what gets dispatched where
        ecosystem_actions = cls._build_ecosystem_actions(
            intent["project_name"], architecture, tasks, risk, governance
        )

        return Blueprint(
            id=f"bp_{uuid.uuid4().hex[:12]}",
            prompt=prompt,
            project_name=intent["project_name"],
            architecture=architecture,
            tasks=tasks,
            estimated_total_minutes=total_minutes,
            risk_level=risk,
            governance=governance,
            created_at=now,
            ecosystem_actions=ecosystem_actions,
        )

    @classmethod
    def _build_ecosystem_actions(
        cls, project_name: str, architecture: Architecture,
        tasks: list[Task], risk: RiskLevel, governance: GovernanceStatus,
    ) -> list[dict]:
        """Build the dispatch payloads for each subsystem."""
        return [
            {
                "target": "pocket_os",
                "action": "create_project",
                "payload": {
                    "name": project_name,
                    "architecture": {
                        "stack": architecture.stack,
                        "pattern": architecture.pattern,
                    },
                    "risk": risk.value,
                    "governance": governance.value,
                },
            },
            {
                "target": "manus_prime",
                "action": "decompose_and_delegate",
                "payload": {
                    "goal": f"Build {project_name}",
                    "task_count": len(tasks),
                    "subsystems": list(set(t.subsystem for t in tasks)),
                    "estimated_minutes": sum(t.estimated_minutes for t in tasks),
                },
            },
            {
                "target": "ralph5",
                "action": "generate_code",
                "payload": {
                    "project": project_name,
                    "components": [c.name for c in architecture.components],
                    "task_count": len([t for t in tasks if t.subsystem == "ralph5"]),
                },
            },
            {
                "target": "igor_os",
                "action": "provision_infrastructure",
                "payload": {
                    "project": project_name,
                    "ci_cd": True,
                    "environments": ["dev", "staging"],
                },
            },
            {
                "target": "synapse_ledger",
                "action": "record_event",
                "payload": {
                    "event": "blueprint_created",
                    "project": project_name,
                    "risk": risk.value,
                    "governance": governance.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        ]


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def compile(prompt: str) -> dict:
    """Compile a prompt into a Blueprint and return it as a dict.

    This is the function the skill calls.
    """
    bp = BlueprintCompiler.compile(prompt)
    return {
        "id": bp.id,
        "prompt": bp.prompt,
        "project_name": bp.project_name,
        "architecture": {
            "stack": bp.architecture.stack,
            "pattern": bp.architecture.pattern,
            "components": [asdict(c) for c in bp.architecture.components],
            "diagram_mermaid": bp.architecture.diagram_mermaid,
        },
        "tasks": [asdict(t) for t in bp.tasks],
        "estimated_total_minutes": bp.estimated_total_minutes,
        "estimated_total_hours": round(bp.estimated_total_minutes / 60, 1),
        "risk_level": bp.risk_level.value,
        "governance": bp.governance.value,
        "created_at": bp.created_at,
        "ecosystem_actions": bp.ecosystem_actions,
    }
