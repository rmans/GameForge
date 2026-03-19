# Templates — Index

> **Purpose:** Document templates for all ID'd types and engine docs. Templates live here only — never in content directories.

## Available Templates

| Step | Template | ID Format | Target Directory |
|------|----------|-----------|-----------------|
| S1 | [design-doc-template.md](design-doc-template.md) | (singleton) | [design/](../design/) |
| S2 | [system-template.md](system-template.md) | SYS-### | [design/systems/](../design/systems/_index.md) |
| S8–S9 | [phase-template.md](phase-template.md) | P#-### | [phases/](../phases/_index.md) |
| S10–S12 | [spec-template.md](spec-template.md) | SPEC-### | [specs/](../specs/_index.md) |
| S10–S12 | [task-template.md](task-template.md) | TASK-### | [tasks/](../tasks/_index.md) |
| S10–S12 | [slice-template.md](slice-template.md) | SLICE-### | [slices/](../slices/_index.md) |
| Any | [decision-template.md](decision-template.md) | ADR-### | [decisions/](../decisions/_index.md) |
| S13 | [playtest-session-template.md](playtest-session-template.md) | PT-YYYY-MM-DD | [decisions/](../decisions/_index.md) |

## Architecture & Reference Templates (Step 3)

| Step | Template | ID Format | Target Directory |
|------|----------|-----------|-----------------|
| S3 | [architecture-template.md](architecture-template.md) | (singleton) | [design/](../design/) |
| S3 | [authority-template.md](authority-template.md) | (singleton) | [design/](../design/) |
| S3 | [interfaces-template.md](interfaces-template.md) | (singleton) | [design/](../design/) |
| S3 | [state-transitions-template.md](state-transitions-template.md) | (singleton) | [design/](../design/) |
| S3 | [entity-components-template.md](entity-components-template.md) | (singleton) | [reference/](../reference/) |
| S3 | [resource-definitions-template.md](resource-definitions-template.md) | (singleton) | [reference/](../reference/) |
| S3 | [signal-registry-template.md](signal-registry-template.md) | (singleton) | [reference/](../reference/) |
| S3 | [balance-params-template.md](balance-params-template.md) | (singleton) | [reference/](../reference/) |
| S3 | [enums-and-statuses-template.md](enums-and-statuses-template.md) | (singleton) | [reference/](../reference/) |

## Visual & UX Templates (Step 5)

| Step | Template | ID Format | Target Directory |
|------|----------|-----------|-----------------|
| S5 | [style-guide-template.md](style-guide-template.md) | (singleton) | [design/](../design/) |
| S5 | [color-system-template.md](color-system-template.md) | (singleton) | [design/](../design/) |
| S5 | [ui-kit-template.md](ui-kit-template.md) | (singleton) | [design/](../design/) |
| S5 | [interaction-model-template.md](interaction-model-template.md) | (singleton) | [design/](../design/) |
| S5 | [feedback-system-template.md](feedback-system-template.md) | (singleton) | [design/](../design/) |
| S5 | [audio-direction-template.md](audio-direction-template.md) | (singleton) | [design/](../design/) |

## Engine Templates (Step 4)

| Step | Template | Target Directory |
|------|----------|-----------------|
| S4 | [engine-coding-template.md](engine-coding-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-ui-template.md](engine-ui-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-input-template.md](engine-input-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-scene-architecture-template.md](engine-scene-architecture-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-performance-template.md](engine-performance-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-simulation-runtime-template.md](engine-simulation-runtime-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-save-load-template.md](engine-save-load-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-ai-task-execution-template.md](engine-ai-task-execution-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-data-content-pipeline-template.md](engine-data-content-pipeline-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-localization-template.md](engine-localization-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-post-processing-template.md](engine-post-processing-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-implementation-patterns-template.md](engine-implementation-patterns-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-debugging-template.md](engine-debugging-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-build-test-template.md](engine-build-test-template.md) | [engine/](../engine/_index.md) |
| S4 | [engine-asset-import-pipeline-template.md](engine-asset-import-pipeline-template.md) | [engine/](../engine/_index.md) |

## Tracking & Decision Templates

| Step | Template | ID Format | Target Directory |
|------|----------|-----------|-----------------|
| Any | [decision-template.md](decision-template.md) | ADR-### | [decisions/architecture-decision-record/](../decisions/architecture-decision-record/_index.md) |
| Any | [known-issue-entry-template.md](known-issue-entry-template.md) | KI-### | [decisions/known-issues/](../decisions/known-issues/_index.md) |
| Any | [design-debt-entry-template.md](design-debt-entry-template.md) | DD-### | [decisions/design-debt/](../decisions/design-debt/_index.md) |
| S13 | [playtest-feedback-entry-template.md](playtest-feedback-entry-template.md) | PF-### | [decisions/playtest-feedback/](../decisions/playtest-feedback/_index.md) |
| Any | [cross-cutting-finding-entry-template.md](cross-cutting-finding-entry-template.md) | XC-### | [decisions/cross-cutting-finding/](../decisions/cross-cutting-finding/_index.md) |

## Pipeline & Reporting Templates

| Step | Template | ID Format | Target Directory |
|------|----------|-----------|-----------------|
| S10–S12 | [triage-log-template.md](triage-log-template.md) | TRIAGE-[SLICE/SPECS]-### | [decisions/triage-log/](../decisions/triage-log/_index.md) |
| S7/S14 | [revision-log-template.md](revision-log-template.md) | REVISION-[layer]-YYYY-MM-DD | [decisions/revision-log/](../decisions/revision-log/_index.md) |
| S13 | [code-review-log-template.md](code-review-log-template.md) | CR-### | [decisions/code-review/](../decisions/code-review/_index.md) |
| Any | [review-template.md](review-template.md) | ITERATE/FIX/REVIEW-* | [decisions/review/](../decisions/review/_index.md) |

## Usage

1. Copy the template to the target directory.
2. Rename it with the next sequential ID (e.g., `SYS-001-player-movement.md`).
3. Fill in all sections.
4. Register the new document in the target directory's `_index.md`.

For engine templates, the seeding skill replaces `[Engine]` with the selected engine name and pre-fills engine-specific conventions.
