# Audio Workflow

> **What this is:** The full audio production pipeline — from identifying what's needed through creating, reviewing, and integrating audio assets. Covers all audio disciplines (SFX, music, ambience, voice) with the actual craft steps, regardless of whether you're working manually, with AI tools, or a hybrid approach.

## Connection to the Main Pipeline

```
Design Pipeline                        Audio Pipeline
───────────────                        ──────────────
Design doc ──→ Entity Presentation ──→ What entities sound like (high-level)
                      │
              Audio Direction ──→ Sound philosophy, categories, hierarchy
                      │
System designs ──→ Asset Needs ──→ Per-system audio requirements
                      │
Specs approved ──→ Asset Requirements ──→ Scan existing assets
                   (what's needed)        ├── Reusable? → mark Ready
                                          └── Needed? → enter Audio Pipeline
                                                │
Task seeding ──→ TASK-###_audio created           │
                 (file paths + prompts)           │
                      │                           │
                      ├── Reference & Design      │
                      ├── Production (discipline) │
                      ├── Technical Prep          │
                      ├── Import & Validate       │
                      ├── Iterate                 │
                      ├── Place at listed paths ──┘
                      └── /scaffold-implement auto-completes task
                           └── wiring tasks unblock
```

**Audio does not block spec approval.** Specs can be approved with Needed assets. Audio blocks **task implementation** — `/scaffold-implement` checks if assets exist at the file paths listed in the audio task's Asset Delivery table. Missing assets block; all present auto-completes the task.

## Asset Types

| Type | Output Directory | Discipline |
|------|-----------------|------------|
| Sound effects | `assets/entities/[entity]/` or `assets/ui/` | Sound design |
| Music | `assets/music/` | Composition & production |
| Ambience | `assets/environment/[location]/` | Environmental sound design |
| Voice | `assets/entities/[entity]/` | Voice production |

---

## Phase 1 — Identify Requirements

**When:** Audio identification happens at three levels, progressively more specific:
1. **Design doc** (`### Entity Presentation`) — high-level sound identity per content category
2. **System designs** (`### Asset Needs`) — per-system audio requirements tied to actions/states
3. **Specs** (`### Asset Requirements`) — per-behavior asset list with Status: Needed/Ready

**Source for production:** The audio task's `## Asset Delivery` table (auto-generated during task seeding from spec Asset Requirements). Each row has file path, duration, and a generation prompt.

Before marking anything as Needed:
1. **Scan existing audio** — glob `assets/` subdirectories for sounds that match.
2. **Check for reusable base sounds** — pitch shift, volume adjustment, or layering can make one sound serve multiple purposes.
3. **Check feedback-system.md** — the Event-Response Table defines what sound categories this behavior maps to. Use those categories to search for existing audio.
4. **Only mark Needed** for audio that genuinely doesn't exist and can't be derived from existing work.

## Phase 2 — Reference & Design

**Before producing any audio**, establish the sonic direction:

1. **Read the audio task** — the Asset Delivery table has generation prompts pre-built from audio direction context. Use these as starting points.

2. **Read design context** (if the prompts need refinement):
   - `design/audio-direction.md` — audio philosophy, sound categories, restraint principles, feedback hierarchy
   - `design/feedback-system.md` — event-response coordination, priority level, cross-modal timing
   - `design/style-guide.md` — visual tone (translate to audio: gritty → raw, polished → clean, organic → natural)
   - `design/design-doc.md` — Entity Presentation sound identity, world setting, mood, genre

3. **Find reference sounds** — existing games, sound libraries, recordings that capture the target character.

3. **Define the sound's role:**
   - What feedback priority is this? (Critical alert vs ambient detail)
   - What visual channel fires alongside it? (Must complement, not compete)
   - How frequently will it play? (Constant loop vs rare event)
   - What audio layer does it belong to? (Music, ambience, SFX, voice)

---

## Phase 3 — Production

This phase varies by discipline. Follow the pipeline for the asset type you're creating.

### Sound Effects (SFX)

