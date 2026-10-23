# Notifications Specification

## Purpose
Define los requisitos para el envío automatizado de notificaciones por correo electrónico a los usuarios afectados en cada transición de estado de sus reservas.

## Requirements

### Requirement: NOT-01 Notificación de Confirmación de Solicitud
El sistema SHALL enviar un correo de confirmación al usuario cuando una reserva es creada y queda en estado `PENDING`.

#### Scenario: NOT-01-A Correo enviado tras creación de reserva
- **GIVEN** una reserva creada exitosamente en estado `PENDING`
- **WHEN** el sistema completa la transacción de creación
- **THEN** el sistema SHALL encolar y enviar un correo de confirmación al correo del usuario en segundo plano

#### Scenario: NOT-01-B Fallo de envío no bloquea la reserva
- **GIVEN** un error transitorio del servidor SMTP
- **WHEN** se intenta enviar la notificación
- **THEN** el sistema SHALL registrar el error en logs y NO revertir la reserva creada

### Requirement: NOT-02 Notificación de Aprobación
El sistema SHALL enviar un correo al usuario cuando su reserva es aprobada (`PENDING` a `APPROVED`).

#### Scenario: NOT-02-A Correo de aprobación enviado
- **GIVEN** una reserva aprobada por un administrador
- **WHEN** el estado cambia a `APPROVED`
- **THEN** el sistema SHALL enviar correo de aprobación al propietario de la reserva

### Requirement: NOT-03 Notificación de Rechazo
El sistema SHALL enviar un correo al usuario cuando su reserva es rechazada (`PENDING` a `REJECTED`), incluyendo el motivo.

#### Scenario: NOT-03-A Correo de rechazo con motivo
- **GIVEN** una reserva rechazada con motivo registrado
- **WHEN** el estado cambia a `REJECTED`
- **THEN** el sistema SHALL enviar correo con el motivo del rechazo al propietario

### Requirement: NOT-04 Notificación de Cancelación
El sistema SHALL enviar un correo al usuario cuando una reserva es cancelada por el usuario o por un administrador.

#### Scenario: NOT-04-A Correo de cancelación por el usuario
- **GIVEN** el usuario cancela su propia reserva
- **WHEN** el estado cambia a `CANCELLED`
- **THEN** el sistema SHALL enviar correo de notificación de cancelación

### Requirement: NOT-05 Comportamiento Asíncrono
El sistema SHALL procesar el envío de notificaciones de forma asíncrona mediante tareas en segundo plano.

#### Scenario: NOT-05-A Tarea en segundo plano sin bloqueo
- **GIVEN** una petición que genera notificación por correo
- **WHEN** la respuesta HTTP es emitida al cliente
- **THEN** el envío del correo se ejecuta de forma desacoplada en segundo plano
