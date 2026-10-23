# Spec Delta: reservation-core

## ADDED Requirements

### Requirement: RES-02 Regla de Duración Máxima (4 Horas)
El sistema SHALL rechazar cualquier reserva cuya duración supere las 4 horas consecutivas (`end_time - start_time <= 240 minutos`).

#### Scenario: RES-02-A Reserva dentro del límite
- **GIVEN** `start_time=09:00`, `end_time=13:00` (duración = 4h exactas)
- **WHEN** se envía `POST /reservations`
- **THEN** el sistema SHALL retornar HTTP 201 (reserva creada exitosamente)

#### Scenario: RES-02-B Reserva que excede el límite
- **GIVEN** `start_time=09:00`, `end_time=13:01` (duración = 4h 1min)
- **WHEN** se envía `POST /reservations`
- **THEN** el sistema SHALL retornar HTTP 422 con mensaje `"La duración máxima de una reserva es de 4 horas consecutivas"`

#### Scenario: RES-02-C Reserva de duración cero
- **GIVEN** `start_time=09:00`, `end_time=09:00`
- **WHEN** se envía `POST /reservations`
- **THEN** el sistema SHALL retornar HTTP 422 con mensaje `"La hora de fin debe ser posterior a la hora de inicio"`

## MODIFIED Requirements

### Requirement: RES-01 Creación de Solicitud de Reserva
El sistema SHALL permitir que usuarios autenticados creen solicitudes de reserva con duración de hasta 4 horas consecutivas.

#### Scenario: RES-01-A Creación exitosa de reserva
- **GIVEN** un usuario autenticado, un espacio activo y un horario de hasta 4 horas sin conflictos
- **WHEN** se envía `POST /reservations` con `space_id`, `start_time`, `end_time` y `purpose`
- **THEN** el sistema SHALL retornar HTTP 201 con los datos de la reserva en estado `PENDING`

#### Scenario: RES-01-B Espacio inactivo o inexistente
- **GIVEN** un `space_id` que no existe o cuyo `is_active=false`
- **WHEN** se envía `POST /reservations`
- **THEN** el sistema SHALL retornar HTTP 404 con mensaje `"Espacio no encontrado o no disponible"`

#### Scenario: RES-01-C Fecha de inicio en el pasado
- **GIVEN** una `start_time` anterior al momento actual
- **WHEN** se envía `POST /reservations`
- **THEN** el sistema SHALL retornar HTTP 422 con mensaje `"La fecha de inicio debe ser futura"`

#### Scenario: RES-01-D Hora fin anterior a hora inicio
- **GIVEN** `end_time` ≤ `start_time`
- **WHEN** se envía `POST /reservations`
- **THEN** el sistema SHALL retornar HTTP 422 con mensaje `"La hora de fin debe ser posterior a la hora de inicio"`
