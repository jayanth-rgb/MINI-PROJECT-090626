---
description: Show current ASES pipeline status — phase, sprint, last step, next step, blockers
allowed-tools: Read
---
Read `.ases/context.json` and `.ases/sprint_context.json` (if exists).

Show a clean terminal status report:
1. Project + current sprint + phase + stage
2. Last completed step → next recommended command
3. Task progress (complete/total) if in sprint execution
4. Any blockers
5. Context window bracket if available

Keep it under 20 lines. No preamble.
