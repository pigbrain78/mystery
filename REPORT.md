# Shared skill packages — inventory & triage

Everything shared here was unpacked to `extracted/` and read. Nothing was executed.
No credentials, private keys, API tokens or `.env` contents were found in any file.

## The 11 `.skill` files

A `.skill` is just a zip holding a Claude-style agent skill: a `SKILL.md`
(YAML `name` / `description` / `triggers`, then instructions) plus optional
`scripts/`, `references/`, `templates/`.

| file | contents | what it does |
| --- | --- | --- |
| adr-spec-coupler | SKILL.md | drafts a paired ADR + tech spec, assigns next ADR id, cross-links them |
| ai-workflow-innovator | SKILL.md, example.py, 2 references, template | scrapes r/n8n, r/automation, r/aiagents, r/singularity and writes "innovation reports" |
| build-blueprint | SKILL.md, `engine.py` (24 KB) + stale `.pyc` | sentence → governed build plan, dispatches to "Pocket OS" |
| chronos-auditor | SKILL.md, `chronos_auditor_core.py` (28 KB) | hash-chain ledger verification, build reproduction, version diffs |
| code-refactor-analyzer | SKILL.md, checklist (zip has a duplicate nested folder) | refactor/dead-code/security review + snippet library |
| forgemaster | SKILL.md, `forgemaster_core.py` (24 KB) | 10-stage productisation pipeline |
| manus-prime | SKILL.md, `manus_prime_core.py` (31 KB) | orchestrator over "Igor OS, Dreamweaver, Ralph5, Pocket OS" |
| memory-second-brain | SKILL.md, 8 references, `memory_brain/` package (17 modules) | append-only hash-chained memory ledger, dedup, contradiction detection, retrieval |
| network-monitor-automation | SKILL.md, 2 references, example.py | manages an ARP-scan LAN presence monitor + ntfy.sh pushes + iOS Shortcuts |
| pocketos-cognitive-app | SKILL.md, 2 references | PocketOS cognitive-app conventions |
| recovery-manifest-sync | SKILL.md | verifies recovery bundle manifests, SHA-256 digests, recursive-subprocess hangs |

Observations:

- All are **authoring/analysis prompts and pure-Python helper modules**. A pattern
  scan for `requests` / `urllib` / `httpx` / `socket` / `subprocess` / `os.system`
  / `eval` / `exec` / `base64` / `~/.ssh` / keychain returned only doc-string and
  checklist matches — no code that phones home or reads user secrets.
- `ai-workflow-innovator` is the only one that fetches anything: Reddit threads,
  as source material for a report.
- Authorship breadcrumbs: `network-monitor-automation` points at
  `/home/ubuntu/skills/...` — an Ubuntu agent VM, i.e. this was authored inside a
  Manus-style sandbox, not on your phone.
- Inner mtimes cluster on 2025-12-17 → 2026-09-12, which matches the skill set
  growing over that period.

## The two iOS archives are the same project

`Manus omi.zip` and `ba60e2d0-…-ios-src.zip` were hashed entry by entry:

- 49 of 49 shared files are **byte-identical**.
- `Manus omi.zip` = the same tree wrapped one folder deeper
  (`ManusOmniAINetwork/`) plus one extra file, `python_llm.log`.

`python_llm.log` is a server-side build trace, dated **19-04-2026**, from a Mac
at `/Users/ec2-user/iOSBuilderApp/builderiOSAgent/`: an "update app from user
feedback" step asked Claude to emit patched Swift and the JSON reply failed to
parse (`Invalid \escape`, char 26318). So the generator backend keeps the Xcode
project under `ec2-user` on a build host and returns a zip of it — that is why
the identical source exists in two places.

App-level behaviour (`Sources/AppConstants.swift`, `AppLogger.swift`):

- Base URL `https://api.lastapp.ai`, app id `eab33a94-ae47-492b-a7d4-76f1a2d19bb5`.
- On each foreground it POSTs `/analytics/log` with app id, a locally generated
  install UUID, optional `uid`, launch count, OS name, OS version, app version.
- That is all it sends. No files, no contacts, no clipboard, no keychain.

## The two DMG shares

