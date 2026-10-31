---
name: forgemaster
description: Autonomous Productization & Manufacturing Layer — turns successful
  experiments into repeatable, deployable, commercial-grade products with a
  10-stage pipeline, capability packaging, and factory memory
triggers:
  - productize this
  - manufacturing pipeline
  - package this capability
  - ForgeMaster
  - factory line
  - turn this into a product
---

## When to use

The user wants to productize a successful experiment or prototype, manage the manufacturing pipeline, package capabilities for the ACE Marketplace, or query factory memory for build patterns and lessons. Use when the user says "productize this", "manufacturing pipeline", "package this capability", "ForgeMaster", "factory line", or describes turning a prototype into a shippable product.

## Inputs

- **action** (required): One of `genesis`, `advance`, `pipeline`, `package`, `record_build`, `memory`, `dashboard`.
- **product_name** (for genesis): Name of the product being created.
- **product_description** (for genesis): What the product does.
- **source_experiment_id** (optional): The experiment or prototype this came from.
- **source_goal_id** (optional): The Manus Prime goal that produced the source material.
- **product_id** (for advance/package/record_build): The product to operate on.
- **asset_type** (for package): One of `internal_capability`, `marketplace_asset`, `licensed_module`, `autonomous_service`.
- **build_data** (for record_build): Dict with successful_patterns, failure_patterns, lessons, promoted_skills, metrics.

## Steps

### 1. Import the engine

```python
import sys
sys.path.insert(0, '<workspace_root>/scripts/')
from forgemaster_core import ForgeMaster, ProductStage, ProductStatus, AssetType

fm = ForgeMaster()
```

### 2. Execute the requested action

#### genesis — Start productizing a prototype

```python
product = fm.genesis(
    name=product_name,
    description=product_description,
    source_experiment_id=source_experiment_id,
    source_goal_id=source_goal_id,
)
```

Report the product ID, name, version, and current stage to the user. Then populate the product definition by asking the user or inferring:
- `product.api_specification` — the API surface
- `product.documentation` — docs summary
- `product.deployment_package` — how it ships
- `product.pricing_model` — dict with pricing details
- `product.security_checklist` — list of security items addressed
- `product.license_metadata` — license type and URL
- `product.support_requirements` — support model

#### advance — Move a product through the pipeline

```python
new_stage = fm.advance_stage(product_id)
```

The pipeline stages are: IDEA_QUEUE → RESEARCH → ARCHITECTURE → IMPLEMENTATION → TESTING → SECURITY → CERTIFICATION → DEPLOYMENT → MONITORING → ITERATION → RELEASED.

Each stage has a gate with checks. If the gate passes, the product advances. If not, tell the user which checks are still needed. Call advance repeatedly until the product reaches the desired stage or gets blocked.

#### pipeline — Show the manufacturing pipeline status

```python
status = fm.get_pipeline_status()
```

Present the stage distribution and product list.

#### package — Create a CapabilityObject for marketplace

```python
cap = fm.package_capability(product_id, asset_type=AssetType.MARKETPLACE_ASSET)
```

Report the capability ID, security score, reputation score, governance status, and provenance hash. This capability object is ready for ACE Marketplace or internal registry.

#### record_build — Store factory memory

```python
entry = fm.record_build(
    product_id=product_id,
    successful_patterns=build_data.get("successful_patterns", []),
    failure_patterns=build_data.get("failure_patterns", []),
    lessons=build_data.get("lessons", []),
    promoted_skills=build_data.get("promoted_skills", []),
    metrics=build_data.get("metrics", {}),
)
```

The factory gets smarter with every build.

#### memory — Query factory memory

```python
wisdom = fm.get_factory_wisdom()
```

Present top successful patterns, top failure patterns, key lessons, and promoted skills.

#### dashboard — Full manufacturing overview

```python
dash = fm.dashboard()
```

Present pipeline status, factory wisdom, and capability registry in a structured summary.

### 3. Persist learnings

After significant operations, call `remember_fact` on the Fig platform:
- Product creation: `remember_fact(content="Product X is in the ForgeMaster pipeline at stage Y", scope="agent")`
- Build lessons: `remember_fact(content="Build #N: pattern P succeeded, lesson L learned", scope="agent")`

## Gotchas

- The stage gates use heuristic checks — some conditions (market fit, value proposition) always pass and require human judgment. Flag these to the user.
- Products must have their definition fields populated (api_specification, documentation, etc.) before they can advance past ARCHITECTURE.
- The CERTIFICATION stage gate expects Chronos Auditor verification — if the user hasn't run an audit yet, remind them.
- Factory memory is in-memory per session. For durable storage, serialize entries and store via `remember_fact`.
