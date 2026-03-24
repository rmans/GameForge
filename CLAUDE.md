# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

GameForge is an installable overlay that helps Claude Code self-document and operate under a structured workflow/pipeline. Everything inside `Install/` is a scaffold that can be copied into any project to give Claude Code the context, conventions, and skills it needs to work effectively.

## Project Structure

```
/
├── Install/
│   ├── .claude/skills/   ← Claude Code skills
│   ├── scaffold/         ← Templates, conventions, tools
│   ├── CLAUDE.md         ← Install-specific instructions
│   └── README.md         ← Installation instructions
├── CLAUDE.md
├── gameforge.py      ← Installer script (contains VERSION)
├── README.md
├── .gitignore
└── .gitattributes
```

## Versioning

The project version lives in `gameforge.py` line 16 as `VERSION = "X.Y.Z"`. After making changes to any files under `Install/` (skills, templates, scaffold docs, tools), bump the version before committing:

- **Patch** (X.Y.**Z**) — bug fixes, wording tweaks, minor corrections
- **Minor** (X.**Y**.0) — new checks, new skill features, new templates, behavioral changes
- **Major** (**X**.0.0) — breaking changes to scaffold structure or skill contracts

## Cross-Reference Checklist

When adding or modifying a skill under `Install/.claude/skills/`, check and update these files as appropriate:

| File | When to update |
|------|---------------|
| `Install/scaffold/WORKFLOW.md` | New skill → add step entry. Changed behavior → update step description. Add to skill summary table. Update pipeline loop descriptions if the skill participates in a stabilization chain. |
| `Install/scaffold/SKILLS.md` | Always — add or update the skill's row in the skill index table. |
| `Install/README.md` | Always — add to the skill category list (Create, Fix, Iterate, Revise, etc.). |
| `Install/scaffold/doc-authority.md` | If the skill writes to scaffold docs → add to "Who writes" column. If it creates decision docs → add to Decision Influence Model table. |
| `Install/scaffold/decisions/revision-log/_index.md` | If the skill is a `revise-*` skill → add its layer to the index. |
| `Install/scaffold/templates/decision-template.md` | If the skill can trigger ADRs → add to "Triggered by" examples. |
| `Install/scaffold/templates/known-issue-entry-template.md` | If the skill can discover known issues → add to "Triggered by" examples. |
| `Install/scaffold/templates/code-review-log-template.md` | If the skill consumes code review drift → add a drift detection section. |
| `Install/.claude/skills/scaffold-revise-foundation/SKILL.md` | If the skill is a `revise-*` skill → update the dispatch table and the affected Step's skill chain. |
| `Install/.claude/skills/scaffold-validate/SKILL.md` | If the skill produces artifacts that validate should check → add checks. |
| `README.md` (root) | If adding a new skill → update skill count and add to category list. |
| `gameforge.py` | Always — bump VERSION. |
