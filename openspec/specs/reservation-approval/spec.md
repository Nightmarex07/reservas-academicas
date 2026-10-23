# Reservation Approval Specification

## Purpose
Define los requisitos para que administradores de espacios revisen, aprueben o rechacen solicitudes de reserva en estado `PENDING`.

## Requirements

### Requirement: APR-01 Listado de Solicitudes Pendientes
El sistema SHALL permitir que `SPACE_ADMIN` y `SYS_ADMIN` obtengan la lista de reservas en estado `PENDING`.

#### Scenario: APR-01-A Listado exitoso
- **GIVEN** un `SPACE_ADMIN` autenticado con solicitudes pendientes en el sistema
- **WHEN** se envía `GET /admin/reservations?status=PENDING`
- **THEN** el sistema SHALL retornar HTTP 200 con lista paginada de reservas pendientes

#### Scenario: APR-01-B Sin solicitudes pendientes
- **GIVEN** no hay reservas en estado `PENDING`
- **WHEN** se envía `GET /admin/reservations?status=PENDING`
- **THEN** el sistema SHALL retornar HTTP 200 con lista vacía

### Requirement: APR-02 Aprobación de Reserva
El sistema SHALL permitir que `SPACE_ADMIN` o `SYS_ADMIN` aprueben una reserva en estado `PENDING`, cambiándola a `APPROVED`.

#### Scenario: APR-02-A Aprobación exitosa
- **GIVEN** una reserva en estado `PENDING` sin conflicto con otras `APPROVED`
- **WHEN** un `SPACE_ADMIN` envía `PUT /admin/reservations/{id}/approve`
- **THEN** el sistema SHALL cambiar el estado a `APPROVED`, registrar `approved_by` y `approved_at`, y retornar HTTP 200

#### Scenario: APR-02-B Conflicto al aprobar
- **GIVEN** una reserva `PENDING` para un espacio cuyo horario ya fue aprobado por otra reserva
- **WHEN** el admin intenta aprobarla
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"No se puede aprobar: existe un conflicto de horario con una reserva ya aprobada"`

#### Scenario: APR-02-C Reserva no encontrada
- **GIVEN** un `reservation_id` inexistente
- **WHEN** se envía `PUT /admin/reservations/{id}/approve`
- **THEN** el sistema SHALL retornar HTTP 404

#### Scenario: APR-02-D Estado inválido para aprobación
- **GIVEN** una reserva en estado `APPROVED`, `REJECTED` o `CANCELLED`
- **WHEN** el admin intenta aprobarla
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"Solo se pueden aprobar reservas en estado PENDING"`

### Requirement: APR-03 Rechazo de Reserva
El sistema SHALL permitir que `SPACE_ADMIN` o `SYS_ADMIN` rechacen una reserva en estado `PENDING`, cambiándola a `REJECTED`, indicando el motivo.

#### Scenario: APR-03-A Rechazo exitoso
- **GIVEN** una reserva en estado `PENDING` y un motivo de rechazo provisto
- **WHEN** un `SPACE_ADMIN` envía `PUT /admin/reservations/{id}/reject` con `{ "reason": "..." }`
- **THEN** el sistema SHALL cambiar el estado a `REJECTED` y retornar HTTP 200

#### Scenario: APR-03-B Rechazo sin motivo
- **GIVEN** una solicitud `PUT /admin/reservations/{id}/reject` sin campo `reason` o con `reason` vacío
- **WHEN** se envía la solicitud
- **THEN** el sistema SHALL retornar HTTP 422 con mensaje `"El motivo del rechazo es obligatorio"`

#### Scenario: APR-03-C Reserva no en estado PENDING
- **GIVEN** una reserva en estado `APPROVED`, `CANCELLED` o `REJECTED`
- **WHEN** el admin intenta rechazarla
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"Solo se pueden rechazar reservas en estado PENDING"`
