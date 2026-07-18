---
name: report-pollinator-learning
description: Turn a Go preference, rough edge, or lesson discovered during project work into a concise handoff message for Pollinator Go maintainers. Use when the user explicitly wants to capture what was learned in another repository and paste it into a Pollinator Go maintenance conversation.
---

# Report Pollinator Learning

Produce one concise, self-contained message that the user can paste into another conversation.

## Understand the learning

Review the conversation to identify the concrete situation, the implementation or agent behavior the user disliked, the behavior the user prefers, and the reason for that preference.

Inspect relevant project files only when needed to represent the situation accurately. If the user's conclusion or rationale remains materially unclear, ask a focused question before writing the report.

## Write the report

Give the learning a descriptive title. Explain what happened, state the user's preferred behavior, and preserve the reasoning that led to it.

Include the smallest relevant code excerpt whenever the learning concerns code shape, placement, naming, abstraction, or another implementation-level distinction. Prefer actual before-and-after code when both are available. If only the unwanted implementation exists, include that excerpt and describe the preferred change without inventing project code.

Code may be omitted when the learning is conceptual and prose communicates it completely. Include other context only when it was important to the conclusion. Choose whatever organization communicates the particular learning most naturally.

Keep the report as short as possible without making the receiving agent reconstruct the original conversation.

## Stay focused

Report only the problem at hand and the conclusion actually reached.

Do not inspect or interpret existing Pollinator Go guidance, suggest which skill or reference should change, rewrite the preference as final upstream wording, or infer adjacent rules, exceptions, or consequences that were not part of the discussion. Omit project history that does not help explain the learning.

Do not modify files or retain the report as an artifact.

## Deliver the report

Return only the copyable report, without introductory or closing commentary.
