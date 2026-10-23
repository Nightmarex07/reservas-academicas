# Reservation History Specification

## Purpose
Define los requisitos para que los usuarios consulten su historial de reservas y puedan cancelar reservas propias, y para que administradores accedan al historial global.

## Requirements

### Requirement: HST-01 Historial Personal de Reservas
El sistema SHALL permitir que cualquier usuario autenticado consulte todas sus reservas con soporte de filtros y paginación.

#### Scenario: HST-01-A Consulta de historial con resultados
- **GIVEN** un usuario autenticado con reservas registradas
- **WHEN** se envía `GET /users/me/reservations`
- **THEN** el sistema SHALL retornar HTTP 200 con lista paginada de reservas

#### Scenario: HST-01-B Historial vacío
- **GIVEN** un usuario autenticado sin ninguna reserva
- **WHEN** se envía `GET /users/me/reservations`
- **THEN** el sistema SHALL retornar HTTP 200 con `{ "items": [], "total": 0, "page": 1 }`

### Requirement: HST-02 Cancelación de Reserva Propia
El sistema SHALL permitir que el propietario de una reserva la cancele si está en estado `PENDING` o `APPROVED`, siempre que la fecha de inicio no haya pasado.

#### Scenario: HST-02-A Cancelación exitosa por el propietario
- **GIVEN** una reserva en estado `PENDING` o `APPROVED` con `start_time` futuro
- **WHEN** el usuario propietario envía `DELETE /reservations/{id}`
- **THEN** el sistema SHALL cambiar el estado a `CANCELLED`, registrar `cancelled_at` y retornar HTTP 200

#### Scenario: HST-02-B Cancelación de reserva pasada
- **GIVEN** una reserva cuyo `start_time` ya transcurrió
- **WHEN** el usuario intenta cancelarla
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"No se puede cancelar una reserva cuya fecha de inicio ya pasó"`

#### Scenario: HST-02-C Cancelación por otro usuario sin permisos
- **GIVEN** un usuario que NO creó la reserva y NO es administrador
- **WHEN** intenta cancelar la reserva de otro usuario
- **THEN** el sistema SHALL retornar HTTP 403 con mensaje `"No tienes permisos para cancelar esta reserva"`

#### Scenario: HST-02-D Cancelación de reserva ya cancelada
- **GIVEN** una reserva en estado `CANCELLED` o `REJECTED`
- **WHEN** se intenta cancelarla nuevamente
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"Esta reserva ya no puede ser cancelada"`

### Requirement: HST-03 Detalle de Reserva Individual
El sistema SHALL permitir que el propietario o un administrador consulte el detalle completo de una reserva específica.

#### Scenario: HST-03-A Consulta exitosa
- **GIVEN** un `reservation_id` válido y el usuario es propietario o admin
- **WHEN** se envía `GET /reservations/{id}`
- **THEN** el sistema SHALL retornar HTTP 200 con todos los campos de la reserva

#### Scenario: HST-03-B Acceso de tercero no autorizado
- **GIVEN** un usuario que no es el propietario ni admin
- **WHEN** intenta consultar `GET /reservations/{id}` de otra persona
- **THEN** el sistema SHALL retornar HTTP 403
