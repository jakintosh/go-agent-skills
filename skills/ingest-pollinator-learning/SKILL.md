---
name: ingest-pollinator-learning
description: Evaluate a pasted Pollinator Go learning report, clarify the user's intent, and propose a minimal targeted guidance change for approval before editing. Use when maintaining the Pollinator Go repository from a report produced during work in another project.
---

# Ingest Pollinator Learning

Treat the pasted report as context for a maintenance decision, not as text to copy into the knowledge base.

## Investigate the report

Confirm that the current repository is the Pollinator Go source repository, then read the complete report, the repository-root `PRINCIPLES.md` and `CONTRIBUTING.md`, and the current guidance relevant to the concern.

Identify the skill and narrowest reference that own the concern. Determine whether the report reveals a missing rule, unclear rule, misleading example, routing problem, or preference that does not belong in shared guidance. Be willing to recommend no change when the existing guidance already expresses the preference or the learning is too project-specific to generalize.

## Check for contradictions

Search skills, references, principles, and examples for guidance that conflicts or meaningfully tensions with the reported preference. Consider direct contradictions and older rules whose rationale points toward a different design value.

Do not reject a new preference because it conflicts with existing guidance, and do not introduce contradictory rules silently. Explain the new preference, the conflicting guidance, and why they cannot remain unchanged together. Recommend the resolution that best reflects the user's apparent current preference while preserving a coherent knowledge base, then ask the user how to resolve the conflict.

Include every rule and example that must change in the eventual proposal.

## Resolve uncertainty

Use the repository to answer questions about existing guidance. Ask the user focused follow-up questions whenever uncertainty about their preference or intended scope could materially change the result.

Do not invent qualifications, exceptions, or broader principles to complete an underspecified report.

## Consider durable rationale

Retain enough rationale in a rule to clarify its purpose or resolve likely ambiguity, but do not preserve the full report.

Use `PRINCIPLES.md` as an editorial lens. Propose a separate principles change only when the report's rationale expresses a value that recurs across multiple areas of the knowledge base or materially helps reconcile conflicting guidance. Keep principles concise and cross-cutting, merge with an existing principle when possible, and never add one merely to memorialize a single report.

## Propose and pause

Before editing any file, present a brief interpretation of the learning, the files that should change, the exact proposed wording or other edits, and any existing content that would be replaced or removed.

Prefer the smallest instruction that will reliably guide future agents. For a simple convention, aim for one direct sentence. Add rationale, examples, qualifications, cross-references, or principles changes only when necessary.

Explicitly ask the user to approve, revise, or reject the proposal. Never edit a skill, reference, or principle before the user explicitly approves the exact proposed change, even when the change appears obvious.

## Apply the approved change

After approval, implement only the agreed change. Update the narrowest applicable reference. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, adjacent routing, or reference selection must change.

Do not preserve the pasted report in the repository. Do not expand the edit into nearby cleanup or additional conventions without proposing them separately.

Run the validation required by `CONTRIBUTING.md` in proportion to the change.

## Request sign-off

Show the resulting wording, changed files, and validation outcome, then ask for final sign-off.

If the user requests a materially different revision, present the revised wording before editing again. Do not commit or publish the change unless the user separately asks.

## Finish the ingestion

After final sign-off, explain concisely what changed and why. Then propose one copy-and-pasteable shell command that stages only the approved files and commits them:

```sh
git add <approved-files> && git commit -m "<kind>: <plain-language result>

<why the change was needed and the important shape of the solution>"
```

Choose `added`, `changed`, `fixed`, `refactor`, or `removed` according to the dominant intent. Write a lowercase, plainspoken, past-tense subject without a trailing period. Keep the body proportional to the change and use it to preserve the rationale from the report plus the important decision embodied by the approved guidance. Do not repeat the subject, inventory files, or claim validation that did not occur.

Use one double-quoted, potentially multiline `-m` argument. Escape double quotes, dollar signs, backticks, and backslashes when needed so the command is safe to paste into the user's shell. Shell-quote file paths when needed.

Inspect the current diff before proposing the command. Include only files whose unstaged changes belong entirely to the approved ingestion. If an affected file also contains unrelated work, disclose that and ask the user to resolve or stage it selectively instead of proposing a whole-file `git add` command that would include unrelated changes.

Do not run the proposed command. End the response with its `sh` code block.
