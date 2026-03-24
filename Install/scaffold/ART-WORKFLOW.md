# Art Workflow

> **What this is:** The full art production pipeline — from identifying what's needed through creating, reviewing, and integrating visual assets. Covers all art disciplines (2D, 3D, UI) with the actual craft steps, regardless of whether you're working manually, with AI tools, or a hybrid approach.

## Connection to the Main Pipeline

```
Design Pipeline                        Art Pipeline
───────────────                        ────────────
Design doc ──→ Entity Presentation ──→ What entities look like (high-level)
                      │
System designs ──→ Asset Needs ──→ Per-system art requirements
                      │
Specs approved ──→ Asset Requirements ──→ Scan existing assets
                   (what's needed)        ├── Reusable? → mark Ready
                                          └── Needed? → enter Art Pipeline
                                                │
Task seeding ──→ TASK-###_art created             │
                 (file paths + prompts)           │
                      │                           │
                      ├── Reference & Concept     │
                      ├── Production (discipline) │
                      ├── Technical Prep          │
                      ├── Import & Validate       │
                      ├── Iterate                 │
                      ├── Place at listed paths ──┘
                      └── /scaffold-implement auto-completes task
                           └── wiring tasks unblock
```

**Art does not block spec approval.** Specs can be approved with Needed assets. Art blocks **task implementation** — `/scaffold-implement` checks if assets exist at the file paths listed in the art task's Asset Delivery table. Missing assets block; all present auto-completes the task.

## Asset Types

| Type | Output Directory | Disciplines |
|------|-----------------|-------------|
| Concept art | `assets/concept/` | 2D illustration |
| Character art | `assets/entities/[entity]/` | 2D illustration, 3D modeling |
| Environment art | `assets/environment/` | 2D illustration, 3D modeling |
| Sprite art | `assets/entities/[entity]/` | 2D pixel art, 2D illustration |
| Icon art | `assets/ui/` or `assets/entities/[entity]/` | 2D graphic design |
| UI mockup | `assets/ui/` | UI/UX design |
| Promo art | `assets/promo/` | 2D illustration, composition |
| Texture | `assets/entities/[entity]/` or `assets/environment/` | Texture painting |
| Tileset | `assets/environment/` | Tile design |

---

## Phase 1 — Identify Requirements

**When:** Asset identification happens at three levels, progressively more specific:
1. **Design doc** (`### Entity Presentation`) — high-level visual identity per content category
2. **System designs** (`### Asset Needs`) — per-system art requirements tied to actions/states
3. **Specs** (`### Asset Requirements`) — per-behavior asset list with Status: Needed/Ready

**Source for production:** The art task's `## Asset Delivery` table (auto-generated during task seeding from spec Asset Requirements). Each row has file path, dimensions, and a generation prompt.

Before marking anything as Needed:
1. **Scan existing assets** — glob `assets/` subdirectories for assets that match.
2. **Check for reusable base assets** — a single sprite/mesh/icon can satisfy multiple requirements through variants (color swap, overlay, scale).
3. **Only mark Needed** for assets that genuinely don't exist and can't be derived from existing work.

## Phase 2 — Reference & Concept

**Before producing any asset**, gather reference material:

1. **Read the art task** — the Asset Delivery table has generation prompts pre-built from style context. Use these as starting points.

2. **Read design context** (if the prompts need refinement):
   - `design/style-guide.md` — art style, visual tone, aesthetic pillars, rendering approach
   - `design/color-system.md` — palette, color roles, semantic tokens
   - `design/ui-kit.md` — component dimensions, spacing (for icons and UI)
   - `design/design-doc.md` — Entity Presentation table, world setting, mood, genre

3. **Gather visual references** — mood boards, style examples, existing assets in the same category for consistency.

4. **Create concept art if needed** — for complex or ambiguous assets, rough out the idea before committing to production.

---

## Phase 3 — Production

This phase varies by discipline. Follow the pipeline for the asset type you're creating.

### 2D Art (Sprites, Icons, Concept Art, Illustrations)

| Step | What | Details |
|------|------|---------|
| **1. Sketching** | Rough thumbnails and silhouette exploration | Block out composition, test readability at target size. For sprites: test at actual in-game camera distance. For icons: test at UI target size. |
| **2. Line art** | Clean up sketch into defined shapes | Crisp edges for pixel art. Clean vectors for icons. Loose lines acceptable for concept art. |
| **3. Color blocking** | Apply flat colors from the project palette | Use color-system tokens — don't pick colors freehand. Semantic colors (danger, health, status) must match the token assignments. |
| **4. Shading / lighting** | Add depth, volume, and light direction | Match the style-guide's rendering approach. Pixel art may use dithering. Painterly styles use soft gradients. Flat styles skip this step. |
| **5. Detail pass** | Textures, highlights, edge refinement | Add visual interest without sacrificing readability. Less detail at smaller display sizes. |
| **6. State variants** | Create variants if the asset has states | Idle/active/damaged/selected/disabled. Each variant should be distinguishable at the target display size. |
| **7. Export** | Correct resolution, format, trim | PNG for sprites (transparency). SVG for scalable icons. Sprite sheets sliced with consistent cell sizes. Power-of-two dimensions if the engine requires it. |

