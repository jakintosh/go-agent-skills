---
name: write-git-commit-messages
description: Write and review Git commit messages in Studio Pollinator's house style. Use when preparing, revising, evaluating, or proposing a commit subject or body, including choosing among added, changed, fixed, refactor, and removed.
---

# Write Git Commit Messages

Describe the exact change set in a lowercase, plainspoken subject and a body proportional to the change. Base the message on the diff or other concrete evidence; do not describe intended work that is absent from the commit.

## Write the subject

Use this form:

```text
<kind>: <plain-language result>
```

Choose one kind according to the commit's dominant intent:

- `added` introduces a capability, supported case, interface, test suite, documentation, infrastructure, or another meaningful new thing.
- `changed` intentionally alters existing behavior, configuration, dependencies, naming, or presentation. Use it as the general category when no narrower kind fits.
- `fixed` corrects defective or unintentionally incomplete behavior. Describe the corrected outcome rather than only the symptom.
- `refactor` reorganizes implementation, responsibilities, naming, or package boundaries without intentionally changing externally observable behavior.
- `removed` primarily deletes a capability, dependency, compatibility path, or obsolete code.

Use `initial commit` without a prefix only for the exceptional first commit. Fold `updated` into `changed`; do not introduce Conventional Commit scopes, exclamation marks, or additional synonyms unless the repository clearly requires them.

Begin the description with lowercase, use a past-tense phrase, and omit the trailing period. State the useful result rather than the activity performed. Use single quotes around identifiers, commands, package paths, and route names when quoting them improves clarity.

Keep the subject focused on one coherent outcome. When the change has several details, summarize their shared purpose in the subject and explain the important parts in the body.

## Preserve the useful story

Scale the body to the context worth preserving, not the number of changed files or lines. Ask what important information would be difficult to recover from the diff later.

Omit the body when the subject and diff tell the complete story. Use one or two sentences when only one small piece of context is missing. Use multiple paragraphs when the change has meaningful background, decisions, tradeoffs, or consequences that need to remain understandable.

A small diff may justify a substantial body. A large mechanical diff may justify none. Write the shortest body that preserves the important story.

The body may explain what changed, why it changed, what prompted it, a decision or rejected alternative, a tradeoff, a compatibility constraint, or a meaningful consequence. Include only the parts that help a future reader. Do not force every body to begin with rationale when a direct account of the completed work is more useful.

## Write the body plainly

Write the body as a brief retrospective account. Use past tense and first-person plural for completed work, such as “we added,” “we changed,” or “we chose.” Describe earlier conditions in the past tense. Use present tense only for a state or consequence that remains true after the commit.

Avoid imperatives such as “add,” “require,” or “validate”; they read like instructions rather than history. Name the affected component when that helps orient the reader. Give distinct changes or ideas separate sentences instead of forcing them into one contrast or abstraction.

Use short sentences with one main idea each. Prefer common words, concrete nouns, and active verbs. For a longer explanation, add sentences and paragraphs instead of making the grammar more complicated. Let each paragraph handle one part of the story, such as background, decision, or consequence.

Read the body once and remove any sentence that does not add information.

Do not repeat the subject, narrate routine edits, or inventory changed files. Omit routine formatting, lint, and test results. Mention verification only when its result or scope materially affects confidence in the change. Never claim verification that did not occur.

Prefer prose. Use bullets only when three or more independently important parts would be harder to understand as a paragraph.

## Return the message

When writing or proposing a commit message, return a copy-and-pasteable `git commit -m <message>` command without an introduction. Put the entire command inside a triple-backtick `sh` block. Use one double-quoted, potentially multiline argument and escape double quotes, dollar signs, backticks, and backslashes when needed so the command is safe for the user's shell.

For a message with a body, use this template:

```sh
git commit -m "<kind>: <plain-language result>

<plain retrospective account with the context worth preserving>"
```

For a trivial change with no body, keep the command on one line:

```sh
git commit -m "<kind>: <plain-language result>"
```

For example, a small change with little hidden context could produce:

```sh
git commit -m "changed: clarified cache defaults and startup output

In the cache settings, we documented that a zero lifetime disables expiration.
In the startup output, we renamed the cache status to match that setting."
```

For example, a small diff with important context could produce:

```sh
git commit -m "fixed: rejected tokens without an audience

Tokens without an audience could be accepted by more than one service. We now
reject missing audiences during decoding so every token has an explicit target."
```

For example, a larger change could produce:

```sh
git commit -m "changed: separated config writes from runtime resolution

The previous loader wrote missing config during ordinary startup. That made a
read path mutate user-authored state and made startup failures harder to reason
about.

We moved those writes into the explicit config initialization flow. Runtime
resolution is now read-only, while existing config paths remain compatible."
```
