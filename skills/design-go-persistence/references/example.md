# Minimal Persistence Example

```go
type CreateReservationParams struct {
	ID         string
	AttendeeID string
}

type Reservation struct {
	ID         string
	EventID    string
	AttendeeID string
	Seat       int
}

// CreateReservation reserves the next seat and returns the persisted reservation.
//
// Persisted preconditions:
//   - The event exists, remains open after now, and has an available seat.
//   - The attendee has no reservation for the event.
//
// Atomic effects:
//   - A reservation is created with the next available seat.
//
// Retry:
//   - The same reservation ID and attendee return the existing reservation.
//   - Reusing the ID for another attendee fails with ErrConflict.
//
// Errors:
//   - ErrNotFound when the event does not exist.
//   - ErrClosed when the event closes at or before now.
//   - ErrFull when no seat remains.
//   - ErrConflict for another reservation by the attendee or incompatible retry.
CreateReservation(
	event string,
	params CreateReservationParams,
	now time.Time,
) (
	*Reservation,
	error,
)
```

The service validates request shape, authorizes the caller, creates the ID, captures `now`, and calls `CreateReservation`. It does not check whether the event is open or has capacity.

The adapter keeps the contract visible:

```go
func (db *DB) CreateReservation(
	event string,
	params service.CreateReservationParams,
	now time.Time,
) (
	*service.Reservation,
	error,
) {
	tx, err := db.Conn.Begin()
	if err != nil {
		return nil, fmt.Errorf("begin reservation: %w", err)
	}
	defer tx.Rollback()

	existing, err := sqlReservationByIdTx(tx, params.ID)
	if err == nil {
		return matchReservationRetry(existing, event, params)
	}
	if !errors.Is(err, service.ErrNotFound) {
		return nil, err
	}

	state, err := sqlEventStateTx(tx, event)
	if err != nil {
		return nil, err
	}
	if !state.ClosesAt.After(now) {
		return nil, service.ErrClosed
	}

	seat, err := sqlNextAvailableSeatTx(tx, state.ID, params.AttendeeID)
	if err != nil {
		return nil, err
	}

	reservation := &service.Reservation{
		ID: params.ID,
		EventID: event,
		AttendeeID: params.AttendeeID,
		Seat: seat,
	}
	if err := sqlInsertReservationTx(tx, state.ID, reservation); err != nil {
		return nil, err
	}
	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("commit reservation: %w", err)
	}
	return reservation, nil
}
```

The adapter tests mirror the contract:

```go
TestCreateReservation_AssignsNextSeat
TestCreateReservation_RejectsClosedEventWithoutChange
TestCreateReservation_RejectsFullEventWithoutChange
TestCreateReservation_ExactRetryReturnsReservation
TestCreateReservation_IncompatibleRetryConflicts
```
