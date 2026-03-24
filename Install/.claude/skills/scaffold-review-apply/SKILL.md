---
name: scaffold-review-apply
description: "Apply accepted changes to target files during document review. Reads action.json for the change list. Edits files. Writes result.json. Shared by /scaffold-iterate and /scaffold-fix."
argument-hint: (called by review dispatchers — not user-invocable)
allowed-tools: Read, Edit, Write, Grep, Glob
---

# Apply Accepted Changes

This skill is called by the `/scaffold-iterate` dispatcher after a pass level completes (L3, L2, or L1). It receives a batch of accepted issues and applies the fixes.

## Input

Read `.reviews/iterate/action.json`:

```json
{
  "action": "apply",
  "session_id": "...",
  "target_file": "design/systems/SYS-005-construction.md",
  "editable_files": ["design/systems/SYS-005-construction.md"],
  "pass": "l3",
  "changes": [
    {
      "section": "### Purpose",
      "fix_description": "Rewrite ### Purpose to: 'Owns construction lifecycle state — what's being built, build progress, and resource reservations for in-progress construction.'",
      "issue_description": "Purpose is too vague — doesn't name unique state.",
      "severity": "HIGH"
    },
    {
      "section": "### Non-Responsibilities",
      "fix_description": "Add specific exclusion: 'Does not own resource availability — owned by ResourceSystem (SYS-003).'",
      "issue_description": "Non-Responsibilities are generic.",
      "severity": "MEDIUM"
    }
  ]
}
```

## Process

1. **Read the target file** to understand current content.

2. **For each change**, in section order (top to bottom in the document):
   a. Find the section in the document.
   b. Read the fix description — it describes WHAT to change, not the exact diff.
   c. Interpret the fix and make the edit using the Edit tool.
   d. Keep edits minimal — change what the fix describes, don't rewrite surrounding content.

3. **Only edit files in `editable_files`.** If a change targets a file not in the list, skip it and note the skip.

4. **Update the document's metadata:**
   - Set `> **Last Updated:**` to today's date.
   - Append a Changelog entry: `- YYYY-MM-DD: [brief description] (ITERATE-[layer]-[target]-YYYY-MM-DD).`

## Output

Write `.reviews/iterate/result.json`:

```json
{
  "applied": 2,
  "skipped": 0,
  "changes": [
    {
      "section": "### Purpose",
      "action": "rewritten",
      "summary": "Replaced vague purpose with specific owned-state description."
    },
    {
      "section": "### Non-Responsibilities",
      "action": "added",
      "summary": "Added ResourceSystem exclusion."
    }
  ],
  "files_modified": ["design/systems/SYS-005-construction.md"],
  "skipped_changes": []
}
```

## Edit Principles

- **Minimal edits.** Change what the fix describes. Don't "improve" surrounding content.
- **Preserve voice.** Match the existing document's tone and style.
- **Don't invent content.** If the fix says "add specific exclusion" but doesn't say what, use the issue description for guidance. If still unclear, describe what you wrote in the result so it can be reviewed.
- **Section order.** Apply top-to-bottom to avoid offset issues with multiple edits.
- **Don't reformat.** Don't change whitespace, table alignment, or heading levels unless the fix specifically requires it.

## What NOT to Do

- **Don't adjudicate.** These changes were already accepted. Apply them.
- **Don't run scope checks.** Already done.
- **Don't add commentary or annotations** to the document ("// Fixed per review").
- **Don't edit files outside `editable_files`.**