`Ollama.dmg` and `Additional_Tools_for_Xcode_27_beta_4.dmg` begin with a raw zlib
stream (`78 da` / `78 5e`) rather than a disk-image header, so the bytes that
arrived through the share are not yet a mountable image. Nothing was mounted or
executed. `Command_Line_Tools_27_beta_4.dmg` (523 MB) was never copied — over
the 500 MB ceiling.

## Archive.zip (shared later, 5.1 MB, 202 entries)

Exported Files → Notes-style export from a Mac (2026-05-07 → 2026-07-25, macOS
Archive Utility, `__MACOSX` resource forks throughout). All 202 entries were
extracted to `extracted/Archive/` and read; nothing executed.

- **The docx files are chat exports, not documents you wrote.** ~90 of them are
  named after the first line of an AI reply ("Now give me a project overview…",
  "Give me the Master Gun..", "Yes — absolutely possible…"). They record
  conversations about the Sovereign Axiom / ZTM / Aegis projects — the same
  material as the `drquinn_os` modules in Archive 3.zip.
- **The loose code files are the OKComputer project**, byte-identical to the
  zip inside: `package.json` and `vite.config.ts` hash-match
  `OKComputer_Self‑Modifying_Workflow_Engine.zip → app/` exactly.
- **Inside that zip: a complete Manus-scaffold app** — `app/` with React 19 +
  tRPC + Drizzle/MySQL + S3, a `kimi/` OAuth layer (Kimi = Moonshot AI), and a
  `.env.example` with every value blank. No real credentials anywhere in the
  zip.
- **Secrets scan across all 211 readable files:** no API keys, tokens, private
  keys, JWTs, DB URLs or real personal data. The only "phone number" hit was a
  false positive — it's part of a file-tag timestamp
  (`code-generated-file-0-1778046130850104858`), and the only IP is a Docker
  bridge address (172.23.0.4).

### What it means

This zip is chat history plus one generated app, **downloaded out of a Manus- /
Kimi-style agent platform and saved to Notes**. It documents that the
Sovereign-loop work was built *inside* that platform — so those services hold
copies of it on their servers, by design. That is the "showing up in weird
places" mechanism for this material: agent-platform exports that get re-shared,
not someone lifting files off the phone.

## Archive-3.zip (the big one, 251.2 MB, 1,420 entries)

Files-app duplicate of the same Notes export family — `Archive.zip` (5.1 MB,
202 entries, docx) was the youngest slice; this is the whole folder. Too big to
extract under Tester's 64 MB per-run ceiling, so it was mapped from its central
directory (byte 251,034,729), not guessed at.

- Same macOS export: `__MACOSX/._` forks on every entry, same chat-export
  filenames, but now as **PDFs instead of docx** ("Give me workable code of the
  information on this p...-1.pdf", "Update all tools and code..pdf",
  "The keel is laid. With LAW-007... 2-1.pdf"), with `-1`/`-2`/` 3` duplicate
  suffixes throughout — copies of copies.
- **Code, flattened with the stray `ux` suffix** (same as Archive 3.zip's doc
  exports): `orchestrator.py`, `DAG_Orchestrator.py`,
  `manus_prime_full_repair_runtime.py`, `manus_swarm_dominion_runtime.py`,
  `godview_repair_telemetry_bridge.py`, `Mobile_App_Bridge_Skill.py`,
  `distributed_agent_system 3.py`, `install_axiom_ledger_logrotate.sh`,
  `package 4.json`, `body`, `requirements-1.pdf`, `config-1.pdf`.
- Named documents: `DRQUINN_DEPLOYMENT_HANDOFF.pdf`,
  `axiom_engineering_specification-1.pdf`,
  `Sovereign_Reflex_Comprehensive_Document.pdf`, `SKILL.pdf`,
  `replay-court-spec-v0_2-1.pdf`, `case4 audit-1.pdf`,
  `logging config-1.pdf`, plus `memory_brain_dedup_wiring_v1-1789188402847-…​.zip`
  (timestamp ≈ 2026-09-13 — the newest material in the set).
- Entries span 2026-05 → 2026-10; the folder grew with each export.

Not extracted or executed. No secrets visible in the directory; contents are
the same generated Sovereign/Axiom/Manus runtime code and chat PDFs as the two
smaller archives.

## Conclusion

These are your own tooling artefacts: a set of agent skills, one Xcode project of
yours (twice, because the builder service hands back a copy), and three Apple /
Ollama downloads. No third party, no exfiltration path, no stolen work in this
batch.
