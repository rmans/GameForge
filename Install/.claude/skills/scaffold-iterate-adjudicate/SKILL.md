---
name: scaffold-iterate-adjudicate
description: "Judge one reviewer issue during adversarial review. Reads action.json for the issue, section content, and layer rules. Decides accept/reject/escalate/pushback. Writes result.json."
argument-hint: (called by /scaffold-iterate dispatcher — not user-invocable)
allowed-tools: Read, Write, Grep, Glob
---

# Adjudicate One Issue

This skill is called by the `/scaffold-iterate` dispatcher. It receives one issue from an external reviewer and makes a judgment call.

## Input

Read `.reviews/iterate/action.json`. It contains:

```json
{
  "action": "adjudicate",
  "session_id": "...",
  "pass": "l3|l2|l1",
  "section": "### Purpose",
  "issue": {
    "severity": "HIGH|MEDIUM|LOW",
    "section": "Purpose",
    "description": "The purpose statement is too vague — it doesn't name what state this system uniquely owns.",
    "suggestion": "Rewrite to: 'Owns construction lifecycle state — what's being built, build progress, and resource reservations.'"
  },
  "section_content": "... the actual content of the section being reviewed ...",
  "target_file": "design/systems/SYS-005-construction.md",
  "layer": "systems",
  "rules": ["Systems describe BEHAVIOR, not IMPLEMENTATION", "..."],
  "context_summary": "... relevant context from design doc, authority, etc ...",
  "resolved_root_causes": ["...", "..."],
  "exchange_count": 0,
  "max_exchanges": 5
}
```

## Process

1. **Read the issue** — understand what the reviewer is claiming.

2. **Read the section content** — understand what's actually written.

3. **Check the review lock** — is this issue's root cause already in `resolved_root_causes`? If yes, reject as "previously resolved."

4. **Evaluate against layer rules** — does the issue respect document authority? Is it in scope for this layer?

5. **Decide one outcome:**

   - **Accept** — the issue is valid and the suggestion improves the document.
     - Write a clear fix description that `/scaffold-iterate-apply` can act on.
     - Be specific: "Rewrite ### Purpose to: '...'" not "make it clearer."

   - **Reject** — the issue is wrong, out of scope, or contradicted by higher-authority docs.
     - Include reasoning that references specific documents or rules.

   - **Escalate** — requires user judgment, unclear authority, or genuinely ambiguous.
     - Include the question for the user with concrete options (a/b/c).

   - **Pushback** — you disagree but want to counter-argue before deciding.
     - Write a specific counter-argument. Not "I disagree" — explain why with evidence.
     - Only pushback if you have a substantive counter-point. Don't pushback to be thorough.

6. **Check exchange count** — if this is a pushback response and `exchange_count >= max_exchanges`, you must decide (accept, reject, or escalate). No more pushback allowed.

## Output

Write `.reviews/iterate/result.json`:

```json
{
  "outcome": "accept|reject|escalate|pushback",
  "reasoning": "The reviewer is correct — Purpose doesn't name unique state...",
  "fix_description": "Rewrite ### Purpose to: 'Owns construction lifecycle...'",
  "counter_argument": "...",
  "escalation_question": "...",
  "escalation_options": ["a) ...", "b) ...", "c) ..."]
}
```

Only include fields relevant to the outcome:
- `accept` → `reasoning` + `fix_description`
- `reject` → `reasoning`
- `escalate` → `reasoning` + `escalation_question` + `escalation_options`
- `pushback` → `reasoning` + `counter_argument`

## Adjudication Principles

- **Project documents and authority order win.** Higher-ranked documents decide disputes.
- **Never blindly accept.** Every issue gets evaluated against project context.
- **Never half-accept.** Choose exactly one outcome.
- **Pushback is expected and healthy.** But only when you have a real counter-point.
- **Practicality check.** Reject changes that increase rigidity without improving usability.
- **Don't invent content.** If the issue is "behavior is missing," flag the gap — don't write new behavior.
- **Ownership changes always escalate.** Moving state between systems requires user confirmation.
- **Layer-specific rules from the action take precedence** over these general principles.

## What NOT to Do

- **Don't read the target file.** The section content is in the action.
- **Don't edit any files.** That's `/scaffold-iterate-apply`'s job.
- **Don't run scope checks.** That's `/scaffold-iterate-scope-check`'s job. iterate.py will route there if needed.
- **Don't worry about what comes next.** The dispatcher handles sequencing.
