---
name: scaffold-playtest
description: "Log and review playtest sessions. Replaces scaffold-playtest-log and scaffold-playtest-review."
argument-hint: "<log|review> [session-date]"
allowed-tools: Read, Write, Edit, Grep, Glob
user-invocable: true
---

# Playtest — Log and Review

Log or review playtest sessions: **$ARGUMENTS**

## Commands

| Command | What it does |
|---------|-------------|
| `log` | Create a new playtest session log (PT-YYYY-MM-DD) with observations, metrics, summary |
| `review` | Review existing playtest feedback entries, promote observations to patterns, file KIs/ADRs |

## Usage

```
/scaffold-playtest log                 ← start a new playtest session
/scaffold-playtest review              ← review all open feedback entries
/scaffold-playtest review PT-2026-03-22 ← review a specific session
```

## Log Process

1. Create `decisions/playtest-feedback/PT-YYYY-MM-DD.md` from template
2. Interview: focus area, testers, hypothesis
3. Log observations as they happen
4. Post-test questions
5. Summary with surprises
6. Create PF-### entries for significant observations

## Review Process

1. Read open PF-### entries
2. For each: is this a one-off or a pattern?
3. Promote patterns: file KI, ADR, or design doc update
4. Update PF status: Open → Pattern → Resolved
