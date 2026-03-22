# SPEC-### — [Spec Name]

> **Authority:** Rank 7
> **Layer:** Behavior
> **Conforms to:** [design/](../design/_index.md)
> **System:** SYS-### (link to parent system)
> **Secondary Systems:** — (SYS-### IDs if cross-system, or "—")
> **Triggered by:** <!-- What created this spec? Examples: bulk-seed-specs SLICE-###, triage-specs split from SPEC-###, manual creation for gap identified in iterate-slice, ADR-### new behavior required. -->
> **Created:** YYYY-MM-DD
> **Last Updated:** YYYY-MM-DD
> **Status:** Draft
> **Changelog:**

## Definition

### Summary

<!-- One sentence: what behavior this spec defines. -->

### Proof Intent

<!-- What this spec proves within its parent slice. Connects the spec to the slice's proof chain. -->
<!--
Examples:
- proves valid placement path
- proves rejection path
- proves BuildingSystem → RoomSystem propagation
- proves state transition from Hungry to Eating
-->

### Trigger

<!-- What causes this behavior to start — the initiating player action or system event. Makes ownership and causality explicit. -->

### Preconditions

<!-- What must be true before this behavior can occur. -->

## Behavior

### Steps

<!-- Step-by-step description of the behavior. Be precise and testable. Each step describes one observable action or result. -->

### Observable Outcome

<!-- What can be observed when the behavior succeeds. Player-visible or test-observable results — not internal state. -->

### Failure Outcome

<!-- What happens when the behavior is rejected or fails. The expected visible failure behavior. -->

### Postconditions

<!-- What must be true after this behavior completes. -->

## Boundaries

### Edge Cases

<!-- Unusual inputs, boundary conditions, error states. -->

### Secondary Effects

<!-- Follow-on effects in other systems triggered by this behavior. Cross-system propagation, UI refreshes, path recalculations, etc. -->

### Out of Scope

<!-- What this spec intentionally does not cover. Prevents spec creep and duplicate overlap. -->

## Verification

### Acceptance Criteria

<!-- How to verify this spec is correctly implemented. Concrete pass/fail checks. -->

### Asset Requirements

<!-- What art and audio assets does this behavior need? List what's required, not how to produce it. Asset production happens via art/audio skills; tasks wire the results.

Scan existing `assets/` directories for reusable assets before listing something as Needed. A single base asset (mesh, sprite, sound) can satisfy multiple requirements through variants (color, overlay, pitch shift).

| Requirement | Type | Description | Source Section | Satisfied By | Status |
|-------------|------|-------------|---------------|-------------|--------|

Type: Sprite, Mesh, Icon, UI Mockup, Concept Art, SFX, Music, Ambience, Voice
Status: Needed (must be produced), In Production (art/audio skill running), Ready (exists or reusable)
Satisfied By: path to existing asset if reusable, or "—" if Needed

If no assets are required, write "No art or audio assets required for this behavior." -->

## Notes

<!-- ADR constraints, KI references, design debt, or other context. -->