| Step | What | Details |
|------|------|---------|
| **1. Source material** | Record, pull from library, or synthesize | Foley recording for organic sounds (impacts, footsteps). Synthesis for abstract sounds (UI, alerts, power-ups). Sound libraries for foundation layers. |
| **2. Layering** | Combine multiple sources into one sound | A "sword impact" might be: metal clang + cloth movement + bass thud. Layer for richness, not complexity — each layer should add something distinct. |
| **3. Editing** | Trim, time-stretch, pitch-shift | Cut to the right length. Align the transient (the initial "hit") to the start. Remove dead air. Tighten the tail. |
| **4. Processing** | EQ, compression, reverb, distortion | EQ to carve out space in the mix (don't compete with music frequencies). Compression for consistent loudness. Reverb only if the sound plays in a specific space — in-engine reverb is usually better. Distortion/saturation for aggressive or lo-fi sounds. |
| **5. Variation** | Create 2-3 variants for frequent sounds | Slight pitch randomization (±5-10%). Timing variation. Different layers. For footsteps, impacts, and UI clicks — multiple variants prevent listener fatigue. |
| **6. Normalization** | Consistent loudness across all SFX | Use a loudness target (e.g., -14 LUFS for SFX). Leave headroom — the engine handles final mixing. Critical sounds should be louder than ambient ones, but the range should be controlled. |
| **7. Export** | Correct format, sample rate, bit depth | OGG Vorbis for Godot (smaller file size, good quality). WAV for lossless archival. 44.1kHz or 48kHz sample rate. 16-bit minimum. Mono for sounds without spatial character; stereo for wide sounds. |

**AI-assisted shortcut:** AI sound generation (ElevenLabs SFX) can replace steps 1-2 (sourcing and layering) for certain SFX types. The output still needs steps 3-7 — AI-generated sounds often have wrong length, inconsistent loudness, or artifacts that need editing. AI works best for ambient SFX, abstract UI sounds, and environmental effects. It struggles with precise foley (footsteps, cloth), musical SFX, and sounds that need tight timing.

### Music

| Step | What | Details |
|------|------|---------|
| **1. Direction** | Define mood, tempo, instrumentation, energy | From audio-direction and the spec's context. Determine BPM range, key signature, instrument palette. Decide whether this is a looping background track, a one-shot stinger, or an adaptive multi-stem piece. |
| **2. Composition** | Melody, harmony, arrangement | Write the musical content. For game music: prioritize atmosphere over complexity. Melodies should be recognizable but not demanding of attention. Harmonic movement should support the gameplay mood without distracting. |
| **3. Production** | Instrument selection, sound design, mixing | Choose instruments that match the audio-direction's palette. Mix so that the music sits behind gameplay SFX — music is the foundation layer, not the foreground. Leave frequency space for alerts and voice. |
| **4. Loop engineering** | Seamless loop points, intro/outro variants | The loop point must be inaudible. Test by listening to the transition 20+ times — any click, volume jump, or rhythmic hiccup means the loop isn't clean. For tracks with intros: export an intro version and a loop version separately. |
| **5. Adaptive layers (if needed)** | Stems for dynamic intensity | Export individual instrument groups as stems: bass, percussion, melody, pads. In-engine, these layers can be added/removed to change intensity (calm → tension → crisis) without crossfading to a different track. |
| **6. Mastering** | Final loudness, EQ, limiting | Master quieter than you think — music must leave room for SFX, voice, and alerts. Target -16 to -20 LUFS for game background music. Apply a limiter to prevent clipping, not to maximize loudness. |
| **7. Export** | Loop metadata, stem exports, correct format | OGG Vorbis for Godot. If adaptive: export each stem as a separate file with identical length and start points. Include loop point metadata if the format supports it. |

**AI-assisted shortcut:** AI music generation (ElevenLabs, Suno, Udio) can generate full tracks from prompts. The output is usable for prototyping and mood exploration. For production: AI music often has poor loop points (step 4), no adaptive stems (step 5), and inconsistent mastering (step 6). These require manual post-processing in a DAW.

### Ambience

| Step | What | Details |
|------|------|---------|
| **1. Environment definition** | What does this space sound like? | Define the sonic character: indoor/outdoor, natural/artificial, busy/quiet, time of day. Reference real-world spaces or other games. |
| **2. Base layer** | The constant background | The always-present sound: wind, room tone, distant machinery, ocean wash. Should be smooth, unobtrusive, and set the foundation for the space. |
| **3. Detail layers** | Intermittent sounds on top of the base | Bird calls, dripping water, distant thunder, footsteps of NPCs, creaking wood. These add life and variety. They should be sparse enough to feel natural, not constant. |
| **4. Spatial consideration** | Stereo width, implied distance, depth | Base layer: wide stereo for immersion. Detail layers: panned for spatial interest. Implied distance through reverb and frequency content (distant sounds lose high frequencies). |
| **5. Loop engineering** | Seamless, long enough to avoid repetition | Minimum 60 seconds for base layers — longer is better. The loop point must be inaudible. Detail layers can be shorter if they're triggered randomly rather than looping. |
| **6. Mix integration** | Must sit under everything else | Ambience is the lowest-priority audio layer. It should fill silence without competing with SFX, music, or voice. Test by playing ambience with every other layer active — if you can't hear the SFX clearly, the ambience is too loud. |
| **7. Export** | Loopable format, correct loudness | OGG Vorbis. Target -24 to -28 LUFS (very quiet — this is intentional). Base layer as one file. Detail layers as separate files for engine-triggered playback. |

**AI-assisted shortcut:** AI ambient generation (ElevenLabs SFX with looping) can produce base layers effectively. Detail layers typically need manual creation or library sourcing because they require precise timing and spatial placement. AI ambience often needs manual loop point correction (step 5) and loudness normalization (step 6).

### Voice

| Step | What | Details |
|------|------|---------|
| **1. Script** | Write the lines from the game's tone | Dialogue, barks (short contextual exclamations), narration, announcements. Match the design-doc's tone and the audio-direction's voice guidance. Keep barks under 3 seconds. Ensure lines work out of context (the player may hear them in any order). |
| **2. Casting** | Choose the voice | AI voice (OpenAI TTS, ElevenLabs) or human voice actor. For AI: select a voice that matches the character's personality. For human: provide character description, reference lines, and emotional range. |
| **3. Recording / generation** | Capture the performance | For AI: generate via TTS API (OpenAI, ElevenLabs). For human: record in a quiet space, consistent microphone distance, consistent energy level. Multiple takes per line. |
| **4. Editing** | Clean up, trim, normalize timing | Remove breaths (or reduce them — total removal sounds unnatural). Trim silence from start and end. Ensure consistent pacing across all lines for the same character. |
| **5. Processing** | EQ for character, compression, effects | EQ to match the character's vocal quality (warm, thin, nasal, deep). Compress to control dynamics — game dialogue needs consistent loudness. Apply context effects: radio filter for comms, reverb for large spaces, distortion for corruption/damage. |
| **6. Integration prep** | Naming, metadata, subtitle sync | File naming convention matching the script structure (e.g., `colonist_bark_hungry_01.mp3`). Timing metadata for subtitle display. Language tags if localizing. |
| **7. Export** | Correct format, consistent loudness | OGG Vorbis for Godot. Target -14 LUFS for voice (voice sits above music and ambience). All lines for the same character should have matched loudness. Mono for standard dialogue; stereo only for spatial voice (environmental announcements). |

**AI-assisted shortcut:** AI voice (OpenAI TTS, ElevenLabs) replaces steps 2-3 (casting and recording). The output still needs steps 4-7 — AI voice often has inconsistent pacing, unnatural breathing patterns, and loudness variation. AI works well for prototype voiceover, narrator-style lines, and UI announcements. It struggles with emotional range, character acting, and barks that need specific timing.

---

## Phase 4 — Technical Prep

After production, prepare the audio for the engine:

| Audio type | Technical prep |
|-----------|---------------|
| SFX | Trim silence, normalize loudness, verify mono/stereo, check for clipping |
| Music | Verify loop points (listen 20+ times), export stems if adaptive, verify loudness target |
| Ambience | Verify loop seamlessness, verify loudness sits below SFX/music, export detail layers separately |
| Voice | Match loudness across all lines for same character, verify subtitle timing, verify naming convention |

**Common across all types:**
- File format correct for the engine (OGG for Godot)
- Sample rate consistent (44.1kHz or 48kHz — pick one, don't mix)
- No clipping (peaks should not hit 0 dBFS)
- Metadata correct (loop points, channel count)

## Phase 5 — Import & Validate In-Game

1. **Import** into the engine with correct audio bus assignment:
   - SFX → SFX bus
   - Music → Music bus
   - Ambience → Ambience bus
   - Voice → Voice bus

2. **Test in the actual gameplay context:**
   - Does the sound play at the right moment? (Signal wiring correct)
   - Is it the right volume relative to everything else playing? (Mix balance)
   - Does it match the feedback-system's priority? (Critical alerts > SFX > music > ambience)
   - For loops: does it loop seamlessly in-engine? (Engine loop behavior may differ from DAW)
   - For frequent SFX: is it annoying after 20 repetitions? (Audio fatigue)
   - For voice: is it understandable over music and SFX? (Intelligibility)

3. **Spatial test (if applicable):**
   - Does the sound attenuate with distance correctly?
   - Does panning match the visual position?
   - Does reverb match the space?

## Phase 6 — Iterate

If validation fails, return to the appropriate production step:
- Wrong character/mood → back to reference & design
- Wrong loudness → back to normalization/mastering
- Bad loop → back to loop engineering
- Annoying on repeat → create more variants or adjust processing
- Competes with other layers → back to mix integration/EQ

## Phase 7 — Accept & Register

1. Update the spec's Asset Requirements table: Status → **Ready**, Satisfied By → asset path.
2. Update the audio index (`assets/[category]/_index.md`).
3. If reusable across specs, update all specs that can use it.

---

## Audio Layers and Priority

The game's audio exists in layers. Every asset must know which layer it belongs to:

| Layer | Priority | Loudness target | Ducking behavior | When it plays |
|-------|----------|----------------|-----------------|---------------|
| **Voice** | Highest | -14 LUFS | Music and ambience duck | Character speech, narration, announcements |
| **Critical SFX** | High | -12 LUFS | Music ducks | Alarms, emergency alerts, damage |
| **Gameplay SFX** | Medium-High | -14 LUFS | Does not duck | Actions, confirmations, state changes |
| **UI SFX** | Medium | -16 LUFS | Does not duck | Clicks, hovers, panel open/close |
| **Music** | Low | -18 LUFS | Ducks for voice and critical SFX | Background tracks, tension cues |
| **Ambience** | Lowest | -26 LUFS | Ducks for everything | Environmental loops, atmosphere |

These targets come from `design/audio-direction.md` and `design/feedback-system.md`. Production must match the priority — a critical alert that's quieter than ambient wind is a production failure.

## Feedback System Alignment

Every audio asset maps to the feedback system:

| Feedback event type | Audio layer | Production implication |
|--------------------|------------|----------------------|
| Action Confirmation | UI SFX / Gameplay SFX | Short, satisfying, not attention-demanding |
| Action Failure | UI SFX | Distinct from confirmation — the player must know something went wrong |
| State Change | Gameplay SFX | Informative — communicates what changed without explanation |
| Warning / Escalation | Gameplay SFX | Increasing urgency — must scale in intensity |
| Critical Alert | Critical SFX | Cannot be missed — loudest, most distinct sound in the palette |
| Ambient State | Ambience | Continuous, unobtrusive, sets the mood |
| Sustained State | Music | Evolves slowly, supports the gameplay rhythm |

When producing audio for a spec, check which feedback event type the behavior maps to. That determines the audio layer, loudness target, and production character.

## Reuse Strategy

Audio reuse is extremely effective because small parameter changes create perceptually different sounds.

**SFX reuse patterns:**
- **Pitch shift** — same impact sound at -3, 0, +3 semitones = light, medium, heavy
- **Speed change** — same UI sound at 0.8x, 1.0x, 1.2x speed = different interactions
- **Layer addition** — base click + added reverb = indoor vs outdoor variant
- **Truncation** — full impact sound vs just the transient = different intensities

**Music reuse patterns:**
- **Stem removal** — full track minus percussion = calm variant
- **Tempo change** — same composition at different BPM for different tension levels
- **Key transposition** — same melody in a different key for a different location/mood

**Ambience reuse patterns:**
- **Layer combination** — base wind + rain = stormy. Base wind + birds = pleasant. Same base, different detail layers.
- **Filter sweeps** — same ambience with low-pass filter = muffled indoor version

**Voice reuse patterns:**
- **Bark pools** — 3-5 variants of the same intent (hungry bark, tired bark) played randomly
- **Pitch matching** — same voice at different pitches for different characters (use sparingly)

## Batch Production

Group related audio for consistency:
- All UI SFX in one session (consistent click family)
- All alert sounds from quiet to critical (escalating series)
- All ambience base layers for one biome
- All barks for one character

Batch production ensures sonic consistency and makes the feedback priority hierarchy audible.

## Rules

- **Never produce production audio without a spec requirement.** Experimental sounds are freeform, but audio that ships needs a spec.
- **Always read audio-direction and feedback-system before producing.** These define what the game sounds like and when sounds play.
- **Reuse before produce.** Pitch shift, layer, and filter existing sounds before creating new ones.
- **Audio does not block specs.** Specs can be approved with Needed audio. Audio blocks task completion, not planning.
- **Validate in-engine, not just in the DAW.** An asset that sounds good in Audacity may not work in-game at the right volume, timing, or layering.
- **Mark asset status in specs immediately.** When audio is accepted, update the spec table right away.
- **Index every asset.** Every produced audio file gets a row in its category's `_index.md`.
- **Respect the priority hierarchy.** A critical alert must be louder and more distinct than a UI click. Production loudness must match the layer's target.
- **Test loops obsessively.** Listen to the loop transition 20+ times. Any audible seam means it's not ready.
- **Produce variants for frequent sounds.** Any SFX that plays more than once per minute needs 2-3 variants minimum to prevent listener fatigue.
- **Leave headroom.** The engine handles final mixing. Individual assets should never be mastered to 0 dBFS — leave room for the audio bus chain.