**AI-assisted shortcut:** AI image generation (DALL-E, OpenArt, Midjourney) can replace steps 1-5 for certain asset types. The output still needs step 6 (state variants are rarely generated correctly) and step 7 (export formatting). AI works best for concept art, environment illustrations, and character portraits. It struggles with pixel-perfect sprites, precise icon design, and state-variant consistency.

### 3D Art (Characters, Props, Environments)

| Step | What | Details |
|------|------|---------|
| **1. Concept / reference** | 2D concept art or reference images | Front and side views for characters. Orthographic views for architecture. Scale reference using metric units (1 unit = 1 meter). |
| **2. Blockout** | Rough shapes for proportions and silhouette | Use primitives. Nail the silhouette before adding detail. Test in-engine early if possible — catch scale problems now. |
| **3. High-poly modeling** | Detailed sculpt with full geometry | Add all visual detail. This is the "source of truth" mesh. For characters: model in T-pose or A-pose for rigging. |
| **4. Retopology** | Create clean low-poly mesh for real-time use | Optimize face count for the target platform's performance budget. Edge loops at joints for clean deformation. Quads preferred over triangles for animation. |
| **5. UV unwrapping** | Flatten the mesh for texturing | Minimize stretching. Keep seams in hidden areas. Shared UV space for assets that share materials (e.g., all armor pieces on one atlas). |
| **6. Texturing** | Paint color, normal, roughness, metallic maps | Match the style-guide's visual tone. Use the color-system palette for tintable assets. Bake high-poly detail into normal maps for the low-poly mesh. |
| **7. Rigging** | Build skeleton, weight paint | One skeleton per character archetype. Weight paint for clean joint deformation. For modular systems: all attachable pieces must share the same skeleton. |
| **8. Animation** | Keyframes, blend trees, state machines | Idle, walk, run, action-specific animations. Match the style-guide's animation timing and motion principles. |
| **9. Technical setup** | Blend shapes, LODs, collision, modular attachment | Blend shapes / shape keys for body variation (fat/thin, tall/short). LOD levels for distance rendering. Collision meshes for physics. Attachment points for modular equipment. |
| **10. Export** | Correct format with engine settings | glTF 2.0 (.glb) preferred for Godot. Ensure correct up-axis (+Y). Apply modifiers before export. Export body and skeleton together; modular pieces as separate files rigged to copies of the same skeleton. |

**AI-assisted shortcut:** AI 3D generation (Meshy, Tripo) can replace steps 2-3 (blockout and high-poly). The output still needs steps 4-10 — retopology, UV unwrapping, texturing refinement, rigging, animation, and technical setup all require manual work in Blender or equivalent. AI-generated meshes are a starting point, not a finished asset.

**Modular character systems (armor, clothing, accessories):**

For games with equippable items that must fit varying body shapes:

| Step | What | Details |
|------|------|---------|
| **1. Base mesh** | Model the minimum-size character first | This is the Basis for all blend shapes. T-pose or A-pose. |
| **2. Body shape keys** | Create blend shapes for body variation | "Fat" key (width), "Tall" key (height). Optional corrective key for extremes ("Fat_Tall"). Note: height changes may need bone scaling in-engine rather than blend shapes (blend shapes move vertices, not bones). |
| **3. Armor modeling** | Model armor pieces on the base mesh | Use the minimum-size body as a template. Keep pieces as separate objects for modular export. |
| **4. Armor shape transfer** | Bind armor to body shape changes | Use Surface Deform modifier in Blender: bind armor to body, activate each body shape key, save the resulting armor shape as a matching shape key on the armor. |
| **5. Shared skeleton** | Rig body and all armor to one skeleton | Weight paint the body first (automatic weights). Transfer weights from body to armor pieces using Data Transfer modifier. All pieces must deform identically at joints. |
| **6. Export** | Body + skeleton as one file, each armor piece separately | All pieces reference the same skeleton structure. In-engine: attach armor as child of the player's Skeleton3D, sync blend shape values across body and all equipped pieces. |

### UI/UX Art (Mockups, Components, Layouts)

| Step | What | Details |
|------|------|---------|
| **1. Wireframing** | Layout and information hierarchy | Establish what information goes where, priority ordering, navigation flow. No visual styling yet. |
| **2. Mockup** | Visual design with real colors, fonts, spacing | Apply style-guide typography, color-system tokens, ui-kit spacing rules. Show actual game data, not lorem ipsum. |
| **3. Component design** | Reusable UI atoms and molecules | Buttons, panels, sliders, tooltips, status bars. Each component should match ui-kit definitions. |
| **4. State variants** | Hover, pressed, disabled, error, selected | Every interactive component needs all states from the interaction-model. States must be visually distinct using color-system tokens. |
| **5. Responsive variants** | Different resolutions and aspect ratios | Test at minimum and maximum supported resolutions. Verify text remains readable and layouts don't break. |
| **6. Asset slicing** | 9-patch, atlas packing, icon sheets | Slice components for engine use. 9-patch for stretchable panels. Atlas pack small icons. Export individual elements where the engine needs them separate. |
| **7. Export** | Correct formats and sizes | PNG for raster elements. SVG for scalable elements. Maintain naming convention consistent with ui-kit component names. |

