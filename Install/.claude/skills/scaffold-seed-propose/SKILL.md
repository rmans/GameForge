---
name: scaffold-seed-propose
description: "Propose candidate documents from one upstream requirement. Reads action.json with the requirement, project inventory, and existing candidates. Identifies dependencies. Writes result.json with proposed candidates."
argument-hint: (called by /scaffold-seed dispatcher — not user-invocable)
allowed-tools: Read, Write, Grep, Glob
---

# Propose Seed Candidates

This skill is called by the `/scaffold-seed` dispatcher. It receives one upstream requirement and proposes candidate documents to create.

## Input

Read `.reviews/seed/action.json`:

```json
{
  "action": "propose",
  "layer": "tasks",
  "requirement": {
    "source_file": "specs/SPEC-042-place-building_approved.md",
    "source_type": "spec",
    "content_summary": "... first 3000 chars of the spec ...",
    "extract_rule": "Each spec AC produces task steps"
  },
  "inventory": {
    "scaffold_docs": {"tasks": ["tasks/TASK-001-...", ...], "engine": ["engine/godot4-coding.md", ...]},
    "engine_config": {"godot4.project_file": true, "godot4.gdextension": false, "godot4.scons": false},
    "file_system": {"src": false, "game": true, "game/data/balance": true}
  },
  "existing_candidates": [...],
  "template": "scaffold/templates/task-template.md",
  "dependency_checks": [...],
  "is_gap_fill": false
}
```

## Process

1. **Read the upstream requirement** — understand what needs to be created from this source.

2. **Check what already exists** — look at `inventory` and `existing_candidates`. Don't propose duplicates.

3. **For each candidate you'd propose, check its dependencies:**
   - What does this candidate need to work? (engine features, other docs, infrastructure)
   - Check against `inventory.engine_config` and `inventory.file_system`
   - If a dependency is missing, **propose a prerequisite candidate** that creates it
   - Example: task needs C++ compilation → check `godot4.gdextension` → false → propose a "set up gdextension" foundation task first

4. **Propose candidates** with:
   - `proposed_id`: temporary ID (e.g., `task-place-building-impl`)
   - `name`: human-readable name
   - `type`: what kind of doc (task, spec, system, etc.)
   - `source`: what upstream requirement it fulfills
   - `depends_on`: list of proposed_ids this candidate needs (including prerequisites you just proposed)
   - `content_outline`: brief outline of what the doc will contain
   - `needs`: what this candidate requires from the project (for dependency tracking)

5. **Flag assumptions** — anything you can't verify from the inventory:
   - "Assumes balance CSV pattern is established" → check `game/data/balance` exists
   - "Assumes signal registry has construction_started" → can't verify from inventory alone

## Output

Write `.reviews/seed/result.json`:

```json
{
  "candidates": [
    {
      "proposed_id": "task-setup-gdextension",
      "name": "Set up GDExtension build pipeline",
      "type": "foundation",
      "source": "prerequisite — needed by task-place-building-impl",
      "depends_on": [],
      "content_outline": "Configure SConstruct, create src/ directory, set up compilation...",
      "needs": {"engine_config": "gdextension build system"}
    },
    {
      "proposed_id": "task-place-building-impl",
      "name": "Implement building placement",
      "type": "behavior",
      "source": "SPEC-042 AC-1, AC-2, AC-3",
      "depends_on": ["task-setup-gdextension"],
      "content_outline": "Steps: create BuildingSystem node, implement placement validation...",
      "needs": {"gdextension": true, "signal_registry": "construction_started"}
    }
  ],
  "assumptions": [
    {"assumption": "Signal registry has construction_started defined", "verifiable": false, "impact": "Task steps reference this signal"}
  ]
}
```

## Principles

- **One requirement at a time.** You receive one spec/system/phase. Focus on what it needs.
- **Create prerequisites, don't work around missing things.** If gdextension isn't set up, propose a task to set it up — don't rewrite the implementation to avoid C++.
- **Check the inventory.** Don't assume things exist. `engine_config.godot4.gdextension: false` means it's not configured.
- **Don't duplicate.** Check `existing_candidates` before proposing. If a prerequisite was already proposed by a previous requirement, reference it by proposed_id.
- **Flag what you can't verify.** If you need to know something the inventory doesn't cover, make it an explicit assumption.

## What NOT to Do

- **Don't create the files.** You're proposing candidates, not writing docs.
- **Don't read files beyond what's in action.json.** The content_summary and inventory are your context.
- **Don't propose more than needed.** One upstream requirement → the minimum set of candidates to fulfill it + prerequisites.
