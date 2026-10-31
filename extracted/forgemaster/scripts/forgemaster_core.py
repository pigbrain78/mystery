"""
ForgeMaster — Autonomous Productization & Manufacturing Layer
==============================================================
Turns successful experiments into repeatable, deployable, commercial-grade products.

Integrates with:
  - Manus Prime   : receives completed goals as raw material
  - Synapse Ledger: reads build history, writes factory memory
  - SAIL Governor : governance checks before packaging
  - Chronos Auditor: verification before release
  - ACE Marketplace: publishes capability objects

Architecture: Pipeline-based manufacturing with stage gates.
"""

from __future__ import annotations

import json
import hashlib
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------

class ProductStage(Enum):
    """The manufacturing pipeline from raw experiment to marketplace asset."""
    IDEA_QUEUE = "idea_queue"
    RESEARCH = "research"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    SECURITY = "security"
    CERTIFICATION = "certification"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    ITERATION = "iteration"
    RELEASED = "released"
    RETIRED = "retired"


class ProductStatus(Enum):
    DRAFT = "draft"
    IN_PRODUCTION = "in_production"
    VERIFIED = "verified"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class AssetType(Enum):
    INTERNAL_CAPABILITY = "internal_capability"
    MARKETPLACE_ASSET = "marketplace_asset"
    LICENSED_MODULE = "licensed_module"
    AUTONOMOUS_SERVICE = "autonomous_service"


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class CapabilityObject:
    """A packaged, versioned, governed capability ready for the marketplace."""
    id: str
    version: str
    creator: str
    name: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    security_score: float = 0.0
    reputation_score: float = 0.0
    governance_status: str = "pending"
    provenance_hash: str = ""
    asset_type: AssetType = AssetType.INTERNAL_CAPABILITY
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.provenance_hash:
            self.provenance_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = f"{self.id}{self.version}{self.name}{self.creator}{self.created_at}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class ProductDefinition:
    """The complete specification for a product being manufactured."""
    id: str
    name: str
    version: str
    description: str
    source_experiment_id: str | None = None  # the experiment/prototype this came from
    source_goal_id: str | None = None        # the Manus Prime goal that produced it
    current_stage: ProductStage = ProductStage.IDEA_QUEUE
    status: ProductStatus = ProductStatus.DRAFT
    api_specification: str = ""
    documentation: str = ""
    deployment_package: str = ""
    pricing_model: dict[str, Any] = field(default_factory=dict)
    security_checklist: list[str] = field(default_factory=list)
    versioning_scheme: str = "semver"
    support_requirements: str = ""
    license_metadata: dict[str, str] = field(default_factory=dict)
    capability_object: CapabilityObject | None = None
    stage_history: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class FactoryMemoryEntry:
    """A single build's lessons, stored for the factory to learn from."""
    build_id: str
    product_id: str
    successful_patterns: list[str] = field(default_factory=list)
    failure_patterns: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    promoted_skills: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class StageGate:
    """A checkpoint that must pass before a product advances to the next stage."""
    stage: ProductStage
    checks: list[str] = field(default_factory=list)
    required_approvals: list[str] = field(default_factory=list)
    passed: bool = False
    auditor_signoff: bool = False
    governor_signoff: bool = False
    notes: str = ""


# ---------------------------------------------------------------------------
# Stage Gate Definitions
# ---------------------------------------------------------------------------

STAGE_GATES: dict[ProductStage, StageGate] = {
    ProductStage.IDEA_QUEUE: StageGate(
        stage=ProductStage.IDEA_QUEUE,
        checks=["Idea is clearly defined", "Source experiment is documented", "Value proposition is articulated"],
        required_approvals=["Product Owner"],
    ),
    ProductStage.RESEARCH: StageGate(
        stage=ProductStage.RESEARCH,
        checks=["Market fit assessed", "Technical feasibility confirmed", "Dependencies identified"],
        required_approvals=["Product Owner"],
    ),
    ProductStage.ARCHITECTURE: StageGate(
        stage=ProductStage.ARCHITECTURE,
        checks=["Architecture documented", "API surface defined", "Data model designed", "Security boundaries drawn"],
        required_approvals=["Architect", "SAIL Governor"],
    ),
    ProductStage.IMPLEMENTATION: StageGate(
        stage=ProductStage.IMPLEMENTATION,
        checks=["Code complete", "Tests pass", "Documentation drafted", "API spec matches implementation"],
        required_approvals=["Engineering Lead"],
    ),
    ProductStage.TESTING: StageGate(
        stage=ProductStage.TESTING,
        checks=["Unit tests pass", "Integration tests pass", "Performance benchmarks met", "Edge cases covered"],
        required_approvals=["QA Lead"],
    ),
    ProductStage.SECURITY: StageGate(
        stage=ProductStage.SECURITY,
        checks=["Vulnerability scan clean", "Dependency audit passed", "SAIL Governor policy compliant", "Secrets audit clean"],
        required_approvals=["Security Lead", "SAIL Governor"],
    ),
    ProductStage.CERTIFICATION: StageGate(
        stage=ProductStage.CERTIFICATION,
        checks=["Chronos Auditor verification passed", "Build is reproducible", "Deterministic outputs confirmed", "Version comparison clean"],
        required_approvals=["Chronos Auditor", "SAIL Governor"],
    ),
    ProductStage.DEPLOYMENT: StageGate(
        stage=ProductStage.DEPLOYMENT,
        checks=["Deployment package built", "Rollback plan documented", "Monitoring configured", "Support runbook ready"],
        required_approvals=["DevOps Lead", "Product Owner"],
    ),
    ProductStage.MONITORING: StageGate(
        stage=ProductStage.MONITORING,
        checks=["Health metrics stable", "Error rates within threshold", "User feedback positive", "Performance within SLA"],
        required_approvals=["SRE Lead"],
    ),
    ProductStage.ITERATION: StageGate(
        stage=ProductStage.ITERATION,
        checks=["Feedback loop active", "Improvement backlog populated", "Factory memory updated", "Next version planned"],
        required_approvals=["Product Owner"],
    ),
}


