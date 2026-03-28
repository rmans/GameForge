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
  "existing_candidates": [{"proposed_id": "...", "name": "...", "domain": "...", "source": "...", "type": "...", "owns": "..."}],
  "template": "scaffold/templates/task-template.md",
  "dependency_checks": [...],
  "is_gap_fill": false
}
```

## Process

1. **Read the upstream requirement** — understand what needs to be created from this source.

2. **Check what already exists** — look at `inventory` and `existing_candidates`. Don't propose duplicates.

3. **If `propose_rules` is present in action.json, follow it.** Layer-specific derivation rules override the default generic process. See the Systems Layer section below for the most important example.

4. **For each candidate you'd propose, check its dependencies:**
   - What does this candidate need to work? (engine features, other docs, infrastructure)
   - Check against `inventory.engine_config` and `inventory.file_system`
   - If a dependency is missing, **propose a prerequisite candidate** that creates it
   - Example: task needs C++ compilation → check `godot4.gdextension` → false → propose a "set up gdextension" foundation task first

5. **Propose candidates** with:
   - `proposed_id`: temporary ID (e.g., `task-place-building-impl`)
   - `name`: human-readable name
   - `type`: what kind of doc (task, spec, system, etc.)
   - `source`: what upstream requirement it fulfills
   - `depends_on`: list of proposed_ids this candidate needs (including prerequisites you just proposed)
   - `content_outline`: brief outline of what the doc will contain
   - `needs`: what this candidate requires from the project (for dependency tracking)
   - `domain` (systems layer only): organizational grouping label

6. **Flag assumptions** — anything you can't verify from the inventory:
   - "Assumes balance CSV pattern is established" → check `game/data/balance` exists
   - "Assumes signal registry has construction_started" → can't verify from inventory alone

---

## Systems Layer — Derivation Rules

When `layer` is `systems`, the upstream requirement is the design doc itself. The design doc contains everything needed to derive the correct system set — but you must extract systems methodically, not by latching onto random sections.

### System Derivation Order (MANDATORY)

Follow `propose_rules.derivation_order` from action.json. The standard order is:

**Priority 1 — Core Loop → extract required systems.**
Read the Core Loop section. But NOT every loop step becomes a system. A loop step only generates a system if it represents a **persistent gameplay domain with its own state and mechanics**. Cognitive phases like "assess situation" or "watch outcomes" are NOT systems — they are player activities served BY systems. Extract the underlying domains that make each step possible. Example: "Scan → Assess → Adjust → Watch" does NOT produce four systems. It implies the persistent domains underneath: Task System (what gets adjusted), Information/Alert System (what makes scanning possible), etc.

**Priority 2 — Secondary Loops → extract supporting systems.**
Read the Secondary Loops section. Each longer cycle implies supporting systems. If a secondary loop is already covered by a Tier 1 system, note the coverage rather than duplicating. Example: "Expedition Arc" → Expedition System. "Maintenance Cycle" → Containment System.

**Priority 3 — Simulation Requirements → extract simulation systems.**
Read the Simulation Requirements section (State That Matters, Behaviors That Need Rules, Player Actions That Need Governance), Content Categories, and narrative context. Identify major state domains — things the player can observe or that drive gameplay decisions. Each distinct state domain needs a simulation system. Example: Power, Instability, Colonist Needs, Containment, Resources.

**Priority 4 — Player Verbs → extract control systems.**
Read the Player Verbs section. **Multiple verbs that operate on the same domain must be grouped into a single system.** Example: "assign", "prioritize", "queue", "cancel" are all Task System verbs — NOT four separate systems. A verb generates a NEW system only if no existing candidate from priorities 1-3 covers its domain. Example: "Build" → Construction System (new). "Zone" → Zone System (new). "Assign" → already covered by Task System (note coverage).

**Priority 5 — Merge Pass.**
Review all candidates so far. If two or more candidates share the same player-facing purpose, merge them. Be aggressive — over-splitting creates garbage output. Example: "Work System" + "Task Assignment System" + "Job System" → one Task System.

**Priority 6 — Validation Pass.**
Every surviving candidate must pass this test:

> "The player engages with this system when ___, and if ignored ___ happens."

If a candidate cannot fill both blanks with concrete, player-visible answers, reject it.

### System Ownership (MANDATORY)

Follow `propose_rules.ownership_rules` from action.json. Each candidate MUST declare:

- **`owns`** — What state this system controls (e.g., "colonist work assignments, task queue, task priorities")
- **`consumes`** — What it reads from other systems (e.g., "colonist skills from Colonist System, room availability from Room System")
- **`produces`** — What signals/events it outputs (e.g., "task_completed, task_failed, colonist_idle")

If two candidates own the same state, they must be merged or the contested state must be assigned to one owner. These declarations feed directly into `authority.md` and `interfaces.md` during the references seeding step.

### System Boundary Rules

Follow `propose_rules.boundary_rules` and `propose_rules.kill_rules` from action.json. The core principles:

- **A system must represent a player-facing behavior domain, not a technical concern.** Reject "Pathfinding System", "Save System", "UI System", "Rendering System" — unless the design doc explicitly defines them as gameplay systems the player interacts with.
- **Systems describe WHAT happens in the game world, not HOW the engine implements it.** This is Rule 5 from CLAUDE.md.
- **Kill weak systems.** Reject a system if it has no persistent state, exists only for UI convenience, or cannot produce or react to gameplay consequences.

### Scale Target

A well-derived system set for a typical game has **12-25 systems**. Fewer than 8 likely means under-coverage. More than 30 likely means over-splitting or inclusion of technical concerns. Use `propose_rules.scale_target` from action.json as guidance.

### Domain Grouping

Organize proposed systems into domains (e.g., "Colonist Domain", "Facility Domain", "Resource Domain"). Domains are NOT systems — they are organizational labels. Include a `domain` field in each candidate for grouping.

### What the Output Should Look Like

For a colony management game, a correct first pass looks like:

```
Simulation Core
  - Time System
  - Event / Alert System
  - Instability System
Colonist Domain
  - Colonist State System
  - Needs / Stress System
  - Task / Work System
Facility Domain
  - Construction System
  - Power System
  - Containment System
Resource Domain
  - Inventory System
  - Logistics System
Risk Domain
  - Hazard System
  - Weather System
Progression Domain
  - Expedition System
  - Funding System
```

That is ~15 systems. Not 50. Not 8. The right scale.

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
