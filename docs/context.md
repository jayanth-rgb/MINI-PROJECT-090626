# Project Context — Jayanth Trading Tiles System (Human Index)

> Companion to `.ases/context.json` · 2026-06-09

This file is the **human-readable entry point** to the project's ASES state. It is the same content as `.ases/context.md` but lives in `docs/` so PO can find it without digging into `.ases/`.

## Where to find what

| You want to see... | Read... |
|---|---|
| Project brief (objective, users, stack) | [`docs/brief.md`](brief.md) |
| Full PRD (12 features, 53 AC) | [`docs/prd.md`](prd.md) |
| HLD (modules, data flows, risks) | [`docs/hld.md`](hld.md) |
| LLD reference (tables, rules, formulas) | [`docs/lld_reference.md`](lld_reference.md) |
| Roadmap (3 sprints, gates) | [`docs/roadmap.md`](roadmap.md) |
| Architectural decisions (6 ADRs) | [`.ases/decisions.md`](../.ases/decisions.md) |
| Live state (sprint, phase, next step) | [`.ases/context.json`](../.ases/context.json) |
| Global memory (sprint history, etc.) | [`.ases/global_context.md`](../.ases/global_context.md) |

## Pipeline progress

```
✅ interview   → brief.json / brief.md
✅ prd         → prd.json / prd.md
✅ hld         → hld.json / hld.md
✅ roadmap     → roadmap.json / roadmap.md             ⚑ PO APPROVED
✅ init        → .ases/ scaffolded + folder tree
⏭  scaffold    → backend / frontend / Docker (next)
```

## Sprint stack
- **S1** (planned) — Data Foundation (F-001..F-006)
- **S2** (planned) — Transaction Forms + Stock Ledger (F-007..F-009)
- **S3** (planned) — Dashboard + Sales Report + Carry-Forward (F-010..F-012)
