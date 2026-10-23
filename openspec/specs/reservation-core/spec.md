# Reservation Core Specification

## Purpose
Define los requisitos para la creación de solicitudes de reserva, la validación de disponibilidad, la prevención de reservas simultáneas conflictivas y la regla de duración máxima de 4 horas consecutivas.

## Requirements

### Requirement: RES-01 Creación de Solicitud de Reserva
El sistema SHALL permitir que usuarios autenticados (cualquier rol) creen solicitudes de reserva para espacios académicos activos con estado inicial `PENDING`.

#### Scenario: RES-01-A Creación exitosa de reserva
- **GIVEN** un usuario autenticado, un espacio activo y un horario sin conflictos de duración ≤ 4 horas
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

### Requirement: RES-03 Detección y Prevención de Conflictos
El sistema SHALL detectar y prevenir reservas que se solapen temporalmente en el mismo espacio usando bloqueo transaccional.

#### Scenario: RES-03-A Conflicto detectado con solapamiento parcial
- **GIVEN** el espacio LAB-01 tiene una reserva APPROVED de 10:00 a 12:00
- **WHEN** se intenta crear una nueva reserva para LAB-01 de 11:00 a 13:00
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"El espacio no está disponible en el horario seleccionado"`

#### Scenario: RES-03-B Sin conflicto en horarios adyacentes
- **GIVEN** el espacio LAB-01 tiene una reserva APPROVED de 09:00 a 11:00
- **WHEN** se intenta crear una reserva de 11:00 a 13:00 (contigua, sin solapamiento)
- **THEN** el sistema SHALL retornar HTTP 201

#### Scenario: RES-03-C Sin conflicto con reserva cancelada
- **GIVEN** el espacio LAB-01 tiene una reserva CANCELLED de 09:00 a 11:00
- **WHEN** se intenta crear una reserva de 09:00 a 11:00 en el mismo espacio
- **THEN** el sistema SHALL retornar HTTP 201

### Requirement: RES-04 Consulta de Disponibilidad
El sistema SHALL permitir que cualquier usuario autenticado consulte si un espacio está disponible para un rango horario específico.

#### Scenario: RES-04-A Consulta de disponibilidad positiva
- **GIVEN** un espacio activo y un rango horario sin reservas activas
- **WHEN** se envía `GET /reservations/availability?space_id=...&start_time=...&end_time=...`
- **THEN** el sistema SHALL retornar HTTP 200 con `{ "available": true, "conflicts": [] }`

#### Scenario: RES-04-B Consulta de disponibilidad negativa
- **GIVEN** un espacio con reservas activas que solapan el rango consultado
- **WHEN** se envía `GET /reservations/availability?space_id=...&start_time=...&end_time=...`
- **THEN** el sistema SHALL retornar HTTP 200 con `{ "available": false, "conflicts": [...] }`