**AI-assisted shortcut:** AI can generate mockup compositions for exploration and layout validation. The output is a reference image, not usable UI assets — steps 3-7 (component design through export) always require manual work or dedicated UI tools.

---

## Phase 4 — Technical Prep

After production, prepare the asset for the engine. This phase is often interleaved with the end of Phase 3.

| Asset type | Technical prep |
|-----------|---------------|
| 2D sprites | Trim transparent borders, consistent cell sizes, power-of-two if needed, sprite sheet packing |
| 2D icons | Consistent dimensions (e.g., all 64x64 or all 128x128), padding for UI layout |
| 3D models | Apply transforms, check normals, optimize face count, verify UV seams, set up LODs |
| 3D rigged | Verify weight painting at extreme poses, check blend shape ranges, test animation playback |
| UI elements | Slice for 9-patch, set anchor points, verify scaling behavior |

## Phase 5 — Import & Validate In-Game

1. **Import** into the engine with correct import settings (texture filtering, compression, audio bus assignment).
2. **Place in-game** at the actual camera distance / UI position where it'll be used.
3. **Validate:**
   - Does it match the style guide's aesthetic?
   - Is it readable at the real display size?
   - Do colors match the color-system tokens?
   - For 3D: does it deform correctly during animation?
   - For UI: does it scale correctly at different resolutions?
   - For modular: does it attach/detach without visual artifacts?

## Phase 6 — Iterate

If validation fails, return to the appropriate production step:
- Wrong proportions → back to blockout/sketching
- Wrong colors → back to color blocking/texturing
- Bad deformation → back to rigging/weight painting
- Wrong feel → back to concept/reference

Each iteration should be targeted — fix the specific problem, don't redo the whole asset.

## Phase 7 — Accept & Register

1. Update the spec's Asset Requirements table: Status → **Ready**, Satisfied By → asset path.
2. Update the art index (`assets/[category]/_index.md`).
3. If reusable across specs, update all specs that can use it.

---

## Reuse Strategy

Art reuse is the primary way to avoid production bloat.

**2D reuse patterns:**
- Color swap — same sprite, different palette (team colors, damage states, biome variants)
- Overlay — base sprite + decal layer (numbered balls = base ball + number overlay)
- Scale — same icon at different sizes
- Flip/rotate — mirrored or rotated versions of the same sprite

**3D reuse patterns:**
- Shared skeleton — one rig for all characters of the same archetype
- Modular attachment — armor, clothing, accessories as separate meshes on a shared skeleton
- Shape keys — one base mesh with blend shapes for body variation
- Material swap — same mesh, different textures (wood vs stone vs metal)
- Instancing — same mesh placed multiple times with transform variation

**UI reuse patterns:**
- 9-patch — one panel graphic that stretches to any size
- Component composition — combine existing atoms into new molecules
- Theme variants — same components with different color token sets

Before generating or creating any new asset, always ask: **can an existing asset satisfy this requirement with a variant?**

## Batch Production

Group related assets for consistency:
- All sprites for one system (e.g., all construction state indicators)
- All icons for one UI panel
- All character variants from one base mesh
- All props for one environment

Batch production ensures visual consistency that's hard to achieve creating assets one at a time across sessions.

## Concept Art vs Production Art

| When | Art type | Purpose | Fidelity |
|------|----------|---------|----------|
| Design (Steps 1-2) | Concept art | Explore visual direction | Low — mood and intent, not pixel-perfect |
| Design (Step 5) | UI mockups | Validate layouts | Medium — real colors and data, not final assets |
| Planning (specs) | Production art | Ship in the game | High — final quality, correct format, all states |
| Marketing | Promo art | Store pages, press kit | High — polished, aspirational |

Concept art and UI mockups can be created anytime. Production art should wait until specs define the requirements.

## Rules

- **Never create production art without a spec requirement.** Concept art is freeform, but assets that ship in the game need a spec to trace back to.
- **Always read design context before producing.** Style guide, color system, and existing assets ensure consistency.
- **Reuse before create.** One good base asset with variants beats five mediocre unique assets.
- **Art does not block specs.** Specs can be approved with Needed assets. Art blocks task completion, not planning.
- **Validate in-engine, not just in the art tool.** An asset that looks good in Blender/Photoshop may not work in-game at the real camera distance, resolution, or animation speed.
- **Mark asset status in specs immediately.** When an asset is accepted, update the spec table right away.
- **Index every asset.** Every produced asset gets a row in its category's `_index.md`.
- **State variants are non-optional for interactive elements.** If a sprite or icon has gameplay states, all states must be produced — not just the default.
- **Match the performance budget.** 3D models must fit the face count budget. Sprite sheets must fit the texture memory budget. Check the engine performance doc.
