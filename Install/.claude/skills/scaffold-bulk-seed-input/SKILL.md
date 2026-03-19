---
name: scaffold-bulk-seed-input
description: Seed all 5 input docs from the design doc. Phases are sequential: action-map informs bindings, which informs navigation.
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Seed Input Documents from Design Doc

Read the completed design doc and use it to pre-fill action-map, input-philosophy, keyboard/mouse bindings, gamepad bindings, and UI navigation.

## Prerequisites

1. **Read the design doc** at `scaffold/design/design-doc.md`.
2. **Read the interaction model** at `scaffold/design/interaction-model.md`. This is the Rank 2 canon document that defines how the player interacts with the game — action-map, bindings, and navigation all derive from it. If this file does not exist, stop and tell the user to create it first (e.g., via `/scaffold-new-design` or the interaction-model template).
3. **Read the engine input doc** at `scaffold/engine/godot4-input-system.md` for input routing, device handling, and pause behavior constraints.
4. **Read the document authority map** at `scaffold/doc-authority.md` for the influence relationships between input documents and their parent canon docs.
5. **Verify the design doc is sufficiently filled out.** The following sections must have content (not just TODO markers):
   - Player Verbs
   - Core Loop
   - Input Feel (if present)
6. If the design doc is too empty, stop and tell the user to run `/scaffold-new-design` first.

## Phase 1 — Seed Action Map

1. **Read** `scaffold/inputs/action-map.md`.
2. **Extract player verbs** from the design doc's Player Verbs, Core Loop, and Content Structure sections.
3. **Propose action IDs** with namespaces (`player_`, `ui_`, `camera_`, `debug_`).
4. **Present proposed actions** as a table for user confirmation.
5. **Write confirmed content** into the action-map, replacing TODO markers.

## Phase 2 — Seed Input Philosophy

1. **Read** `scaffold/inputs/input-philosophy.md`.
2. **Read advisory theory docs** for context:
   - `scaffold/theory/ux-heuristics.md` — accessibility principles
   - `scaffold/theory/game-design-principles.md` — agency and feedback
3. **Extract principles** from the design doc's Input Feel, Accessibility Philosophy, and Accessibility Targets sections.
4. **Propose input philosophy content:** principles, responsiveness targets, accessibility features, and constraints.
5. **Present proposed content** for each section to the user.
6. **Write confirmed content** into the input-philosophy, replacing TODO markers.

## Phase 3 — Seed KBM Bindings

1. **Read** `scaffold/inputs/default-bindings-kbm.md`.
2. **Read the action-map** (just seeded in Phase 1) for the full action list.
3. **Propose default keyboard/mouse bindings** for every action, grouped by namespace.
4. **Check for conflicts** — flag any duplicate key assignments.
5. **Present proposed bindings** as a table for user confirmation.
6. **Write confirmed content** into the bindings doc, replacing TODO markers.

## Phase 4 — Seed Gamepad Bindings

1. **Read** `scaffold/inputs/default-bindings-gamepad.md`.
2. **Read the action-map** (seeded in Phase 1) for the full action list.
3. **Propose default gamepad bindings** for every action, grouped by namespace.
4. **Check for conflicts** — flag any duplicate button assignments.
5. **Present proposed bindings** as a table for user confirmation.
6. **Write confirmed content** into the bindings doc, replacing TODO markers.

## Phase 5 — Seed UI Navigation

1. **Read** `scaffold/inputs/ui-navigation.md`.
2. **Read the action-map and ui-kit** for UI component and action context.
3. **Propose navigation model** (spatial, tab-order, or hybrid) based on game genre and input philosophy.
4. **Propose focus flow** for major screens based on UI kit components.
5. **Present proposed content** for each section to the user.
6. **Write confirmed content** into the navigation doc, replacing TODO markers.

## Phase 6 — Report

Summarize what was seeded:
- Number of actions registered in action-map
- Number of sections filled in each doc
- Number of sections left as TODO
- Remind the user of next steps:
  - Run `/scaffold-sync-glossary --scope input` to register new domain terms (action names, input concepts) in the glossary
  - Review each doc, then fill in remaining TODOs

## Rules

- **Never write content the user hasn't confirmed.** Always present the proposal first.
- **Phases are sequential.** Action-map informs bindings, which informs navigation. Do not skip ahead.
- **Be specific, not generic.** Proposed content should reference the actual game described in the design doc, not boilerplate.
- **If a section can't be derived**, say so and leave it as TODO. Don't force content where the design doc doesn't provide enough context.
- **Preserve any existing content.** If a section is already filled, skip it — don't overwrite.
- **Created documents start with Status: Draft.**
