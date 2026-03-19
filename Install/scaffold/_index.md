# Scaffold — Master Index

> **Purpose:** Single entry point for document retrieval. Read this file first.

## Retrieval Protocol

1. Start here (`_index.md`) to locate the correct directory.
2. Open the directory's `_index.md` to find the specific document.
3. Read only the document(s) you need — avoid loading entire directories.
4. If two documents conflict, the higher-authority document wins (see [doc-authority.md](doc-authority.md)).

## Directory Map

| Directory | Layer | Contents |
|-----------|-------|----------|
| [design/](design/_index.md) | Canon | What the game is — vision, style, glossary, systems, interfaces, authority, states |
| [reference/](reference/_index.md) | Reference | Canonical data tables — signals, entities, resources, balance |
| [engine/](engine/_index.md) | Implementation | How we build in the target engine — best practices, constraints |
| [inputs/](inputs/_index.md) | Canon | Input action map, bindings, navigation rules |
| [theory/](theory/_index.md) | Reference | Background reading — never canonical |
| [phases/](phases/_index.md) | Scope | Phase gates and milestones |
| [specs/](specs/_index.md) | Behavior | Atomic behavior definitions |
| [tasks/](tasks/_index.md) | Execution | Executable implementation steps |
| [decisions/](decisions/_index.md) | History | ADRs, known issues, design debt, playtest feedback, cross-cutting findings, code reviews, revision logs, triage logs |
| [slices/](slices/_index.md) | Integration | Vertical slice contracts |
| [templates/](templates/_index.md) | Meta | Document templates for all ID'd types and engine docs |
| [decisions/review/](decisions/review/_index.md) | Tooling | Adversarial review logs from `/scaffold-iterate` |
| [art/](art/_index.md) | Content | Generated art from art skills (`/scaffold-art-concept`, `/scaffold-art-ui-mockup`, etc.) |
| [audio/](audio/_index.md) | Content | Generated audio from audio skills (`/scaffold-audio-music`, `/scaffold-audio-sfx`, etc.) |
| [tools/](tools/_index.md) | Tooling | Scripts and utilities for the pipeline |

## Key Files

- [WORKFLOW.md](WORKFLOW.md) — Step-by-step recipe for the full pipeline
- [SKILLS.md](SKILLS.md) — Man-page reference for all 72 slash commands
- [doc-authority.md](doc-authority.md) — Precedence rules (read when conflicts arise)
- [README.md](README.md) — How to use this scaffold

## ID System

| Entity | Format | Example |
|--------|--------|---------|
| System | SYS-### | SYS-001 |
| Phase | P#-### | P1-001 |
| Spec | SPEC-### | SPEC-001 |
| Task | TASK-### | TASK-001 |
| ADR | ADR-### | ADR-001 |
| Slice | SLICE-### | SLICE-001 |
| Playtester Feedback | PF-### | PF-001 |
| Code Review | CR-### | CR-001 |
| Known Issue | KI-### | KI-001 |
| Design Debt | DD-### | DD-001 |
| Cross-Cutting Finding | XC-### | XC-001 |

IDs are permanent. They never change even if the document is renamed.
