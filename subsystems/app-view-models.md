# App View Models

This guide defines the standard shape for view models and presentation modules in server-rendered applications.

It focuses on the mapping layer between domain data and templates, the structure of `view_*.go` modules, and the rules that keep templates declarative instead of presentation-heavy.

The goal is to make presentation code:

- explicit and typed
- organized by UI concern
- reusable across page and fragment rendering
- separate from domain and transport logic

## When to use this guide

Use this guide when you are:

- shaping data for server-rendered templates
- deciding what belongs in templates versus Go presentation code
- organizing `view_*.go` modules
- reviewing whether handlers or templates are absorbing too much formatting logic

## Non-goals

This guide does not define:

- HTMX request-flow behavior
- HTTP routing or handler structure in detail
- domain service rules
- CSS or client-side enhancement code

## Core rules

- Use explicit view models between domain data and templates.
- Organize UI code by ownership boundaries, with one presentation module per concern.
- Keep mapper functions pure presentation mapping with no store or network access.
- Keep templates declarative and move formatting into Go presentation code.
- Keep one renderer boundary so handlers call renderer methods built on view models.

## What a view model is for

A view model is the display-ready shape of UI data.

It should answer presentation questions such as:

- what title or label should be shown?
- which action URL should be used?
- should a panel be open, disabled, or empty?
- what formatted string should appear for a date or status?

It should not be a raw copy of the domain entity just because that is convenient.

## Presentation-module boundary

Treat each `view_*.go` file as a small presentation module for one coherent UI concern.

For example:

```text
internal/app/
  view_projects.go
  view_project_detail.go
  view_settings.go
```

A good module usually owns:

- one or more typed view structs
- mapping helpers such as `NewProjectView(...)`
- small nested view types for repeated fragments
- concern-specific renderer methods when helpful

This keeps presentation logic local to the part of the UI it supports.

## Canonical shape

A typical presentation module looks like:

```go
type ProjectRowView struct {
	ID          string
	Name        string
	DetailURL   string
	DeleteURL   string
	ConfirmText string
	UpdatedText string
}

func NewProjectRowView(project service.Project) ProjectRowView {
	return ProjectRowView{
		ID:          project.ID,
		Name:        project.Name,
		DetailURL:   "/projects/" + project.ID,
		DeleteURL:   "/projects/" + project.ID,
		ConfirmText: "Delete " + project.Name + "?",
		UpdatedText: project.UpdatedAt.Format("2006-01-02 15:04"),
	}
}
```

The mapper's job is to turn domain data into template-ready data.

That includes:

- formatted strings
- labels and action metadata
- nested child views
- booleans that drive conditional rendering

## Keep templates declarative

Templates should mostly do:

- field reads
- simple conditionals
- named-template composition

Formatting and presentation decisions should live in Go code instead.

That means view models should often carry:

- preformatted dates
- human-readable status labels
- URLs and button labels
- confirm text
- empty-state messages or flags

Do not make templates assemble complex strings or perform presentation-heavy logic inline.

## Pure mapping

`NewXView(...)` mappers should be pure presentation mapping functions.

They should not:

- open stores
- call services
- fetch network data
- mutate application state

Handlers or higher-level orchestration should gather the domain state first. Then view builders shape it for rendering.

## Nested and grouped state

When a UI concern is hierarchical, prefer parent view models that own nested child views.

When a page has many related state inputs, group them into state structs rather than long positional argument lists.

For example:

```go
type ProjectPageState struct {
	SelectedProjectID string
	Search            string
	Page              int
}

type ProjectPageView struct {
	List   []ProjectRowView
	Detail *ProjectDetailView
}
```

This makes complex page-state mapping easier to read and change.

## Renderer relationship

Handlers should pass view models to renderer methods, and renderer methods should be the place that chooses which named templates to execute.

This keeps the renderer boundary intact while still letting presentation modules own the typed shapes that rendering depends on.

## Testing expectations

View-model code should be easy to test for:

- formatting behavior
- action URL generation
- empty-state mapping
- selection and pagination carryover
- parity between full-page and fragment rendering inputs when they share the same view builders

Focused mapping tests are often more valuable here than large template-output snapshots.

## Anti-patterns

- passing raw domain entities directly into templates by default
- templates formatting dates, labels, and action text inline
- view builders that fetch data or mutate state
- one giant presentation file for the entire application
- handlers manually assembling many template fields instead of using typed view models

## Related guides

- `server-rendered-htmx-ui.md`
- `service-construction.md`
