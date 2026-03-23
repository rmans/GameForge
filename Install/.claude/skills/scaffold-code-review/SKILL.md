---
name: scaffold-code-review
description: Adversarial code review using an external LLM reviewer. File-scope (default) for pipeline use, system-scope for manual audits. Bounded edits with early stopping.
argument-hint: <file-path or system-name> [--scope file|system] [--iterations N] [--topic N] [--focus "..."] [--max-exchanges N]
allowed-tools: Read, Edit, Write, Grep, Glob, Bash, Agent
---

# Adversarial Code Review

Run an adversarial code review using an external LLM reviewer. Each topic gets its own back-and-forth until consensus. Edits are bounded to the resolved target set. The caller owns post-review build verification.

## Scopes

| Scope | Default From | Purpose | Edit Boundary |
|-------|-------------|---------|---------------|
| `file` | scaffold-implement-task | Correctness, engine patterns, performance, maintainability, local structure | Target file only — paired file is read-only context |
| `system` | Manual invocation | Cross-file architecture, ownership boundaries, domain design, signal flow, lifecycle | Only files resolved in Step 1 for that system — no edits outside the resolved set |

## Topics

Topics are ordered by priority — correctness first, structure last.

| # | Topic | What It Evaluates | File Scope | System Scope |
|---|-------|-------------------|------------|--------------|
| 1 | Correctness | Happy-path behavior, edge cases, invalid input handling, state corruption, lifecycle bugs, signal ordering, off-by-one / bounds / null issues | Full | Full |
| 2 | Architecture | Authority ownership, single-writer discipline, dependency direction, boundary leaks, signal misuse, orchestrator violations, cross-system coupling | Skip by default — include only when file is boundary-relevant (orchestrator, registration, wiring) | Full |
| 3 | Engine Correctness | Node lifecycle, signal connection patterns, resolution timing, ClassDB bindings, memory ownership, GDExtension conventions, scene integration | Full | Full |
| 4 | Performance | Tick cost, scan patterns, allocation in hot paths, repeated work, early exits, cost vs. expected scale — focused on real hot-path risk, not speculative micro-optimization | Full | Full |
| 5 | Domain Design | State transitions, recovery behavior, workflow logic, domain modeling, behavior legibility and stability | Skip by default — include only when file contains meaningful behavior logic (state machines, processing pipelines, multi-step workflows) | Full |
| 6 | Maintainability | Growth trajectory, function complexity, API clarity, implicit behavior, comment quality where it matters, extensibility risk | Full | Full |
| 7 | Code Organization | File/class/function structure, header/impl split, naming coherence, file placement, whether the file should be split | Full | Full |

In file scope, topics marked "Skip" may still be reviewed if `--topic` explicitly selects them. The default behavior is to skip them as not meaningfully applicable at file granularity.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `file-path` | Yes | — | Path to a code file, or a system name (e.g., `task_system`, `power_system`) |
| `--scope` | No | `file` | `file` for single-file review (pipeline default), `system` for full system review (manual audits) |
| `--iterations` | No | 10 | Maximum full review passes. Stops early on convergence — if a pass produces no new issues, iteration ends. |
| `--topic` | No | scope default | Review only a specific topic (1-7). Overrides scope-based topic selection. |
| `--focus` | No | — | Narrow the review within each topic to a specific concern |
| `--max-exchanges` | No | 5 | Maximum back-and-forth exchanges per topic |

## Steps

### 1. Resolve Target Files

**If `--scope file` (default):**

The argument is a single file path. This is the **target file** — the only file edits may be applied to.

Identify the **context pair:**
- If target is `.cpp`: load the matching `.h` as read-only context.
- If target is `.h`: load the matching `.cpp` as read-only context.

If no natural pair exists for the target file (e.g., `register_types.cpp`, `game_manager.gd`), continue with the target file alone plus scope-appropriate context.

Result: One target file (mutable) and zero or one context files (read-only). The reviewer sees both but changes apply only to the target.

**If `--scope system`:**

Parse the argument and find all source files:

