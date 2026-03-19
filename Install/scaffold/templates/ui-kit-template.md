# UI Kit

> **Authority:** Rank 2
> **Layer:** Canon
> **Conforms to:** [design-doc.md](design-doc.md), [style-guide.md](style-guide.md), [color-system.md](color-system.md)
> **Created:** YYYY-MM-DD
> **Last Updated:** YYYY-MM-DD
> **Status:** Draft
> **Changelog:**
> - YYYY-MM-DD: Initial creation from template.

This document defines **UI components, their states, composition patterns, and layout conventions** at the component level. It governs all UI implementation.

<!-- This doc defines WHAT UI components exist and HOW they look/behave. It does NOT define screen maps, scene hierarchies, modal graphs, or full HUD structure — those belong in engine docs or planning docs. Component-level feedback (what a button looks like pressed) is defined here; coordinated cross-modal feedback (what happens when a building is placed) is in feedback-system.md. -->

---

## Component Definitions

<!-- Define each UI component the game needs. Derive from the design doc's Player Verbs, Core Loop, and Player Control Model — what does the player need to see and interact with? Reference system designs for what information each system surfaces to the player. Reference resource-definitions for what items/resources need UI representation. -->

### Panels

<!-- What panel types exist? Info panels, build panels, zone panels, inventory panels, alert panels? What does each contain? How do they open/close? -->

### Buttons

<!-- Button types: primary action, secondary action, toggle, icon-only, text-only, icon+text. Size variants. -->

### Tooltips

<!-- When do tooltips appear? What information do they show? Delay before showing? Rich content (stats, descriptions) vs simple labels? -->

### Progress Bars

<!-- What uses progress bars? Construction, need fulfillment, health, skill training? Segmented vs continuous? Color from color-system tokens. -->

### Alerts & Notifications

<!-- How are alerts and notifications displayed? Feed, toast, banner, modal? Severity levels? Dismissal rules? Reference color-system signal palette for severity colors. -->

### Confirmation Dialogs

<!-- When does the game ask for confirmation? Destructive actions only? What information is shown? Default focus (confirm vs cancel)? -->

---

## Layout Rules

<!-- Rules for how components are arranged on screen. Keep this at the component composition level — not full screen maps. -->

### Spacing

<!-- Spacing scale (e.g., 4px base unit). Padding inside components. Margins between components. Consistent gaps. -->

### Safe Zones

<!-- Screen edge margins where UI should not place content. Platform-specific safe zones (TV overscan, notch areas). -->

---

## Typography

<!-- Type scale, font choices, weight usage. Reference the style-guide's visual tone and the design doc's Player Information Model for data density needs. -->

<!-- Define:
- Heading sizes (H1-H4 and when each is used)
- Body text size and line height
- Label/caption size
- Numeric display (monospace for stats?)
- Maximum line lengths for readability
-->

---

## Iconography

<!-- Icon design rules for this game. Reference the style-guide's Iconography Style section for aesthetic direction. Reference entity-components for what entity types need icons. -->

### Icon Categories

<!-- What types of icons does the game need? Resource icons, entity icons, action icons, status icons, alert icons, system icons? -->

### Icon Rules

<!-- Size constraints, color usage (tokens from color-system), outline rules, minimum readable size, state variants (normal, disabled, active, alert). -->

---

## Component States

<!-- How do interactive components change across states? Map states to color tokens from color-system.md. -->

| State | Visual Treatment | Color Token | Example |
|-------|-----------------|-------------|---------|
| Default | <!-- base appearance --> | <!-- token --> | <!-- --> |
| Hover | <!-- highlight change --> | <!-- token --> | <!-- --> |
| Pressed | <!-- depression/scale --> | <!-- token --> | <!-- --> |
| Focused | <!-- focus ring/glow --> | <!-- token --> | <!-- --> |
| Disabled | <!-- muted/grey --> | <!-- token --> | <!-- --> |
| Error | <!-- error highlight --> | <!-- token --> | <!-- --> |
| Selected | <!-- selection indicator --> | <!-- token --> | <!-- --> |

---

## Animation & Transitions

<!-- How do UI elements animate? Reference the style-guide's Animation Style for motion language and timing. -->

<!-- Define:
- Transition duration for panel open/close
- Hover/press animation timing
- Easing curves (ease-out for appearing, ease-in for disappearing)
- What NEVER animates (critical alerts appear instantly?)
-->

---

## Sound Feedback

<!-- Per-component sound events. These define LOCAL component sounds (click, hover, toggle). Coordinated cross-modal feedback (what happens when a game event fires) belongs in feedback-system.md. Audio aesthetic rules belong in audio-direction.md. -->

| Component | Event | Sound | Notes |
|-----------|-------|-------|-------|
| Button | Click | <!-- short, crisp --> | |
| Button | Hover | <!-- subtle, optional --> | |
| Panel | Open | <!-- whoosh/slide --> | |
| Panel | Close | <!-- reverse of open --> | |
| Toggle | On | <!-- distinct from Off --> | |
| Toggle | Off | <!-- --> | |
| Alert | Appear | <!-- severity-dependent --> | Coordinated with feedback-system |

---

## Responsive & Resolution Scaling

<!-- How does the UI adapt to different screen sizes and resolutions? Reference the design doc's Target Platforms section. -->

<!-- Define:
- Minimum supported resolution
- Scaling strategy (DPI-aware, fixed pixel, proportional)
- What changes at different scales (font size, icon size, spacing, component size)
- Touch target minimums if applicable
-->

---

## Rules

1. All UI implementation must use components defined here. New component types require updating this doc first.
2. Component colors reference tokens from color-system.md — never raw hex values.
3. This doc defines components and composition. Screen maps, scene hierarchies, and full HUD layout belong in engine docs or planning docs.
4. Per-component sounds are defined here. Cross-modal coordination (visual + audio + UI firing together for game events) belongs in feedback-system.md.
