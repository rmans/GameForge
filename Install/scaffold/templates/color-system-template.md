# Color System

> **Authority:** Rank 2
> **Layer:** Canon
> **Conforms to:** [design-doc.md](design-doc.md), [style-guide.md](style-guide.md)
> **Created:** YYYY-MM-DD
> **Last Updated:** YYYY-MM-DD
> **Status:** Draft
> **Changelog:**
> - YYYY-MM-DD: Initial creation from template.

This document defines **the game's color language** — palette, semantic tokens, usage rules, and accessibility constraints. Every color choice in the game traces back to this doc.

<!-- This doc derives from style-guide.md (mood, tone registers, visual identity) and state-transitions.md (entity states that need color mapping). UI-kit.md and all art/UI implementation reference this doc for color consistency. -->

---

## Palette

<!-- Define the core color palette. Group by purpose, not by hue. Reference the style-guide's tone registers — each register may shift the palette. -->

### Base Palette

<!-- The default colors when the game is in its baseline tone. Background colors, surface colors, text colors, border colors. These define the "normal" look of the game. -->

### Signal Palette

<!-- Colors that communicate system state: health (green → yellow → red), resources (plentiful → scarce), alerts (info → warning → critical). Derive from state-transitions.md entity states. -->

### Identity Palette

<!-- Colors that identify factions, teams, zones, entity types, or other categorical distinctions. Reference the design doc for what categories need visual distinction. -->

---

## Color Tokens

<!-- Semantic color tokens that decouple meaning from specific hex values. UI and art reference tokens, not raw colors. -->

### State Tokens

<!-- Map entity/system states to colors. Examples: `healthy` → green, `injured` → yellow, `critical` → red, `dead` → grey. Derive from state-transitions.md. -->

| Token | State | Hex | Usage |
|-------|-------|-----|-------|
| <!-- token name --> | <!-- entity/system state --> | <!-- #RRGGBB --> | <!-- where this color appears --> |

### UI Tokens

<!-- Tokens for UI components. Examples: `primary`, `secondary`, `accent`, `background`, `surface`, `text`, `text-muted`, `border`, `hover`, `pressed`, `disabled`, `error`, `success`, `warning`, `info`. -->

| Token | Hex | Usage |
|-------|-----|-------|
| <!-- token name --> | <!-- #RRGGBB --> | <!-- where this color appears --> |

---

## Usage Rules

<!-- Rules that govern how colors are used across the game. These prevent color chaos and maintain readability. -->

<!-- Examples:
- No more than N accent colors on screen simultaneously
- Signal colors are reserved — never use red for decoration
- Text must meet WCAG contrast ratios against its background
- Color must never be the ONLY way to convey information (accessibility)
-->

---

## UI vs World Colors

<!-- How do UI colors relate to world/game colors? Does the UI overlay have its own palette separate from the game world? Do UI elements use world colors or abstracted tokens? Reference the style-guide's rendering approach. -->

---

## Accessibility

<!-- Color accessibility rules. Reference the design doc's Accessibility Philosophy. -->

<!-- Consider:
- WCAG contrast ratio targets (AA = 4.5:1 text, 3:1 large text; AAA = 7:1)
- Color-blind safe palette (test against protanopia, deuteranopia, tritanopia)
- Redundant encoding (shape + color, pattern + color, icon + color)
- High-contrast mode variant if needed
-->

---

## Theme Variants

<!-- Does the game have multiple visual themes? Factions with distinct palettes? Biomes with different color temperatures? Escalation states that shift the whole palette? Day/night cycles? -->

<!-- For each variant, define which tokens shift and how. Reference the style-guide's tone registers for escalation-driven shifts. -->

---

## Rules

1. All color usage in the game traces back to tokens defined here. Raw hex values in implementation must reference a token.
2. Signal colors (health, danger, alert) are reserved — never used decoratively.
3. Accessibility constraints are non-negotiable. Color is never the sole channel for gameplay information.
4. Tone register shifts (from style-guide.md) may adjust palette temperature and saturation, but never break token semantics.
