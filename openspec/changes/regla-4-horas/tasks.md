# Tareas: Regla de 4 Horas Consecutivas

## Especificación
- [x] Actualizar `openspec/specs/reservation-core/spec.md` — agregar RES-02 con escenarios GIVEN/WHEN/THEN
- [x] Crear delta spec en `openspec/changes/regla-4-horas/specs/reservation-core/spec.md`

## Implementación
- [x] Definir `MAX_RESERVATION_HOURS = 4` en `schemas.py`
- [x] Agregar `model_validator` en `ReservationCreateRequest` que valida duración ≤ 4h
- [x] Importar y usar la constante en `reservation_service.py`

## Pruebas
- [x] `TestRegla4Horas::test_exactamente_4_horas_valido` — RES-02-A
- [x] `TestRegla4Horas::test_4_horas_1_minuto_rechazado` — RES-02-B
- [x] `TestRegla4Horas::test_5_horas_rechazado` — RES-02-B (adicional)
- [x] `TestRegla4Horas::test_duracion_cero_rechazada` — RES-02-C
- [x] `TestRegla4Horas::test_1_hora_valido` — caso positivo
- [x] `TestRegla4Horas::test_3_horas_59_minutos_valido` — caso límite positivo

## Verificación
- [x] Ejecutar `pytest tests/test_reservations.py::TestRegla4Horas -v`
- [x] Verificar que funcionalidades existentes no se rompieron (`pytest -v`)
- [x] Archivar este change: `openspec archive regla-4-horas`
