# Global Context — Jayanth Trading Tiles System

> Auto-generated companion to `.ases/global_context.json` · 2026-06-09

This is the project's **long-memory** store. Entries here are loaded only by explicit `/ases-inject [IDs]` — never injected automatically into a session.

| Prefix | Type | Created by |
|---|---|---|
| `SP-NNN` | Sprint summary | `/ases-sprint-close` |
| `DS-NNN` | Architectural decision | `/ases-hld`, `/ases-lld` |
| `TD-NNN` | Tech debt | `/ases-critique`, `/ases-final-audit` |
| `FT-NNN` | Feature delivered | `/ases-release` |
| `RI-NNN` | Risk identified | `/ases-hld`, `/ases-final-audit` |
| `CF-NNN` | Carry-forward item | `/ases-sprint-close`, `/ases-release` |

**Currently empty** — populated as sprints complete.

Query without injecting: `/ases-gc [ID|type|tag]`
Inject into session: `/ases-inject [ID...]` or `/ases-inject tags:M-001,performance`