- If a file path: auto-discover related files (`.h` ↔ `.cpp`, split files like `*_hauling.cpp`).
- If a system name: Glob `src/gdextension/systems/{name}*.cpp` and `{name}*.h`.

Result: A primary file (the `.h` header) and all implementation files. All are passed to the Python script together. Edits may be applied to any file in this resolved set, but **no files outside it**.

If resolution finds zero files, report the error and stop. If the resolved files span multiple unrelated systems (no shared basename), report the ambiguity and stop.

### 2. Gather Context Files

Load context files appropriate to the review scope. Only include files that exist — skip missing ones silently.

**File scope — minimal context:**

Always include:

| Context File | Why |
|-------------|-----|
| Paired file (`.h` ↔ `.cpp`) | Read-only counterpart for the target file |
| `scaffold/decisions/design-debt.md` | Known compromises — reject issues matching these |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| System design doc (Glob `scaffold/design/systems/SYS-*{system_name}*.md`) | System-specific design intent — derive system name from file basename; if not derivable, skip silently |

Include `scaffold/design/architecture.md` only if the target file is an orchestrator, registration file (`register_types.cpp`), scene wiring file (`game_manager.gd`), or a system that emits/connects cross-system signals. Otherwise skip it — architecture context adds noise for internal implementation files.

**System scope — full context:**

| Context File | Why |
|-------------|-----|
| `scaffold/design/architecture.md` | Tick order, signal wiring, dependency graph, data flow rules |
| `scaffold/design/interfaces.md` | Cross-system contracts |
| `scaffold/design/authority.md` | Data ownership table |
| `scaffold/decisions/design-debt.md` | Known compromises — reject issues matching these |
| `scaffold/design/glossary.md` | Canonical terminology |
| `scaffold/doc-authority.md` | Document authority ranking, same-rank conflict resolution rules, deprecation protocol |
| System design doc (Glob `scaffold/design/systems/SYS-*{system_name}*.md`) | System-specific design intent |

### 3. Topic Loop

Determine which topics to review:
- If `--topic N` is provided, review only that topic (regardless of scope).
- If file scope: review topics 1, 3, 4, 6, 7 by default. Include topic 2 (Architecture) only when the file is boundary-relevant (orchestrator, registration, wiring). Include topic 5 (Domain Design) only when the file contains meaningful behavior logic (state machines, processing pipelines, multi-step workflows).
- If system scope: review all topics 1–7.

For each topic:

#### 3a. Request Review

```bash
python scaffold/tools/code-review.py review <primary-file> \
    --topic N \
    --iteration M \
    --files <impl1.cpp> <impl2.cpp> ... \
    --context-files <context1> <context2> ... \
    [--focus "<value>"]
```

Parse JSON output. If `"error"` key, report and stop.

Output: `## Topic N: [Name] — Score: X/10`

#### 3b. Inner Loop — Evaluate Issues

For each issue:

1. **Read the relevant code section** before evaluating.
2. **Classify** using explicit decision criteria:

**AGREE** — apply the change — when ALL of these are true:
- Issue is factually correct about the code
- Issue is in scope for the current review mode
- Fix aligns with project architecture and conventions
- Fix is worth making now (not speculative or premature)

**PUSHBACK** — reject the issue — when ANY of these are true:
- Issue is factually wrong about what the code does
- Issue matches an entry in `design-debt.md` (known compromise)
- Issue is out of scope for current mode (e.g., cross-file edit in file scope)
- Issue conflicts with an explicit project decision (ADR, architecture.md, authority.md)
- Issue proposes edits outside the resolved target set
- Issue is cosmetic or stylistic with no functional impact

**PARTIAL** — accept the problem, propose a different fix — when:
- The underlying issue is real, but the suggested remediation is wrong, too broad, or too invasive
- Apply a narrower fix that addresses the root cause

3. **In file scope:** reject any change that targets the context pair file. Changes apply only to the target file.
4. **In system scope:** reject any change that targets files outside the resolved set from Step 1.
5. **Compose response**, write to temp file, send via `respond` command.
6. Continue exchanges up to `--max-exchanges`.

**Key rule:** Claude is the authority on this codebase. Ties go to Claude.

