# Diseño Técnico: Regla de 4 Horas Consecutivas

## Enfoque

Implementar la validación de duración máxima en la capa de schemas (Pydantic) para obtener respuesta HTTP 422 automática con mensaje descriptivo, antes de que la solicitud llegue al servicio o la base de datos.

## Ubicación de la validación

```python
# schemas.py — ReservationCreateRequest
@model_validator(mode="after")
def validate_times(self):
    if self.end_time <= self.start_time:
        raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
    duration = (self.end_time - self.start_time).total_seconds() / 3600
    if duration > MAX_RESERVATION_HOURS:  # MAX_RESERVATION_HOURS = 4
        raise ValueError(
            f"La duración máxima de una reserva es de {MAX_RESERVATION_HOURS} horas consecutivas"
        )
    return self
```

## Constante centralizada

`MAX_RESERVATION_HOURS = 4` se define en `schemas.py` y se importa en `reservation_service.py` para evitar duplicación.

## Respuesta HTTP

- Duración válida (≤ 4h): continúa el flujo normal.
- Duración inválida (> 4h): FastAPI retorna automáticamente HTTP 422 con detalle de la validación:
```json
{
  "detail": [{
    "type": "value_error",
    "msg": "La duración máxima de una reserva es de 4 horas consecutivas"
  }]
}
```

## Casos límite verificados

| Duración | Resultado esperado |
|---|---|
| 0 minutos (start == end) | HTTP 422 — "fin debe ser posterior a inicio" |
| 1 minuto | HTTP 201 ✅ |
| 3h 59m | HTTP 201 ✅ |
| 4h exactas | HTTP 201 ✅ |
| 4h 1m | HTTP 422 ❌ |
| 5h | HTTP 422 ❌ |
| 24h | HTTP 422 ❌ |
