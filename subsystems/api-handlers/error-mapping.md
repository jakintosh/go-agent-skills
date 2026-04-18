# Error Mapping

This guide defines the default shape for translating service errors into HTTP responses

Use it when several handlers in one domain need the same status mapping, or when inline error checks are starting to repeat

## Required

- Keep error-to-status translation in one small helper near the handlers that use it
- Map service errors, not store or transport errors
- Keep transport wording inside the helper so handlers stay focused on request flow
- Use one default fallback response for unexpected errors
- Keep the mapping local to one domain area unless the same contract is shared intentionally

## Local Flow

The normal pattern is:

1. a handler calls a service method
2. the handler passes any returned error to one local helper
3. the helper maps typed service errors to status codes and response messages

This keeps handlers short and makes status behavior easy to audit

## Focused Example

```go
var (
	ErrProjectNotFound = errors.New("project not found")
	ErrProjectConflict = errors.New("project conflict")
	ErrInvalidProject  = errors.New("invalid project")
)

func (s *Service) handleGetProject(w http.ResponseWriter, r *http.Request) {
	projectID := r.PathValue("project_id")

	project, err := s.GetProject(projectID)
	if err != nil {
		writeProjectError(w, err)
		return
	}

	wire.WriteData(w, http.StatusOK, project)
}

func (s *Service) handleCreateProject(w http.ResponseWriter, r *http.Request) {
	var req createProjectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		wire.WriteError(w, http.StatusBadRequest, "invalid json")
		return
	}

	project, err := s.CreateProject(req.Name)
	if err != nil {
		writeProjectError(w, err)
		return
	}

	wire.WriteData(w, http.StatusCreated, project)
}

func writeProjectError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, ErrProjectNotFound):
		wire.WriteError(w, http.StatusNotFound, "project not found")
	case errors.Is(err, ErrProjectConflict):
		wire.WriteError(w, http.StatusConflict, "project conflict")
	case errors.Is(err, ErrInvalidProject):
		wire.WriteError(w, http.StatusBadRequest, "invalid project")
	default:
		wire.WriteError(w, http.StatusInternalServerError, "internal server error")
	}
}
```

Keep the helper small. If one mapping function is handling unrelated domains, split it by domain.
