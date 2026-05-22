# Web View Models

This guide defines the standard shape for view models in `internal/web`.

Use it when shaping service data for `html/template`, deciding what belongs in templates versus Go code, or reviewing whether handlers and templates are absorbing too much presentation logic.

## Required

- Use explicit view models between service data and templates.
- Keep view models display-ready.
- Keep view builders pure: no service calls, store calls, network access, or state mutation.
- Put resource-specific view models beside the resource handlers by default.
- Build the smallest view model that matches the region being rendered.
- Compose page views from the same region views used by fragment renderers.
- Move formatting, labels, URLs, selected state, and empty-state text into Go view builders.
- Keep templates limited to field reads, simple conditionals, ranges, and named-template composition.
- Keep view models separate from service domain types and API DTOs.

## View Model Purpose

A view model answers presentation questions:

- what text should be displayed?
- which URL should this action use?
- should this region be open, empty, selected, disabled, or invalid?
- what formatted date, status, or count should appear?
- what message should be shown after a mutation?

Do not pass raw service values to templates just because their fields currently match the HTML.

## Resource Locality

Keep view models in the resource file that owns the UI concern when that keeps the behavior readable.

```text
internal/web/
  documents.go
  settings.go
```

For example, `documents.go` may own:

- document route registration
- document handlers
- document list and detail views
- document form views
- document-specific renderer methods

Split view models into a separate file only when the resource file stops being easy to scan.

## Canonical Shape

```go
type DocumentRowView struct {
	ID          string
	Title       string
	DetailURL   string
	DeleteURL   string
	ConfirmText string
	UpdatedText string
	IsSelected  bool
}

func NewDocumentRowView(
	doc service.Document,
	selectedID string,
) DocumentRowView {
	return DocumentRowView{
		ID:          doc.ID,
		Title:       doc.Title,
		DetailURL:   "/documents/" + doc.ID,
		DeleteURL:   "/documents/" + doc.ID + "/delete",
		ConfirmText: "Delete " + doc.Title + "?",
		UpdatedText: doc.UpdatedAt.Format("2006-01-02 15:04"),
		IsSelected:  doc.ID == selectedID,
	}
}
```

The builder turns domain state into template-ready data. The template should not assemble URLs, format dates, or decide labels inline.

## Region And Page Views

Fragment renderers should receive the region view they render. Full-page views should compose those same region views.

```go
type DocumentListView struct {
	Rows []DocumentRowView
}

type DocumentsPageView struct {
	List   DocumentListView
	Detail *DocumentDetailView
	Form   DocumentFormView
	Flash  *FlashView
}

func NewDocumentListView(
	docs []service.Document,
	selectedID string,
) DocumentListView {
	rows := make([]DocumentRowView, 0, len(docs))
	for _, doc := range docs {
		rows = append(rows, NewDocumentRowView(doc, selectedID))
	}

	return DocumentListView{Rows: rows}
}

func NewDocumentsPageView(
	list DocumentListView,
	detail *DocumentDetailView,
	form DocumentFormView,
	flash *FlashView,
) DocumentsPageView {
	return DocumentsPageView{
		List:   list,
		Detail: detail,
		Form:   form,
		Flash:  flash,
	}
}
```

Do not pass a page view to a fragment renderer just because the page contains that fragment. Build the list view once, render it directly for an HTMX list response, or compose it into the page view for a normal full-page response.

This keeps full-page rendering, direct links, refreshes, and HTMX swaps aligned without giving fragment renderers more state than they need.

## Form Views

Represent submitted values and validation messages explicitly.

```go
type DocumentFormView struct {
	Title       string
	TitleError  string
	FormError   string
	SubmitLabel string
}
```

The template should be able to render a valid empty form, a submitted invalid form, and an edit form from the same typed shape.

Read `./forms-and-mutations.md` for the shared form validation flow.

## Testing Expectations

View-model tests should cover presentation behavior that is easy to break:

- URL generation
- formatted dates and counts
- selected or disabled state
- empty-state values
- validation state projection
- shared full-page and fragment inputs

Focused mapping tests are usually more valuable than large template-output snapshots.
