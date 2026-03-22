---
name: scaffold-iterate
description: "Adversarial document review using an external LLM. Orchestrated by iterate.py — handles any layer (design, systems, spec, task, slice, phase, roadmap, references, style, input, engine). Supports single targets and ranges. Replaces all layer-specific iterate skills."
argument-hint: "<layer> [target] [--focus \"concern\"] [--topics \"1,3\"] [--iterations N] [--max-exchanges N] [--signals \"...\"] [--sections \"Identity,Shape\"] [--fast]"
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
user-invocable: true
---

# Adversarial Document Review

Run an adversarial per-topic review of scaffold documents: **$ARGUMENTS**

This skill orchestrates reviews across all document layers using `iterate.py` and per-layer YAML configs. The Python script manages the topic loop, issue delivery, review lock, scope guard, and report generation. Claude's job is simple: **adjudicate each issue one at a time**.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `<layer>` | Yes | — | Layer to review: `design`, `systems`, `spec`, `task`, `slice`, `phase`, `roadmap`, `references`, `style`, `input`, `engine` |
| `[target]` | Depends | — | Target document or range. Required for layers with ranges (e.g., `SYS-001`, `SPEC-001-SPEC-020`). Optional for fixed-target layers (e.g., `design` always reviews `design-doc.md`). |
| `--focus` | No | — | Narrow review to a specific concern within each topic |
| `--topics` | No | all | Comma-separated topic numbers (e.g., `"1,3,5"`) |
| `--iterations` | No | from config | Maximum outer loop iterations |
| `--max-exchanges` | No | from config | Maximum back-and-forth exchanges per topic |
| `--signals` | No | — | Design signals from the corresponding fix skill |
| `--sections` | No | — | Section groups that changed (auto-maps to relevant topics via config) |
| `--topic` | No | — | Single topic number (shorthand for `--topics "N"`) |
| `--fast` | No | false | Batch L3 subsection reviews by parent section instead of one-at-a-time. Fewer API calls, less granular. |

## How It Works

The review uses a three-pass model: L3 (subsections) → L2 (sections) → L1 (document). Each pass builds on the previous — fix the bricks before judging the wall.

```
User calls /scaffold-iterate <layer> [target] [args]
│
├─ 1. Parse arguments
├─ 2. Resolve work list (single target or range)
├─ 3. For each target document:
│   ├─ a. Preflight check (iterate.py preflight)
│   ├─ b. For each iteration (1..max):
│   │   │
│   │   ├─ L3 PASS — Subsections (### level)
│   │   │   For each ### subsection in the YAML config:
│   │   │   ├─ Send ONLY that subsection's content + its questions to the reviewer
│   │   │   ├─ While issues remain:
│   │   │   │   ├─ READ the issue
│   │   │   │   ├─ ADJUDICATE: accept / reject / escalate / respond
│   │   │   │   └─ Get next issue
│   │   │   ├─ Sleep between subsections
│   │   │   └─ Next subsection
│   │   │   (--fast mode: batch all ### under each ## parent as one call)
│   │   │
│   │   ├─ L2 PASS — Sections (## level)
│   │   │   For each ## section in the YAML config:
│   │   │   ├─ Send the FULL section content + its L2 questions to the reviewer
│   │   │   ├─ Adjudicate issues one at a time
│   │   │   ├─ Sleep between sections
│   │   │   └─ Next section
│   │   │
│   │   ├─ L1 PASS — Document (# level)
│   │   │   ├─ Send the WHOLE document + L1 questions to the reviewer
│   │   │   ├─ Adjudicate issues one at a time
│   │   │   ├─ Run identity check / bias pack / stress test (if configured)
│   │   │   └─ Done
│   │   │
│   │   ├─ Apply accepted changes (iterate.py apply) → Claude edits the files
│   │   └─ Check convergence (iterate.py convergence)
│   │       ├─ clean → stop
│   │       ├─ converged → stop
│   │       ├─ human_only → stop, report escalations
│   │       ├─ limit → stop
│   │       └─ needs_iteration → back to L3 (verification pass)
│   │
│   └─ c. Generate report (iterate.py report) → Claude writes review log
└─ 4. Print final summary
```

### Default vs Fast Mode

**Default (granular):** Each `###` subsection is a separate review call. The reviewer only sees one subsection at a time with 2-4 targeted questions. Best quality — the reviewer can't skip subsections or give shallow answers.

