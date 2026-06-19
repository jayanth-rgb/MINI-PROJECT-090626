---
description: Query the global context by ID, type, or tag — without injecting into session
allowed-tools: Read
argument-hint: "[ID | type:X | tags:X,Y | list]"
---
Read `.ases/global_context.json`.

Modes:
- `list` — show all entry IDs with one-line summaries
- `DS-003` — show full entry for that ID
- `type:decision` — list all decisions
- `tags:M-001,performance` — list all entries matching ALL tags

Format output clearly with IDs prominent. Remind PO they can use /ases-inject [IDs] to inject entries.
