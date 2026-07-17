---
name: design-go-public-packages
description: Guide deliberately public Go APIs. Use for design, implementation, debugging, testing, or review of pkg packages, exported compatibility surfaces, constructors, types, errors, or package documentation; exclude internal-only exports.
---

# Design Go Public Packages

Use this skill whenever code may become part of a supported external Go API. Treat public-package design as a product and compatibility decision, not a directory cleanup.

## Preserve the boundary

- Keep code in `internal/` unless external reuse is a real intended use case.
- Make each `pkg/` package small, purpose-built, understandable without the application, and supportable over time.
- Export the narrowest useful surface and document its contracts.
- Keep application-specific domain and infrastructure assumptions out of public types.
- Require package-level documentation and focused tests for the supported API.

## Consult the knowledge base

1. Inspect the candidate package, its current consumers, imports, exported surface, documentation, tests, and application coupling.
2. Determine whether external consumers and a stable compatibility boundary are genuinely intended.
3. Read [public-package-design.md](references/public-package-design.md) for every public-package task, including creation, modification, debugging, testing, and review.
4. Apply the decision test to each proposed export, not only to the package as a whole.
5. Prefer keeping uncertain or application-specific code internal.
6. Explain any material deviation when compatibility or ecosystem constraints require a broader surface.

## Include adjacent domains

- Consult the owning domain skill when public code wraps or mirrors application behavior; do not copy internal contracts into `pkg/` by default.
- Consult [API guidance](../work-with-go-http-apis/SKILL.md) when the public package is an HTTP client or shares a versioned wire contract.
- Consult [CLI guidance](../work-with-go-clis/SKILL.md) when a command consumes a public client package.
- Consult [service guidance](../work-with-go-services/SKILL.md) before exposing service-owned domain types or behavior.

## Validate the result

- Prefer the repository's documented formatting, test, lint, and check commands.
- Test constructor validation, documented behavior, exported error contracts, and representative external usage.
- Verify `doc.go` or equivalent package documentation explains purpose, entry points, and constraints.
- Review exported names for accidental application coupling and compatibility burden.
- For reviews, report concrete usability or supportability risks rather than requesting exports for convenience.

## Keep the skill current

Update [public-package-design.md](references/public-package-design.md) when repeated public-API work reveals missing or stale guidance. Change `SKILL.md` only when activation, universal boundaries, consultation behavior, or reference routing needs to change.
