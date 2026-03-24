---
name: scaffold-validate
description: "Structural validation gate. Runs deterministic checks via validate.py with per-scope YAML configs. Read-only — never edits files. Reports pass/fail/warn with suggested next actions."
argument-hint: "[--scope design|systems|refs|engine|style|input|roadmap|phases|slices|specs|tasks|foundation|all] [--range SYS-###-SYS-###] [--incremental]"
allowed-tools: Read, Write, Bash, Grep, Glob
user-invocable: true
---

# Structural Validation Gate — Dispatcher

Run structural validation checks on scaffold documents: **$ARGUMENTS**

This skill is a **thin dispatcher** that calls `validate.py` to run deterministic checks defined in per-scope YAML configs. It is **read-only** — it never edits files. It reports pass/fail/warn and suggests the next action (usually `/scaffold-fix <layer>`).

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--scope` | No | `all` | Which checks to run: `design`, `systems`, `refs`, `engine`, `style`, `input`, `roadmap`, `phases`, `slices`, `specs`, `tasks`, `foundation`, `all` |
| `--range` | No | — | Filter to a range within a scope (e.g., `SYS-001-SYS-020`) |
| `--incremental` | No | false | Only validate changed files and their dependents |

## How It Works

```
validate.py runs checks (Python — read-only)
  ├── Deterministic checks (file exists, sections present, index sync, health score)
  ├── Heuristic checks (glossary compliance, design content detection)
  └── Report (pass/fail/warn with impact and confidence)
```

## Execution

### Step 1 — Preflight

```bash
python scaffold/tools/validate.py preflight --scope <scope>
```

Checks activation preconditions (required files exist). Scopes that don't apply yet (e.g., `tasks` when no tasks exist) return `skip` instead of `fail`.

### Step 2 — Run Checks

```bash
python scaffold/tools/validate.py run --scope <scope> [--range <range>] [--incremental]
```

validate.py loads the scope's YAML config, runs all checks, writes `.reviews/validate/action.json` with the report.

### Step 3 — Display Report

Read `action.json` and display:

```
## Validation: [scope]

| Check | Status | Impact | Issues |
|-------|--------|--------|--------|
| systems-index-files | PASS | — | 0 |
| systems-structure | FAIL | Medium | 2 |
| systems-section-health | WARN | Low | 3 |
| ... | ... | ... | ... |

**Verdict:** FAIL
**Blocking:** Yes
**Critical:** 0  **High:** 0  **Medium:** 2  **Low:** 3
**Next:** Run `/scaffold-fix systems` to resolve FAIL issues.
```

## Scopes

| Scope | What It Validates |
|-------|------------------|
| `design` | Design doc structure, governance, cross-references |
| `systems` | System design structure, index sync, health, dependencies |
| `refs` | Reference/architecture doc existence and structure |
| `engine` | Engine doc structure, Step 3 alignment, cross-engine consistency |
| `style` | Step 5 visual/UX doc structure and cross-doc consistency |
| `input` | Input doc structure, action coverage, binding checks |
| `roadmap` | Roadmap structure and coverage |
| `phases` | Phase structure, index sync, entry/exit criteria |
| `slices` | Slice structure, index sync, dependency resolution |
| `specs` | Spec structure, index sync, system references |
| `tasks` | Task structure, index sync, spec references |
| `foundation` | Foundation architecture completeness (Step 7 gate) |
| `all` | All scopes + cross-cutting + cross-layer integrity |

## Check Types

### Deterministic (High Confidence)
Structural checks with no ambiguity. PASS or FAIL.
- File existence
- Section structure (required headings present)
- Index registration (file in _index.md)
- Status-filename sync
- Section health score
- Review freshness

### Heuristic (Medium Confidence)
Pattern-based with clear rules. Labeled `[ADVISORY]`.
- Glossary NOT-column compliance
- Design content detection in engine docs
- Naming convention compliance

## Verdicts

- **PASS** — all checks pass. Proceed to next pipeline step.
- **WARN** — issues found but not blocking. Review and decide.
- **FAIL** — blocking issues. Run `/scaffold-fix <layer>` or `/scaffold-review <layer>` before proceeding.

## File Locations

| File | Lifetime | Purpose |
|------|----------|---------|
| `.reviews/validate/action.json` | One run | validate.py → report output |
| `configs/validate/*.yaml` | Permanent | Per-scope check definitions |

## Rules

- **This skill never edits files.** It is read-only.
- **FAIL blocks progression.** `/scaffold-approve-*`, `/scaffold-implement`, and `utils.py complete` check validation status.
- **Scopes are independent.** `--scope systems` only runs system checks.
- **`--scope all` includes cross-cutting and cross-layer checks** that don't run on individual scopes.
- **Heuristic checks are advisory.** They may produce false positives — labeled `[ADVISORY]`.
