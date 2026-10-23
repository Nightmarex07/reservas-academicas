# Revisión de Especificaciones — Fase 2

## Motivación

Antes de iniciar la implementación, se realizó una revisión formal de las seis especificaciones OpenSpec para garantizar consistencia, completitud y correspondencia con el `PLAN_INGENIERIA.md`.

## Módulos revisados

- `user-management` — Registro, autenticación, roles, JWT
- `space-management` — CRUD de espacios, disponibilidad
- `reservation-core` — Creación, validación de conflictos, regla 4h
- `reservation-approval` — Aprobación y rechazo por admins
- `reservation-history` — Historial personal y global, cancelación
- `notifications` — Correos en cada transición de estado

## Hallazgos de la revisión

### ✅ Consistencias verificadas

1. **Ciclo de vida de reserva** es consistente entre `reservation-core`, `reservation-approval` y `reservation-history`:
   - Estados válidos: `PENDING → APPROVED/REJECTED`, `PENDING/APPROVED → CANCELLED`.
   - Ninguna spec permite transiciones inválidas.

2. **Jerarquía de roles** es coherente en todas las specs:
   - `STUDENT` y `TEACHER` no pueden aprobar/rechazar reservas.
   - `SPACE_ADMIN` gestiona espacios y reservas pero no usuarios.
   - `SYS_ADMIN` tiene acceso completo.

3. **Códigos HTTP** son consistentes con las convenciones REST:
   - `201` para creaciones exitosas.
   - `200` para actualizaciones y lecturas.
   - `204` para eliminaciones.
   - `409` para conflictos de negocio.
   - `422` para validaciones de schema.
   - `401/403` para autenticación/autorización.

4. **Regla de 4 horas** está documentada en `reservation-core` (RES-02) con escenarios límite claros.

5. **Asincronía de notificaciones** explícitamente declarada en `notifications` (NOT-05) para no bloquear flujos de negocio.

### ⚠️ Ambigüedades resueltas

| Ambigüedad | Resolución adoptada |
|---|---|
| ¿Pueden los TEACHER aprobar reservas? | No. Solo `SPACE_ADMIN` y `SYS_ADMIN`. El PLAN_INGENIERIA indica "prioridad en aprobación" como prioridad de atención, no de rol. |
| ¿Qué pasa con reservas PENDING al desactivar un espacio? | Se cancelan automáticamente (SPC-03-B). Las APPROVED también se cancelan. |
| ¿El conflicto incluye reservas PENDING? | Sí. Se valida contra PENDING y APPROVED para evitar aprobar dos PENDING del mismo slot. |
| ¿Puede un admin cancelar la reserva de otro usuario? | Sí. La spec HST-02-C lo permite para `SPACE_ADMIN` y `SYS_ADMIN`. |
| ¿El refresh token se invalida al hacer logout? | Sí, se elimina de Redis. No hay endpoint de logout en la spec actual; se agrega a tasks. |

### 📋 Correspondencia con PLAN_INGENIERIA.md

| Funcionalidad del Plan | Spec correspondiente | Estado |
|---|---|---|
| Gestión de espacios académicos | `space-management` | ✅ Cubierto |
| Registro y administración de usuarios | `user-management` | ✅ Cubierto |
| Roles y permisos | `user-management` (USR-03) | ✅ Cubierto |
| Creación de solicitudes de reserva | `reservation-core` (RES-01) | ✅ Cubierto |
| Validación de disponibilidad | `reservation-core` (RES-04) | ✅ Cubierto |
| Prevención de reservas simultáneas | `reservation-core` (RES-03) | ✅ Cubierto |
| Aprobación y rechazo de solicitudes | `reservation-approval` | ✅ Cubierto |
| Cancelación e historial | `reservation-history` | ✅ Cubierto |
| Notificaciones | `notifications` | ✅ Cubierto |
| Regla de 4 horas consecutivas | `reservation-core` (RES-02) | ✅ Cubierto |

### ❌ Contradicciones detectadas y corregidas

No se detectaron contradicciones entre specs. Todos los límites de estado y roles son mutuamente consistentes.

## Decisión de implementación

Las especificaciones están listas para su implementación. El orden de desarrollo seguirá las dependencias definidas en el PLAN_INGENIERIA.md:

1. Infraestructura (modelos, BD, config)
2. Autenticación y usuarios
3. Espacios académicos
4. Reservas (núcleo)
5. Aprobación/rechazo
6. Historial y cancelación
7. Notificaciones
