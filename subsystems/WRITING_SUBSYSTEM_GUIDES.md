# Writing Subsystem Guides

This document captures the working standard for how subsystem guides should be written in this style system.

It exists so future guides stay:

- focused
- consistent
- generic
- actually useful during implementation

## What a subsystem guide is

A subsystem guide explains how one specific architectural job should work.

Good examples:

- router composition
- config systems
- database adapters
- API tests
- server-rendered HTMX UI

A subsystem guide is not:

- a whole-project philosophy document
- a checklist
- a dump of rules from old docs
- a set of real-project excerpts

## The job-to-be-done test

A topic deserves a subsystem guide when a reader could reasonably ask:

- "How should we do this kind of thing here?"

And the answer needs all of these:

- a boundary
- a structure
- a canonical flow
- responsibilities by layer or file
- testing expectations
- anti-patterns

If a topic is too small for that, it probably belongs in foundations.

If a topic is just an implementation reminder, it probably belongs in a checklist.

## The main goal

A good subsystem guide should let a capable engineer implement the subsystem in the intended style without needing to reverse-engineer the examples repository or reread the whole style system.

That means the guide should answer:

- when to use this pattern
- what owns what
- what the normal shape looks like
- what not to do

## What to optimize for

Optimize for:

- clarity over completeness theater
- transferability across projects
- explicit boundaries
- generic examples
- scanability

Do not optimize for:

- exhaustive historical context
- proving every claim with a long real-project tour
- covering every edge case up front

## Recommended structure

Most subsystem guides should use roughly this structure:

1. title and one-paragraph purpose
2. when to use this guide
3. non-goals, if there are plausible scope confusions
4. core rules
5. canonical shape
6. canonical flow
7. responsibilities and boundaries
8. testing expectations
9. anti-patterns
10. generic example
11. related guides

Not every guide needs every heading, but this is the default shape.

## How to write a good Non-goals section

Only include `Non-goals` when it helps a reader avoid a plausible misunderstanding.

Good non-goals:

- adjacent concerns a reader might expect this guide to cover
- things with a real boundary relationship to the subsystem
- details that vary intentionally from project to project

Bad non-goals:

- random unrelated topics
- obvious things no one would expect the guide to cover
- filler added because every guide "should" have a non-goals section

If there are no realistic confusion points, omit the section entirely.

## How to keep guides narrow

A subsystem guide should teach one subsystem, not re-teach the entire style system.

If a guide starts spending too much time on:

- overall project layout
- general coding philosophy
- unrelated subsystem behavior

it is getting too broad.

Link to related guides instead of re-explaining shared principles in full.

## What to capture from source material

When extracting from old docs or temporary examples, preserve:

- the actual rules
- the ownership model
- the recurring flow shape
- the reasons the pattern works

Do not preserve:

- project-specific names
- temporary migration framing
- historical accidents
- real production examples as the final teaching material

## Generic examples

Subsystem guides should use concise generic examples.

A good generic example should:

- feel realistic
- show the intended shape clearly
- use neutral names like `documents`, `projects`, `settings`, or `themes`
- be short enough to scan in one pass

A generic example should not:

- copy a real project too literally
- include unnecessary domain detail
- become a second full tutorial

## How to use the matrix

The rule inventory matrix is the extraction control document.

When writing a subsystem guide:

1. find the rules owned by that subsystem
2. separate `required` rules from `default` rules
3. decide what needs explanation versus a short statement
4. write the guide from the matrix, not from the old docs directly

That helps keep the new guides cleaner than the source material.

## Tone and style

A good subsystem guide should sound:

- confident
- practical
- architectural
- specific without being brittle

It should not sound:

- academic
- defensive
- overloaded with caveats
- like a migration note

## What to include explicitly

These are usually worth stating plainly:

- ownership boundaries
- where precedence or resolution happens
- where composition happens
- what the main entry points are
- what gets tested
- what counts as an anti-pattern

These are often more valuable than large code examples.

## Signs a guide is working

You know a subsystem guide is in good shape when:

- it is easy to skim
- the subsystem boundary feels obvious
- the examples are generic but convincing
- a reader could implement a first pass from the guide alone
- it does not rely on temporary source repos for comprehension

## Signs a guide needs revision

- the guide keeps saying "see project X"
- the guide uses lots of real names from production code
- the guide explains several subsystems at once
- the non-goals section feels random
- the example is more memorable than the rule
- the document reads like a cleaned-up migration note

## Working rule for future drafts

When in doubt:

- make the boundary clearer
- shorten the example
- remove unrelated material
- prefer one strong canonical shape over several weak variants
