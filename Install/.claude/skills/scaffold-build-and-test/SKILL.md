---
name: scaffold-build-and-test
description: Pure verification gate — build, lint, regression tests, unit tests. Reports pass/fail without fixing code.
argument-hint: [--files <file...>] [--skip-unit] [--skip-lint]
allowed-tools: Read, Grep, Glob, Bash
---

# Build and Test

Pure verification gate. Builds the project and runs all test suites. Reports pass/fail with details. **Does not fix code** — the caller is responsible for interpreting results and making corrections.

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| --files | No | — | Source files changed by the current task (used for lint targeting) |
| --skip-unit | No | false | Skip unit tests |
| --skip-lint | No | false | Skip linting |

## Step 0 — Preflight Checks

Before running any step, verify that required tools and files exist. Prerequisites are split into **required** (failure stops the gate) and **optional** (missing means skip that step).

### Required

1. **Engine or build tool:** Verify the project's build tool or engine executable exists. Check project files to determine the engine (e.g., `project.godot` → Godot, `*.csproj`/`*.sln` → .NET/Unity, `*.uproject` → Unreal, `Makefile`/`CMakeLists.txt` → C/C++). If the engine executable or build tool cannot be found, **fail preflight**.
2. **Build command:** Verify the project's build system is available (e.g., `scons`, `dotnet`, `msbuild`, `make`, `cmake`). If missing, **fail preflight**.
3. **Test harness:** Verify the project's test entry point exists (e.g., a test scene, test runner script, or test configuration). If missing, record `Tests: FAIL (harness missing)` and set verdict to FAIL, then return immediately.

### Optional

1. **Unit test framework:** If `--skip-unit` is not set, verify the unit test framework is available. If missing, record `Unit Tests: SKIP (framework not installed)`.
2. **Linter:** If `--skip-lint` is not set, verify the project's linter is available on PATH. If missing, record `Lint: SKIP (linter not found)`.

If any **required** prerequisite is missing, record the failure in the output table, set verdict to FAIL, and return immediately — do not execute any steps. The caller must always receive a structured result.

## Step 1 — Build

Run the project's build command from the project root.

**PASS** if zero errors. **FAIL** if any compilation errors.

If the build fails, **stop**. Do not run subsequent steps — they depend on a successful build. Report the build failure and return.

## Step 2 — Lint

Skip if `--skip-lint` or if the linter is unavailable (per Step 0).

If `--files` was not provided, record `Lint: SKIP (no file list provided)`.

If `--files` was provided, filter the list to source files appropriate for the project's linter. If no lintable files remain after filtering, record `Lint: SKIP (no changed source files)`.

For each source file, run the linter.

**PASS** if every targeted file passes. **FAIL** if any file has lint issues.

Record per-file results.

## Step 3 — Regression Tests

If the test harness was missing in Step 0, this step is already recorded as FAIL. Do not run.

Run the project's regression/integration test suite.

**PASS** if all three conditions are met:
- Failed count = 0
- Error count = 0
- Warning count = 0

**FAIL** if any condition is not met.

Record: X passed, Y failed, Z errors, W warnings.

## Step 4 — Unit Tests

Skip if `--skip-unit` or if the unit test framework is missing (per Step 0).

Run the project's unit test suite.

**PASS** if zero test failures. **FAIL** if any test fails.

Record: X passed, Y failed.

## Output

Report all results in structured format:

```
## Verification Results

| Step | Result | Details |
|------|--------|---------|
| Build | PASS / FAIL | zero errors / N errors |
| Lint | PASS / FAIL / SKIP | N files clean (via --files) / N issues in M files / reason skipped |
| Regression | PASS / FAIL | X passed, 0 failed, 0 errors, 0 warnings / X passed, Y failed, Z errors, W warnings / harness missing |
| Unit Tests | PASS / FAIL / SKIP | X passed, 0 failed / X passed, Y failed / reason skipped |

**Verdict: PASS / FAIL**
```

The verdict is PASS only if every non-skipped step passed. Any FAIL in any step — including a missing test harness — makes the verdict FAIL.

If the verdict is FAIL, include the relevant error output (build errors, lint issues, test failures, warnings) so the caller has the information needed to fix the code.

## Rules

- **This skill is a verification gate, not a repair tool.** It runs checks and reports results. It never modifies code, fixes bugs, or retries failing steps. The caller (typically `/scaffold-implement`) is responsible for fixing issues and re-invoking this skill.
- **Build failure is a hard stop.** If the build fails, skip all subsequent steps — they cannot produce meaningful results without a successful build.
- **Missing test harness is a failure, not a skip.** The test suite is a core verification dependency. If the harness doesn't exist, the gate cannot verify correctness.
- **Report raw results.** Do not interpret whether failures are "pre-existing" or "new." Report what happened. The caller has the context to make that judgment.
- **Lint requires explicit file targets.** If `--files` was not provided and lint is not skipped, skip lint rather than guessing which files to check. The parent skill is responsible for passing the file list.
- **Skip gracefully for optional steps.** If the unit test framework or linter is missing, skip that step and note it in the output.
