# Error Mapping

This guide defines the default shape for translating service errors into HTTP responses in `internal/api`.

Use it when handlers need consistent status behavior for service errors.

## Required

- Keep service-error-to-status translation in `internal/api`.
- Prefer one package-level mapping helper for the API surface.
- Map service errors, not store, SQL, driver, or transport errors.
- Keep transport wording near the response-writing helper so handlers stay focused on request flow.
- Use one default fallback response for unexpected errors.
- Split the mapper only when one package-level helper has become genuinely hard to audit.

## Local Flow

The normal pattern is:

1. a handler calls a service method
2. the handler passes any returned error to one API helper
3. the helper maps typed service errors to status codes and response messages

This keeps handlers short and makes status behavior easy to audit.

## Focused Example

```go
package api

import (
	"errors"
	"net/http"

	"example/internal/service"
	"git.sr.ht/~jakintosh/command-go/pkg/wire"
)

func writeServiceError(
	w http.ResponseWriter,
	err error,
) {
	wire.WriteError(w, httpStatusFromError(err), err.Error())
}

func httpStatusFromError(
	err error,
) int {
	switch {
	case errors.Is(err, service.ErrInvalidCredentials):
		return http.StatusUnauthorized
	case errors.Is(err, service.ErrProjectNotFound):
		return http.StatusNotFound
	case errors.Is(err, service.ErrInvalidProject):
		return http.StatusBadRequest
	case errors.Is(err, service.ErrProjectConflict):
		return http.StatusConflict
	case errors.Is(err, service.ErrPermissionDenied):
		return http.StatusForbidden
	default:
		return http.StatusInternalServerError
	}
}
```

The mapper should read like the API contract for failures. If several service errors map to the same status, group them together in the same case.
