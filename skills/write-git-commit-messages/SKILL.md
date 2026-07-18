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

## Size the body to the change

For a substantive change, leave one blank line after the subject and write one or two compact paragraphs, normally 40–100 words. For a small change, use a sentence or two. Omit the body when the change is truly trivial and the subject already communicates everything a future reader would need to know.

Explain why the change was needed, then identify the most important shape of the solution: a design choice, ownership boundary, behavioral consequence, or tradeoff that the diff cannot explain by itself. Mention tests, compatibility, migration concerns, or known limitations when they materially help a future reader. Never claim verification that did not occur.

Do not repeat the subject, narrate routine edits, or inventory every changed file. Prefer prose. Use bullets only when three or more independently important parts would be harder to understand as a paragraph.

## Return the message

When writing or proposing a commit message, return a copy-and-pasteable `git commit -m <message>` command without an introduction. Put the entire command inside a triple-backtick `sh` block. Use one double-quoted, potentially multiline argument and escape double quotes, dollar signs, backticks, and backslashes when needed so the command is safe for the user's shell.

For a message with a body, use this template:

```sh
git commit -m "<kind>: <plain-language result>

<why the change was needed and the important shape of the solution>

<meaningful verification, compatibility impact, or limitation, when relevant>"
```

For a trivial change with no body, keep the command on one line:

```sh
git commit -m "<kind>: <plain-language result>"
```

For example, a substantive change could produce:

```sh
git commit -m "fixed: validate integration urls against audience

Integration URLs were accepted without confirming that their tokens were
intended for the Consent API. Validate the audience during decoding and reject
tokens that omit or target a different audience.

Newly issued tokens include the required audience, and coverage exercises
missing, invalid, and valid values."
```
