# Style Guide

> **Authority:** Rank 2
> **Layer:** Canon
> **Conforms to:** [design-doc.md](design-doc.md)
> **Created:** YYYY-MM-DD
> **Last Updated:** YYYY-MM-DD
> **Status:** Draft
> **Changelog:**
> - YYYY-MM-DD: Initial creation from template.

This document defines **what the game looks like** — the visual identity, rendering style, animation language, and iconography rules that govern all visual output. It is engine-agnostic and describes intent, not implementation.

<!-- This doc is the visual foundation. Color-system.md derives its palette from the mood and tone defined here. UI-kit.md derives component style from the rendering approach and animation rules here. All art skills read this doc for consistency. -->

---

## Art Direction

<!-- What is the overall visual style? Reference the design doc's Aesthetic Pillars and Genre & Reference Points. Is it pixel art, hand-painted, low-poly, realistic, cel-shaded? What visual references capture the target look? -->

### Aesthetic Pillars

<!-- List the 3-5 core visual principles. Examples: "readable at a glance," "warm but not cheerful," "clinical precision," "organic decay." These should trace directly to the design doc's aesthetic pillars. -->

### Reference Points

<!-- Visual references — games, films, art styles, artists. Be specific: "Rimworld's clean icon language" not just "Rimworld." What exactly are you taking from each reference? -->

---

## Visual Tone

<!-- How does the visual presentation shift with game state? Define 2-4 tone registers that the game moves between. These registers drive color shifts, lighting changes, animation pacing, and audio mood. -->

### Tone Registers

<!-- Example registers: Baseline (calm, productive), Tension (something is wrong), Crisis (active emergency), Recovery (returning to normal). Define what each looks and feels like visually. -->

### Mood Communication

<!-- How does the game communicate mood visually without explicit UI? Lighting shifts? Color temperature? Particle density? Animation speed? Post-processing? -->

---

## Rendering Approach

<!-- 2D or 3D? Top-down, isometric, side-view? Sprite-based or model-based? What's the camera perspective? How does this affect readability and information density? Reference the design doc's Camera/Perspective section. -->

### Resolution & Scale

<!-- What's the target art resolution? Pixel density? Entity size relative to screen? Zoom range? How do these choices support readability? -->

---

## Character & Entity Style

<!-- What do the game's entities look like? How are different entity types visually distinguished? Reference the design doc's entity descriptions and system designs for what entities exist. -->

### Entity Visual Hierarchy

<!-- How does the player tell entities apart at a glance? Size? Color? Shape language? Silhouette? What visual features communicate entity state (healthy, injured, working, idle)? -->

### Character Proportions

<!-- If the game has characters: proportions, level of detail, how expression/emotion is communicated at the game's camera distance. -->

---

## Environment Style

<!-- What does the game world look like? Reference the design doc's Place & Time and Rules of the World sections. How do biomes, regions, or areas differ visually? -->

### Terrain & Surface

<!-- Ground tiles, terrain types, how different surfaces read at zoom distance. -->

### Structures & Objects

<!-- Built structures, natural objects, interactable items. How are player-built things visually distinct from natural environment? -->

---

## VFX & Particles

<!-- What visual effects exist? Construction sparkles, damage indicators, weather, fire, status auras? When are particles used vs sprite animations vs shader effects? Keep it light — detailed VFX specs belong in engine docs. -->

---

## Animation Style

<!-- What's the motion language? Snappy and responsive, or slow and weighty? How does animation timing relate to game feel? Reference the design doc's Input Feel and Aesthetic Pillars. -->

### Motion Principles

<!-- 3-5 rules for how things move. Examples: "UI transitions are fast (< 200ms)," "entity movement uses easing, never linear," "combat animations prioritize readability over flair." -->

### Feedback Animations

<!-- How do interactive elements respond to player input? Hover, press, select, drag. Keep this brief — detailed feedback coordination is in feedback-system.md. -->

---

## Iconography Style

<!-- How are icons designed? What style rules ensure icons are readable at the game's camera distance and UI scale? Reference the design doc's Player Information Model for what must be visible at a glance. -->

### Icon Design Rules

<!-- Size constraints, color usage, outline rules, state variants (normal, disabled, active, alert). -->

### Icon Categories

<!-- What types of icons does the game need? Resource icons, entity icons, action icons, status icons, alert icons? -->

---

## Rules

1. All visual output must conform to this style guide. Engine docs and art skills reference this doc for style consistency.
2. Tone registers defined here drive color-system.md palette shifts and audio-direction.md mood changes.
3. This doc describes visual intent, not engine implementation. Node hierarchies, shader code, and rendering pipelines belong in engine docs.
4. When this doc conflicts with engine constraints, file an ADR — do not silently deviate.
