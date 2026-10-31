---
name: build-blueprint
description: Natural-language front door into the Meta Software Factory. Turns a
  single sentence into a governed, executable build plan with architecture,
  tasks, risk assessment, and ecosystem dispatch to Pocket O
triggers:
  - build blueprint
  - compile a plan
  - create a build plan
  - blueprint this
  - turn this into a plan
  - generate a project plan
---

## When to use

The user says something like "Build a memory engine," "Create a FastAPI auth service," or "Add OAuth to Pocket OS." This skill compiles that sentence through a 5-stage pipeline and returns a complete, governed implementation plan ready for ecosystem dispatch.

## Pipeline

```
User Prompt → Intent Parser → Architecture Planner → Dependency Analyzer
           → Task Generator → Governance Review → Ecosystem Dispatch
```

## Steps

### 1. Import the engine

```python
import sys
sys.path.insert(0, '<workspace_root>/scripts/')

from build_blueprint.engine import compile
```

### 2. Compile a prompt

```python
blueprint = compile("Build a memory engine.")
```

Returns a dict with:

- `project_name` — extracted from the prompt
- `architecture` — stack, pattern, components with dependency edges, Mermaid diagram
- `tasks` — concrete implementation tasks mapped to subsystems (dreamweaver, ralph5, igor_os, pocket_os)
- `estimated_total_minutes` / `estimated_total_hours`
- `risk_level` — low, medium, high, or critical
- `governance` — pending_approval, approved, rejected, or needs_review
- `ecosystem_actions` — dispatch payloads for Pocket OS, Manus Prime, Ralph5, Igor OS, and SynapseLedger

### 3. Present the blueprint

Show the user:
- Architecture diagram (Mermaid)
- Task breakdown by subsystem
- Risk level and governance status
- Estimated time
- Ecosystem dispatch targets

### 4. Dispatch (when the user approves)

For each `ecosystem_actions` entry, route to the appropriate subsystem:

- `pocket_os` → `remember_fact` for project context
- `manus_prime` → invoke `/manus-prime` with the goal
- `ralph5` → use `write_file`, `shell`, `edit_file` for implementation
- `igor_os` → use `shell`, `publish_project`, `create_scheduled_task`
- `synapse_ledger` → `remember_fact` with `scope="entity"` for immutable event recording

## Supported prompt types

The intent parser recognizes these categories and maps them to appropriate stacks:

| Keywords | Stack | Components |
|---|---|---|
| memory engine, knowledge graph, neo4j, vector store | FastAPI, Neo4j, PostgreSQL, Redis, Qdrant | api, graph-store, vector-index, cache-layer, worker, admin-ui |
| auth, oauth, login, sso, jwt | FastAPI, PostgreSQL, Redis, SendGrid | auth-api, user-db, session-store, email-service, admin-ui |
| dashboard, ui, swiftui, ios, react | React, TypeScript, Tailwind CSS, Vite | web-ui, api-gateway, component-library |
| api, backend, fastapi, service, rest | FastAPI, PostgreSQL, Redis, Docker | api, database, cache, worker |
| cli, command line, terminal | Python, Click, Rich | cli, core-lib, config |
| database, schema, postgres, migration | PostgreSQL, Alembic, SQLAlchemy | models, migrations, seed-data |

## Governance rules

- Auth/payment/PII keywords → HIGH risk, NEEDS_REVIEW
- Deploy/migration/refactor keywords → MEDIUM risk, PENDING
- Destructive operations (drop, purge, destroy) → CRITICAL, NEEDS_REVIEW
- Everything else → LOW risk, PENDING

## Gotchas

- The intent parser is keyword-driven. For prompts that don't match any category, it defaults to the API/backend stack.
- Project name extraction uses regex — very short or unusual prompts may produce odd names. The user can override.
- The engine is deterministic (no LLM call). For ambiguous prompts, ask the user to clarify before compiling.
- `scripts/build_blueprint/engine.py` is the canonical engine. It ships bundled with this skill.
