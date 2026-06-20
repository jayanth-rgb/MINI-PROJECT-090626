# Global Context — Jayanth Trading Tiles System

> Auto-generated companion to `.ases/global_context.json` · last update 2026-06-20

This is the project's **long-memory** store. Entries here are loaded only by explicit `/ases-inject [IDs]` — never injected automatically into a session.

| Prefix | Type | Created by |
|---|---|---|
| `SP-NNN` | Sprint summary | `/ases-sprint-close` |
| `DS-NNN` | Architectural decision | `/ases-hld`, `/ases-lld` |
| `TD-NNN` | Tech debt | `/ases-critique`, `/ases-final-audit` |
| `FT-NNN` | Feature delivered | `/ases-release` |
| `RI-NNN` | Risk identified | `/ases-hld`, `/ases-final-audit` |
| `CF-NNN` | Carry-forward item | `/ases-sprint-close`, `/ases-release` |

Query without injecting: `/ases-gc [ID|type|tag]`
Inject into session: `/ases-inject [ID...]` or `/ases-inject tags:M-001,performance`

## Entries (13)

### Sprint Digests
- **SP-001** — Sprint S1 shipped (2026-06-20). Final audit verdict SHIP. 40/40 tasks complete; 46/46 TCs pass; 19/19 UAT ACs accepted.

### Features Delivered
- **FT-001** F-001 Supplier Master (AC-001..AC-003)
- **FT-002** F-002 Staff Master (AC-004..AC-006)
- **FT-003** F-003 Dealer Master (AC-007..AC-009)
- **FT-004** F-004 Grade Master with UNIQUE(grade_code) (AC-010..AC-012)
- **FT-005** F-005 Trading Design Master (AC-013..AC-015)
- **FT-006** F-006 Design-Grade Mapping — DF-006 contract delivered (AC-016..AC-019)

### Tech Debt
- **TD-005** (minor, S1, closes on W5) — Migration 0002 hand-authored from ORM
- **TD-006** (minor, S1, closes on W5) — Seed runtime verification deferred until W5
- **TD-007** (minor, S2) — TIMESTAMP → TIMESTAMPTZ in TimestampMixin

### Carry-Forward
- **CF-001** — W5: PO completes long-lived PG bring-up (`.env` + docker-compose + alembic upgrade head + seed). Closes TD-005 and TD-006.

### Risks
- **RI-001** (low) — TIMESTAMP vs TIMESTAMPTZ drift between ORM and LLD prose (mitigated by TD-007)
- **RI-002** (low) — Long-lived PG dev environment not yet bootstrapped (mitigated by CF-001)

### Architectural Decisions (DS-001..DS-012)
DS entries live in `.ases/decisions.json` rather than here (created by `/ases-hld` and `/ases-lld`). See that file for the 12 architectural decisions made before sprint execution.