# ---------------------------------------------------------------------------
# ForgeMaster Core
# ---------------------------------------------------------------------------

class ForgeMaster:
    """
    Autonomous Productization & Manufacturing Layer.

    Responsibilities:
    - Product Genesis: transform prototype → product definition → marketplace release
    - Factory Line Management: shepherd products through the manufacturing pipeline
    - Capability Packaging: produce governed, versioned CapabilityObjects
    - Factory Memory: every build becomes training data for the factory
    """

    def __init__(self):
        self.products: dict[str, ProductDefinition] = {}
        self.factory_memory: list[FactoryMemoryEntry] = []
        self.capability_registry: dict[str, CapabilityObject] = {}
        self.pipeline_queue: list[str] = []  # product IDs waiting for processing
        self._build_counter: int = 0

    # ------------------------------------------------------------------
    # 1. Product Genesis
    # ------------------------------------------------------------------

    def genesis(
        self,
        name: str,
        description: str,
        source_experiment_id: str | None = None,
        source_goal_id: str | None = None,
        version: str = "0.1.0",
    ) -> ProductDefinition:
        """
        Take a successful experiment/prototype and begin the productization process.
        Returns a ProductDefinition at IDEA_QUEUE stage.
        """
        product_id = f"prod_{uuid.uuid4().hex[:8]}"
        product = ProductDefinition(
            id=product_id,
            name=name,
            version=version,
            description=description,
            source_experiment_id=source_experiment_id,
            source_goal_id=source_goal_id,
            current_stage=ProductStage.IDEA_QUEUE,
        )
        product.stage_history.append({
            "stage": ProductStage.IDEA_QUEUE.value,
            "entered_at": product.created_at,
            "note": "Product genesis initiated.",
        })

        self.products[product_id] = product
        self.pipeline_queue.append(product_id)
        return product

    # ------------------------------------------------------------------
    # 2. Factory Line Management
    # ------------------------------------------------------------------

    def advance_stage(self, product_id: str) -> ProductStage | None:
        """
        Attempt to advance a product to the next pipeline stage.
        Checks the stage gate — if it passes, moves forward; otherwise stays.
        Returns the new stage (or current if gate failed).
        """
        product = self.products.get(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found.")

        stages = list(ProductStage)
        current_idx = stages.index(product.current_stage)

        if current_idx >= len(stages) - 1:
            return product.current_stage  # already at terminal stage

        next_stage = stages[current_idx + 1]
        gate = STAGE_GATES.get(next_stage)
        if not gate:
            return product.current_stage

        # Check the gate
        gate.passed = all(
            self._check_gate_condition(product, check)
            for check in gate.checks
        )

        if gate.passed:
            old_stage = product.current_stage
            product.current_stage = next_stage
            product.updated_at = datetime.now(timezone.utc).isoformat()
            product.stage_history.append({
                "stage": next_stage.value,
                "entered_at": product.updated_at,
                "note": f"Advanced from {old_stage.value}.",
            })

            if next_stage == ProductStage.RELEASED:
                product.status = ProductStatus.PUBLISHED

        return product.current_stage

    def _check_gate_condition(self, product: ProductDefinition, check: str) -> bool:
        """
        Evaluate a single gate condition against the product's current state.
        In production this would run actual verification; here we use heuristics.
        """
        check_lower = check.lower()

        if "api spec" in check_lower:
            return bool(product.api_specification)
        if "documentation" in check_lower:
            return bool(product.documentation)
        if "deployment package" in check_lower:
            return bool(product.deployment_package)
        if "security checklist" in check_lower:
            return len(product.security_checklist) > 0
        if "pricing" in check_lower:
            return bool(product.pricing_model)
        if "license" in check_lower:
            return bool(product.license_metadata)
        if "version" in check_lower:
            return bool(product.versioning_scheme)
        if "support" in check_lower:
            return bool(product.support_requirements)

        # For checks we can't automatically verify, default to True
        # (these require human or auditor sign-off)
        return True

    def get_pipeline_status(self) -> dict:
        """Return a snapshot of the entire manufacturing pipeline."""
        stage_counts: dict[str, int] = defaultdict(int)
        for p in self.products.values():
            stage_counts[p.current_stage.value] += 1

        return {
            "total_products": len(self.products),
            "queued": len(self.pipeline_queue),
            "stage_distribution": dict(stage_counts),
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "version": p.version,
                    "stage": p.current_stage.value,
                    "status": p.status.value,
                }
                for p in self.products.values()
            ],
        }

    # ------------------------------------------------------------------
    # 3. Capability Packaging
    # ------------------------------------------------------------------

    def package_capability(
        self,
        product_id: str,
        asset_type: AssetType = AssetType.INTERNAL_CAPABILITY,
        creator: str = "ForgeMaster",
    ) -> CapabilityObject:
        """
        Produce a governed, versioned CapabilityObject from a completed product.
        This is the output that feeds into the ACE Marketplace.
        """
        product = self.products.get(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found.")

        cap = CapabilityObject(
            id=f"cap_{uuid.uuid4().hex[:8]}",
            version=product.version,
            creator=creator,
            name=product.name,
            description=product.description,
            dependencies=[product.source_experiment_id] if product.source_experiment_id else [],
            security_score=self._calculate_security_score(product),
            reputation_score=self._calculate_reputation_score(product),
            governance_status="approved" if product.status == ProductStatus.PUBLISHED else "pending",
            asset_type=asset_type,
            tags=self._infer_tags(product),
        )

        product.capability_object = cap
        self.capability_registry[cap.id] = cap
        return cap

    def _calculate_security_score(self, product: ProductDefinition) -> float:
        """Score based on security checklist completion and governance status."""
        base = 5.0
        if product.security_checklist:
            base += min(len(product.security_checklist) * 0.5, 3.0)
        if product.current_stage in (ProductStage.SECURITY, ProductStage.CERTIFICATION, ProductStage.RELEASED):
            base += 2.0
        return min(base, 10.0)

    def _calculate_reputation_score(self, product: ProductDefinition) -> float:
        """Score based on build history, iterations, and factory memory."""
        base = 5.0
        related_memory = [m for m in self.factory_memory if m.product_id == product.id]
        if related_memory:
            success_count = sum(len(m.successful_patterns) for m in related_memory)
            base += min(success_count * 0.3, 3.0)
        if product.current_stage == ProductStage.RELEASED:
            base += 2.0
        return min(base, 10.0)

    def _infer_tags(self, product: ProductDefinition) -> list[str]:
        """Infer capability tags from the product description and metadata."""
        tags = []
        desc_lower = (product.description + " " + product.name).lower()
        keyword_map = {
            "api": "api", "auth": "authentication", "data": "data",
            "ml": "machine-learning", "ai": "artificial-intelligence",
            "db": "database", "cache": "caching", "queue": "messaging",
            "web": "web", "mobile": "mobile", "cli": "cli",
            "security": "security", "monitor": "monitoring",
            "test": "testing", "deploy": "deployment",
        }
        for kw, tag in keyword_map.items():
            if kw in desc_lower:
                tags.append(tag)
        return list(set(tags))

    def list_capabilities(self) -> list[dict]:
        """List all packaged capabilities in the registry."""
        return [
            {
                "id": c.id,
                "name": c.name,
                "version": c.version,
                "security_score": c.security_score,
                "reputation_score": c.reputation_score,
                "governance_status": c.governance_status,
                "asset_type": c.asset_type.value,
                "provenance_hash": c.provenance_hash,
            }
            for c in self.capability_registry.values()
        ]

    # ------------------------------------------------------------------
    # 4. Factory Memory
    # ------------------------------------------------------------------

    def record_build(
        self,
        product_id: str,
        successful_patterns: list[str] | None = None,
        failure_patterns: list[str] | None = None,
        lessons: list[str] | None = None,
        promoted_skills: list[str] | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> FactoryMemoryEntry:
        """
        Record a build's outcomes so the factory learns over time.
        Every build becomes training data.
        """
        self._build_counter += 1
        entry = FactoryMemoryEntry(
            build_id=f"build_{self._build_counter:04d}",
            product_id=product_id,
            successful_patterns=successful_patterns or [],
            failure_patterns=failure_patterns or [],
            lessons=lessons or [],
            promoted_skills=promoted_skills or [],
            metrics=metrics or {},
        )
        self.factory_memory.append(entry)
        return entry

    def query_factory_memory(
        self,
        product_id: str | None = None,
        pattern_keyword: str | None = None,
    ) -> list[FactoryMemoryEntry]:
        """Search factory memory for relevant lessons."""
        results = self.factory_memory
        if product_id:
            results = [m for m in results if m.product_id == product_id]
        if pattern_keyword:
            kw = pattern_keyword.lower()
            results = [
                m for m in results
                if any(kw in p.lower() for p in m.successful_patterns + m.failure_patterns + m.lessons)
            ]
        return results

    def get_factory_wisdom(self) -> dict:
        """Aggregate all factory memory into distilled wisdom."""
        all_successful = []
        all_failures = []
        all_lessons = []
        all_skills = []

        for entry in self.factory_memory:
            all_successful.extend(entry.successful_patterns)
            all_failures.extend(entry.failure_patterns)
            all_lessons.extend(entry.lessons)
            all_skills.extend(entry.promoted_skills)

        return {
            "total_builds": self._build_counter,
            "top_successful_patterns": self._top_n(all_successful, 5),
            "top_failure_patterns": self._top_n(all_failures, 5),
            "key_lessons": list(set(all_lessons)),
            "promoted_skills": list(set(all_skills)),
        }

    @staticmethod
    def _top_n(items: list[str], n: int) -> list[str]:
        counts: dict[str, int] = defaultdict(int)
        for item in items:
            counts[item] += 1
        return [item for item, _ in sorted(counts.items(), key=lambda x: -x[1])[:n]]

    # ------------------------------------------------------------------
    # 5. Dashboard
    # ------------------------------------------------------------------

    def dashboard(self) -> dict:
        """Full manufacturing dashboard."""
        pipeline = self.get_pipeline_status()
        wisdom = self.get_factory_wisdom()
        capabilities = self.list_capabilities()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline": pipeline,
            "factory_wisdom": wisdom,
            "capabilities": capabilities,
            "capability_count": len(capabilities),
        }


# ---------------------------------------------------------------------------
# Smoke Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    fm = ForgeMaster()

    # Product Genesis
    product = fm.genesis(
        name="ACE Reputation Engine",
        description="Agent reputation scoring engine for the autonomous software ecosystem.",
        source_experiment_id="exp_001",
        source_goal_id="goal_abc123",
    )
    print(f"Product genesis: {product.name} v{product.version} [{product.current_stage.value}]")

    # Populate the product definition
    product.api_specification = "REST API v1 — POST /score, GET /reputation/{agent_id}"
    product.documentation = "Full API docs with examples."
    product.deployment_package = "Docker image ace-reputation:0.1.0"
    product.pricing_model = {"tier": "freemium", "free_calls": 1000, "price_per_1k": 0.01}
    product.security_checklist = [
        "Input validation on all endpoints",
        "Rate limiting enforced",
        "SAIL Governor policy attached",
    ]
    product.license_metadata = {"type": "BSL", "url": "https://license.example.com/bsl"}
    product.support_requirements = "Community support via ACE Marketplace; enterprise SLA available."

    # Advance through stages
    for _ in range(12):
        new_stage = fm.advance_stage(product.id)
        print(f"  Stage: {new_stage.value}")

    # Package as capability
    cap = fm.package_capability(product.id, asset_type=AssetType.MARKETPLACE_ASSET)
    print(f"\nCapability packaged: {cap.name} v{cap.version}")
    print(f"  Security score: {cap.security_score}/10")
    print(f"  Reputation score: {cap.reputation_score}/10")
    print(f"  Governance: {cap.governance_status}")
    print(f"  Provenance: {cap.provenance_hash}")

    # Record factory memory
    fm.record_build(
        product_id=product.id,
        successful_patterns=["FastAPI + PostgreSQL + Redis + SAIL Gate"],
        failure_patterns=["Direct agent-to-agent execution"],
        lessons=["Always route through Governor"],
        promoted_skills=["Governed API Architecture v2"],
        metrics={"build_time_s": 342, "test_coverage_pct": 94.2},
    )

    # Dashboard
    dash = fm.dashboard()
    print(f"\n--- FORGEMASTER DASHBOARD ---")
    print(f"Pipeline: {dash['pipeline']['total_products']} products, {dash['pipeline']['queued']} queued")
    print(f"Capabilities: {dash['capability_count']}")
    print(f"Factory builds: {dash['factory_wisdom']['total_builds']}")
    print(f"Top patterns: {dash['factory_wisdom']['top_successful_patterns']}")
    print(f"Key lessons: {dash['factory_wisdom']['key_lessons']}")