#### 3c. Request Consensus

```bash
python scaffold/tools/code-review.py consensus <primary-file> \
    --topic N \
    --iteration M
```

#### 3d. Apply Changes

For each accepted change:
- Read the relevant code file.
- Apply using Edit tool.
- **Enforce edit boundary:** only edit files within the resolved target set. No edits to context files, test files, docs, or files outside the system.
- If a fix requires out-of-boundary changes, log the need in the review report instead of applying.

#### 3e. Log Topic Results

Record: topic name, score, issues raised, resolutions (accepted/rejected/partial), changes applied.

#### 3f. Transition

Output: `### Topic N: [Name] — Final Score: X/10 | Issues: A raised, B accepted, C rejected`

Respect provider rate limits between external review calls.

### 4. Iterate

If `--iterations > 1`:
1. Check if the previous pass produced any accepted issues that resulted in code changes.
2. **If no code changes were applied in the previous pass, stop early** — the code is stable. Do not run additional passes.
3. If changes were applied, re-read source files and repeat the topic loop on updated code.
4. Track reappearing issues. If the same high-severity issue reappears in 2+ passes without acceptable resolution, flag it as **unresolved** in the final summary.

### 5. Create Review Log

Create `scaffold/decisions/code-review/CR-###-{name}.md` (assign the next sequential CR-### ID):

```markdown
# CR-###: {name}

## Review Info
| Field | Value |
|-------|-------|
| Files | `file1.h`, `file1.cpp`, ... |
| Scope | file / system |
| Provider | [OpenAI/Anthropic] |
| Model | [model name] |
| Date | [YYYY-MM-DD] |
| Iterations | [N completed / M max] |
| Early stop | [Yes — stable after pass N / No] |

## Topic Scores

| # | Topic | Score | Issues | Accepted | Rejected |
|---|-------|-------|--------|----------|----------|
| 1 | Correctness | X/10 | N | N | N |
| ... | ... | ... | ... | ... | ... |

**Overall Score: X/10**

## Topic Details
<!-- Per-topic issues, discussion, changes, rejections -->

## Unresolved Issues
<!-- High-severity issues that reappeared across passes without resolution -->

## Final Summary
- **Total issues found:** [N]
- **Accepted:** [N]
- **Rejected:** [N]
- **Code changes applied:** [N]
- **Files changed:** [list or "none"]
```

Update `scaffold/decisions/code-review/_index.md`.

### 6. Report

```
## Code Review Complete: {name}

| Topic | Score | Issues | Accepted | Rejected |
|-------|-------|--------|----------|----------|
| ... | ... | ... | ... | ... |

**Overall: X/10**
**Scope:** file / system
**Iterations:** N completed / M max [early stop: yes/no]
**Changes applied:** N code changes
**Unresolved:** [count or "none"]
**Review log:** scaffold/decisions/code-review/CR-###-{name}.md
```

## Rules

- **Claude is the authority on this codebase.** Ties go to Claude. The reviewer is an outsider with no project context beyond what's provided.
- **Edit boundary is enforced.** File scope: target file only. System scope: resolved file set only. Never edit context files, test files, docs, or out-of-system files. Log out-of-boundary needs instead of applying.
- **Never blindly accept.** Evaluate every issue against project context using the AGREE/PUSHBACK/PARTIAL criteria.
- **Build verification is the caller's responsibility.** This skill applies edits but does not rebuild or run tests. The parent skill (`/scaffold-implement` Step 7) handles post-review verification.
- **Pushback is expected and healthy.** The value is in the discussion, not automatic acceptance.
- **One topic at a time.** Complete the full review → discuss → consensus cycle before moving on.
- **Early stop on stability.** If a pass produces no code changes, do not run additional passes regardless of remaining iteration budget.
- **Design debt is not a bug.** Reject issues matching `design-debt.md` entries and reference the DD-### entry.
- **Respect provider rate limits** between external review calls.
- **Clean up temporary files** used for `--message-file` after each exchange.
- **Read before evaluating.** Always read the relevant code section before agreeing or pushing back on an issue.
