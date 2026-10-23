# Space Management Specification

## Purpose
Define los requisitos para crear, consultar, actualizar y eliminar espacios académicos (laboratorios, auditorios y salas de cómputo) en el sistema de reservas.

## Requirements

### Requirement: SPC-01 Creación de Espacio Académico
El sistema SHALL permitir que usuarios con rol `SPACE_ADMIN` o `SYS_ADMIN` registren nuevos espacios académicos.

**Restricciones:**
- El nombre SHALL ser único en el sistema.
- La capacidad MUST ser mayor que 0.

#### Scenario: SPC-01-A Creación exitosa
- **GIVEN** un `SPACE_ADMIN` autenticado y datos de espacio válidos
- **WHEN** se envía `POST /spaces` con nombre, tipo, capacidad y ubicación
- **THEN** el sistema SHALL retornar HTTP 201 con los datos del espacio creado incluyendo su `id`

#### Scenario: SPC-01-B Nombre duplicado
- **GIVEN** un nombre de espacio ya existente en el sistema
- **WHEN** se envía `POST /spaces` con ese nombre
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"Ya existe un espacio con ese nombre"`

#### Scenario: SPC-01-C Tipo de espacio inválido
- **GIVEN** un valor de `type` que no sea `LABORATORY`, `AUDITORIUM` o `COMPUTER_ROOM`
- **WHEN** se envía `POST /spaces`
- **THEN** el sistema SHALL retornar HTTP 422 con detalle de los valores aceptados

#### Scenario: SPC-01-D Acceso no autorizado
- **GIVEN** un usuario con rol `STUDENT` o `TEACHER`
- **WHEN** intenta crear un espacio vía `POST /spaces`
- **THEN** el sistema SHALL retornar HTTP 403

### Requirement: SPC-02 Consulta de Espacios
El sistema SHALL permitir que cualquier usuario autenticado liste y consulte espacios académicos.

#### Scenario: SPC-02-A Listado de todos los espacios activos
- **GIVEN** un usuario autenticado
- **WHEN** se envía `GET /spaces?is_active=true`
- **THEN** el sistema SHALL retornar HTTP 200 con lista de espacios activos

#### Scenario: SPC-02-B Consulta de espacio individual
- **GIVEN** un `space_id` existente
- **WHEN** se envía `GET /spaces/{space_id}`
- **THEN** el sistema SHALL retornar HTTP 200 con los datos completos del espacio

#### Scenario: SPC-02-C Espacio no encontrado
- **GIVEN** un `space_id` inexistente
- **WHEN** se envía `GET /spaces/{space_id}`
- **THEN** el sistema SHALL retornar HTTP 404 con mensaje `"Espacio no encontrado"`

### Requirement: SPC-03 Actualización de Espacio
El sistema SHALL permitir que `SPACE_ADMIN` o `SYS_ADMIN` actualicen los datos de un espacio existente.

#### Scenario: SPC-03-A Actualización exitosa
- **GIVEN** un `SPACE_ADMIN` autenticado y un `space_id` existente
- **WHEN** se envía `PUT /spaces/{space_id}` con campos a modificar
- **THEN** el sistema SHALL retornar HTTP 200 con los datos actualizados

#### Scenario: SPC-03-B Desactivación con reservas pendientes
- **GIVEN** un espacio con reservas futuras en estado `PENDING` o `APPROVED`
- **WHEN** se actualiza `is_active=false`
- **THEN** el sistema SHALL cancelar esas reservas y retornar HTTP 200 indicando el número de reservas canceladas

### Requirement: SPC-04 Eliminación de Espacio
El sistema SHALL permitir que `SYS_ADMIN` elimine un espacio lógicamente (soft delete).

#### Scenario: SPC-04-A Eliminación exitosa
- **GIVEN** un `SYS_ADMIN` y un `space_id` existente sin reservas futuras activas
- **WHEN** se envía `DELETE /spaces/{space_id}`
- **THEN** el sistema SHALL retornar HTTP 204

#### Scenario: SPC-04-B Eliminación con reservas futuras
- **GIVEN** un espacio con reservas futuras activas
- **WHEN** se envía `DELETE /spaces/{space_id}`
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"No se puede eliminar: el espacio tiene reservas futuras activas. Desactívelo primero."`

### Requirement: SPC-05 Consulta de Disponibilidad
El sistema SHALL exponer un endpoint que indique los bloques de tiempo ocupados para un espacio en un rango de fechas.

#### Scenario: SPC-05-A Consulta de disponibilidad exitosa
- **GIVEN** un `space_id` activo, una `date_from` y `date_to` válidas
- **WHEN** se envía `GET /spaces/{space_id}/availability?date_from=...&date_to=...`
- **THEN** el sistema SHALL retornar HTTP 200 con lista de intervalos ocupados
