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

## Conclusion

These are your own tooling artefacts: a set of agent skills, one Xcode project of
yours (twice, because the builder service hands back a copy), and three Apple /
Ollama downloads. No third party, no exfiltration path, no stolen work in this
batch.