**`--fast` mode:** All `###` subsections under each `##` parent are batched into one review call. The reviewer sees the full section with all subsection questions at once. Fewer API calls, less granular.

```
Default:    20 L3 calls → 6 L2 calls → 1 L1 call = 27 calls (systems example)
--fast:      6 L3 calls → 6 L2 calls → 1 L1 call = 13 calls
```

### Multi-Doc Layers (style, input, references, engine)

For layers with multiple documents, the flow is:

```
For each doc in the layer:
  ├─ L3: review each ### subsection (per-doc tailored questions)
  ├─ L2: review each ## section (per-doc tailored questions)
  └─ Per-doc summary question

After all docs reviewed:
  └─ L1: cross-doc integration review (layer-wide questions)
```

## Execution

### Step 1 — Parse Arguments and Resolve Work List

Parse `$ARGUMENTS` to extract layer, target, and options.

**Single targets:** `design`, `roadmap`, `SYS-005`, `SPEC-042`, `TASK-017`, etc.
**Ranges:** `SYS-001-SYS-043`, `SPEC-001-SPEC-020`, `TASK-001-TASK-010`, etc.

For ranges, glob the matching files and build a work list sorted by ID number.

For layers with `target_type: fixed` in their config (e.g., `design`, `roadmap`), the target is predetermined — no argument needed.

**Section scoping:** If `--sections` is provided (e.g., `--sections "Identity,Player Experience"`), only review the L3 subsections and L2 sections matching those `##` groups. L1 still runs in full since it's holistic.

### Step 2 — Loop Over Work List

For each document in the work list, execute Steps 3-6 below. This is the skill's primary job — a simple sequential loop.

### Step 3 — Preflight

```bash
python scaffold/tools/iterate.py preflight --layer <layer>
```

Check the JSON output:
- `"status": "ready"` → proceed. Note any `skip_topics`.
- `"status": "blocked"` → report the message to the user and stop this target.

### Step 4 — Iteration Loop

For each iteration (starting at 1):

#### 4a — L3 Pass (### Subsections)

For each `###` subsection defined in the YAML config's `l3_sections`:

```bash
python scaffold/tools/iterate.py start \
    --layer <layer> \
    --target <relative-path> \
    --pass l3 \
    --section "### Purpose" \
    --iteration <N> \
    [--focus "concern"]
```

The script extracts ONLY that subsection's content from the document, combines it with the subsection's questions from the YAML config, and sends it to the reviewer. Returns issues one at a time.

**`--fast` mode:** Instead of one call per `###`, batch all `###` subsections under each `##` parent into one call:

```bash
python scaffold/tools/iterate.py start \
    --layer <layer> \
    --target <relative-path> \
    --pass l3 \
    --section "## Identity" \
    --iteration <N> \
    --fast
```

**Adjudicate each issue** (same for all passes):

For each issue returned, read it carefully. The issue contains `severity`, `section`, `description`, and `suggestion`. Decide on one outcome:

1. **Accept** — the issue is valid and the fix is appropriate.
   - First, run scope check:
     ```bash
     python scaffold/tools/iterate.py scope-check --session <id> --change "<description>"
     ```
   - Review the scope guard tests returned. If any test fails, reject instead.
   - If scope is clean:
     ```bash
     python scaffold/tools/iterate.py adjudicate --session <id> --outcome accept --reasoning "..."
     ```

2. **Reject** — the issue is incorrect, out of scope, or contradicted by higher-authority docs.
   ```bash
   python scaffold/tools/iterate.py adjudicate --session <id> --outcome reject --reasoning "..."
   ```

3. **Escalate** — requires user judgment, unclear authority, or reviewer and Claude remain split.
   ```bash
   python scaffold/tools/iterate.py adjudicate --session <id> --outcome escalate --reasoning "..."
   ```

4. **Pushback** — Claude disagrees and wants to counter-argue before deciding.
   ```bash
   python scaffold/tools/iterate.py respond --session <id> --message "counter-argument"
   ```
   - Read the reviewer's response, then adjudicate.

After adjudicating, the script returns the next issue or `"status": "section_complete"`.

**Sleep between subsections** to avoid rate limits.

#### 4b — L2 Pass (## Sections)

For each `##` section defined in the YAML config's `l2_sections`:

