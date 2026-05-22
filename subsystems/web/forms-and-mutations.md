# Forms And Mutations

This guide defines the default form, validation, mutation, and flash-message shape for `internal/web`.

Use it when implementing create, update, delete, or settings forms in a server-rendered UI.

## Required

- Use ordinary HTML forms as the base interaction.
- Add HTMX attributes only to enhance the same form route.
- Parse form input in the handler or a small resource-local parser.
- Validate request-local shape before calling the service.
- Preserve submitted values and validation messages in a typed form view.
- Redirect after successful non-HTMX mutations.
- Re-fetch affected service state after successful HTMX mutations.
- Render authoritative fragments from re-fetched state.
- Use flash/status view models for user-visible mutation results.
- Keep domain validation in the service and form-shape validation in `internal/web`.

## Form State Shape

Use a small input type for parsed request values and a view type for rendering.

```go
type DocumentForm struct {
	Title string
	errs  FormErrors
}

type DocumentFormView struct {
	Title       string
	TitleError  string
	FormError   string
	SubmitLabel string
}

func ParseDocumentForm(
	r *http.Request,
) DocumentForm {
	_ = r.ParseForm()
	return DocumentForm{
		Title: strings.TrimSpace(r.FormValue("title")),
		errs:  FormErrors{},
	}
}

func (f *DocumentForm) Validate() bool {
	if f.Title == "" {
		f.errs.Set("title", "Title is required.")
	}
	return f.errs.Empty()
}

func (f DocumentForm) View() DocumentFormView {
	return DocumentFormView{
		Title:       f.Title,
		TitleError:  f.errs.Get("title"),
		FormError:   f.errs.Get(""),
		SubmitLabel: "Create document",
	}
}
```

The exact helper names may vary, but the rendered view should carry submitted values and field-specific messages explicitly.

## Shared Form Errors

Keep shared validation primitives small.

```go
type FormErrors map[string]string

func (e FormErrors) Set(
	field string,
	message string,
) {
	if e != nil {
		e[field] = message
	}
}

func (e FormErrors) Get(
	field string,
) string {
	return e[field]
}

func (e FormErrors) Empty() bool {
	return len(e) == 0
}
```

Use `""` or another package-standard key for form-level errors. Keep field names aligned with form input names unless there is a clear reason not to.

## Mutation Handler Flow

```go
func (w *Web) handleCreateDocument(
	rw http.ResponseWriter,
	r *http.Request,
) {
	req := ParseRequestContext(r)

	form := ParseDocumentForm(r)
	if !form.Validate() {
		rw.WriteHeader(http.StatusBadRequest)
		w.renderer.RenderDocumentForm(rw, form.View())
		return
	}

	if _, err := w.service.CreateDocument(form.Title); err != nil {
		form.errs.Set("", "Document could not be created.")
		rw.WriteHeader(http.StatusBadRequest)
		w.renderer.RenderDocumentForm(rw, form.View())
		return
	}

	if !req.IsHTMX {
		http.Redirect(rw, r, "/documents", http.StatusSeeOther)
		return
	}

	docs, err := w.service.ListDocuments()
	if err != nil {
		w.writeError(rw, err)
		return
	}

	view := NewDocumentsPageView(
		docs,
		"",
		DocumentFormView{SubmitLabel: "Create document"},
		NewFlashView("Document created."),
	)
	w.renderer.RenderDocumentListWithFlash(rw, view)
}
```

This keeps non-HTMX and HTMX behavior aligned while letting each response use the right browser mechanism.

## Validation Responses

Invalid form submissions should render the same form region with:

- submitted values
- field errors
- form-level error when needed
- the same action URL and submit label

For HTMX requests, return the form fragment targeted by the submitted form. For normal requests, either render the full page with the invalid form embedded or return the form page with an appropriate non-2xx status.

Choose the response shape that keeps the route understandable and apply it consistently for that resource.

## Flash And Status Messages

Use a small status view model instead of ad hoc strings in templates.

```go
type FlashView struct {
	Message string
	Kind    string
}

func NewFlashView(
	message string,
) *FlashView {
	if message == "" {
		return nil
	}
	return &FlashView{
		Message: message,
		Kind:    "success",
	}
}
```

For normal redirects, store flash state only if the project already has a server-side mechanism for it. Otherwise, use the destination page's ordinary state to communicate the result.

For HTMX responses, include the flash region in the returned fragment or return it as an intentional out-of-band swap.

## Delete Forms

Use ordinary POST forms for delete actions unless the project has a broader method-override convention.

```html
<form method="post" action="{{.DeleteURL}}" hx-post="{{.DeleteURL}}" hx-target="#documents-list">
  <button type="submit">Delete</button>
</form>
```

The handler should perform the delete through the service, redirect for normal requests, and re-fetch the affected list or parent page state for HTMX requests.

## Service Errors

Map service errors into user-facing form or page state at the web boundary.

Do not expose raw internal error strings in templates. Use stable, human-readable messages that fit the form or page context.
