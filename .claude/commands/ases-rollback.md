---
description: Restore a task to its pre-dev snapshot state
allowed-tools: Read, Write
argument-hint: "[task-id] [sprint-id]"
---
TASK_ID = first argument, SPRINT_ID = second argument.

1. Read `sprints/$SPRINT_ID/execution/snapshots/$TASK_ID-pre.json`
2. Show PO exactly which files will be restored and their previous hashes
3. Wait for explicit confirmation: "yes" or "confirm"
4. Restore files to pre-dev state from snapshot
5. Update `sprints/$SPRINT_ID/execution/tasks.json` task status → `pending`, iteration_count → 0
6. Append to `.ases/.audit.log`: `[ROLLBACK] {timestamp} Task $TASK_ID rolled back by PO`
