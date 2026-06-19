---
description: Show full ASES project context — global history, decisions, sprint history
allowed-tools: Read
---
Read `.ases/global_context.json`, `.ases/decisions.json`, `.ases/context.json`.

Display with sections:
1. **Project State** — from context.json
2. **Sprint History** — SP-NNN entries from global_context (most recent first)
3. **Active Decisions** — DS-NNN entries where status=active
4. **Open Tech Debt** — TD-NNN entries where status=open
5. **Open Risks** — RI-NNN entries where status=open or monitoring

Format each entry with its ID prominently — PO needs to reference these in /ases-inject calls.