```bash
python scaffold/tools/iterate.py start \
    --layer <layer> \
    --target <relative-path> \
    --pass l2 \
    --section "## Identity" \
    --iteration <N>
```

The script extracts the FULL section content (including all `###` subsections) and sends it with the L2 questions. These questions focus on cross-subsection coherence — do the subsections within this section agree with each other?

Adjudicate issues using the same process as L3.

#### 4c — L1 Pass (# Document)

```bash
python scaffold/tools/iterate.py start \
    --layer <layer> \
    --target <relative-path> \
    --pass l1 \
    --iteration <N>
```

The script sends the WHOLE document with the `l1_questions` from the YAML config. These are the big-picture questions — does the document hold together as a whole?

If the config includes `identity_check`, `bias_pack`, or `stress_test`, those run as part of L1.

#### 4d — Apply Changes

After all three passes:
```bash
python scaffold/tools/iterate.py apply --session <id>
```

The script returns the list of accepted changes. **Claude applies each change** by editing the target file(s) using the Edit tool. Only edit files listed in the layer config's `adjudication.editable_files`.

#### 4e — Check Convergence

```bash
python scaffold/tools/iterate.py convergence --session <id>
```

- `"clean"` → no issues found, stop iterating
- `"converged"` → same issues as before, stop
- `"human_only"` → only escalations remain, stop
- `"limit"` → max iterations reached, stop
- `"needs_iteration"` → changes were applied, run another pass (back to 4a — verification)

**Verification pass rule:** If changes were applied, the next iteration is a verification pass. Only a pass with ZERO new issues counts as clean. Stopping after fixes without verification is a skill failure.

### Step 5 — Generate Report

```bash
python scaffold/tools/iterate.py report --session <id>
```

The script returns:
- `report` — the formatted summary to display to the user
- `log_content` — the full review log content
- `log_path` — where to write the log file

**Claude writes:**
1. The review log to `scaffold/decisions/review/<log_name>` using the Write tool
2. Updates `scaffold/decisions/review/_index.md` with a new row

**Claude fills in** the final questions and rating in the report based on the review findings.

### Step 6 — Print Summary

Display the report to the user. If there are escalated issues, present them using the Human Decision Presentation pattern — numbered, with concrete options (a/b/c).

## Adjudication Principles

These apply regardless of layer. Layer-specific rules are in the YAML configs.

- **Project documents and authority order win.** Higher-ranked documents decide disputes.
- **Never blindly accept.** Every issue gets evaluated against project context.
- **Pushback is expected and healthy.**
- **Never half-accept.** Choose exactly one outcome per issue.
- **Resolved issues are locked.** The script tracks this — if an issue reappears with the same root cause, it was already filtered out.
- **Reappearing material issues escalate to user** after 2 iterations.
- **Cross-topic soft weaknesses escalate** if the same issue degrades 2+ topics.
- **Practicality check.** Reject changes that increase rigidity without improving usability.
- **Edits are limited to clarification and restructuring** unless the layer config explicitly allows broader changes. Never invent content to solve a review issue — flag the gap.
- **Ownership changes always require user confirmation.**

## Provider Fallback

The Python scripts handle provider fallback automatically (via `review_config.json`). If all providers are exhausted, `iterate.py` returns `"fallback": "self-review"`. In that case:

Fall back to **self-review mode**: Claude performs the review directly using the same topics and criteria from the YAML config — without the external LLM. Self-review is weaker (no independent perspective) but better than stopping. Log which mode was used.

## Range Review Notes

For range reviews (e.g., `SYS-001-SYS-043`):

1. Glob all matching files for the range.
2. Sort by ID number.
3. Log the full work list.
4. Loop through each document sequentially, running the full review cycle (Steps 3-5) for each.
5. After all documents reviewed, print a combined summary with per-document ratings.

Cross-document topics (e.g., Topic 4 "Cross-System Coherence" for systems) should be run last, after all individual documents have been reviewed and updated.

## Rules

- **Do not run this skill on documents that haven't been through their fix skill first.** The preflight check catches this.
- **Sleep between API calls.** The topic sleep is configured per layer. Respect it.
- **Clean up temporary files** (pushback messages, topic prompts) after use.
- **Only edit files in the editable_files list** from the layer config.
- **Log which review mode was used** (adversarial vs self-review) in the review log.
