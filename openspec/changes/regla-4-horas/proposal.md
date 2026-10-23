# Propuesta de Cambio: Regla de Duración Máxima de 4 Horas

## Motivación

La institución universitaria ha establecido una nueva política de uso equitativo de espacios académicos: **ningún usuario podrá reservar un espacio durante más de cuatro horas consecutivas**.

Esta regla busca garantizar que los espacios sean accesibles a un mayor número de usuarios y evitar el acaparamiento de instalaciones académicas.

## Módulos afectados

| Módulo | Tipo de impacto |
|---|---|
| `reservation-core` | Requisito nuevo (RES-02) — validación de duración |
| `backend/schemas.py` | Validator de Pydantic en `ReservationCreateRequest` |
| `backend/services/reservation_service.py` | Constante y validación en `create_reservation` |
| `backend/tests/test_reservations.py` | Nuevos casos de prueba (clase `TestRegla4Horas`) |

## Análisis de impacto

### ¿Afecta funcionalidades existentes?
- **No afecta** la detección de conflictos (RES-03): sigue operando igual.
- **No afecta** la aprobación/rechazo (APR-02/03): el cambio ocurre en el momento de creación.
- **No afecta** el historial ni cancelación: estados no cambian.

### ¿Requiere migración de datos?
No. La regla solo aplica a **nuevas** reservas. Las reservas existentes con duración > 4h se respetan (grandfathering).

### ¿Requiere actualizar el plan de ingeniería?
Sí. El `PLAN_INGENIERIA.md` no contemplaba esta restricción. Se registra como decisión técnica sobrevenida.

## Correspondencia con PLAN_INGENIERIA.md

El plan indicaba validaciones de horario (sección 3.4) pero no especificaba límite de duración. Este cambio complementa el plan sin contradecirlo.

## Implementación

La validación se implementa en **dos capas** para garantizar robustez:
1. **Schema layer** (`schemas.py`): `model_validator` en `ReservationCreateRequest` — retorna HTTP 422 antes de llegar al servicio.
2. **Service layer** (`reservation_service.py`): constante `MAX_DURATION_MINUTES = 240` como referencia para pruebas unitarias de la lógica pura.
