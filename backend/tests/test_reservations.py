"""
Tests for reservation-core, reservation-approval, and reservation-history specs.
Critical: RES-02 (4-hour rule), RES-03 (conflict detection), APR-02/03, HST-02.
"""
import pytest
from datetime import datetime, timedelta, timezone


def future_dt(hours_from_now: float, extra_minutes: int = 0) -> str:
    dt = (datetime.now(timezone.utc) + timedelta(hours=hours_from_now, minutes=extra_minutes)).replace(microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_reservation(client, token, space_id, start_offset_h=2, duration_h=1, purpose="Reserva de prueba"):
    base = datetime.now(timezone.utc).replace(microsecond=0)
    start = (base + timedelta(hours=start_offset_h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (base + timedelta(hours=start_offset_h + duration_h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return client.post("/reservations", json={
        "space_id": space_id,
        "start_time": start,
        "end_time": end,
        "purpose": purpose,
    }, headers={"Authorization": f"Bearer {token}"})


# ─── Regla de 4 Horas (RES-02) ─────────────────────────────────────────────

class TestRegla4Horas:
    """Spec: RES-02 — CRÍTICO: regla de duración máxima 4 horas."""

    def test_exactamente_4_horas_valido(self, client, student_token, sample_space):
        """RES-02-A: duración exacta de 4h debe ser aceptada (HTTP 201)."""
        base = datetime.now(timezone.utc).replace(microsecond=0)
        start = (base + timedelta(hours=24)).isoformat()
        end = (base + timedelta(hours=28)).isoformat()
        resp = client.post("/reservations", json={
            "space_id": sample_space["id"],
            "start_time": start,
            "end_time": end,
            "purpose": "Clase de programación",
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

    def test_4_horas_1_minuto_rechazado(self, client, student_token, sample_space):
        """RES-02-B: duración 4h01m debe ser rechazada (HTTP 422)."""
        start = future_dt(48)
        end = future_dt(48) # Will add 4h1m below
        start_dt = datetime.now(timezone.utc) + timedelta(hours=48)
        end_dt = start_dt + timedelta(hours=4, minutes=1)
        resp = client.post("/reservations", json={
            "space_id": sample_space["id"],
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "purpose": "Reserva demasiado larga",
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
        assert "4 horas" in resp.json()["detail"][0]["msg"] or "4 horas" in str(resp.json())

    def test_5_horas_rechazado(self, client, student_token, sample_space):
        """RES-02-B: duración 5h debe ser rechazada (HTTP 422)."""
        start_dt = datetime.now(timezone.utc) + timedelta(hours=72)
        end_dt = start_dt + timedelta(hours=5)
        resp = client.post("/reservations", json={
            "space_id": sample_space["id"],
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "purpose": "Reserva excesiva",
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 422

    def test_duracion_cero_rechazada(self, client, student_token, sample_space):
        """RES-02-C: start == end debe retornar 422."""
        start_dt = datetime.now(timezone.utc) + timedelta(hours=10)
        resp = client.post("/reservations", json={
            "space_id": sample_space["id"],
            "start_time": start_dt.isoformat(),
            "end_time": start_dt.isoformat(),
            "purpose": "Reserva instantánea",
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 422

    def test_1_hora_valido(self, client, student_token, sample_space):
        """Reserva de 1 hora es válida."""
        resp = make_reservation(client, student_token, sample_space["id"],
                                start_offset_h=100, duration_h=1)
        assert resp.status_code == 201

    def test_3_horas_59_minutos_valido(self, client, student_token, sample_space):
        """3h59m debe ser aceptado."""
        start_dt = datetime.now(timezone.utc) + timedelta(hours=200)
        end_dt = start_dt + timedelta(hours=3, minutes=59)
        resp = client.post("/reservations", json={
            "space_id": sample_space["id"],
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "purpose": "Laboratorio extenso",
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 201


# ─── Conflictos (RES-03) ─────────────────────────────────────────────────────

class TestConflictos:
    """Spec: RES-03 — detección y prevención de conflictos."""

    def test_solapamiento_parcial_rechazado(self, client, student_token, admin_token, sample_space):
        """RES-03-A: solapamiento parcial retorna 409."""
        # First reservation: 10h-12h from now
        r1 = make_reservation(client, student_token, sample_space["id"],
                               start_offset_h=500, duration_h=2)
        assert r1.status_code == 201

        # Second: 11h-13h (overlaps)
        start_dt = datetime.now(timezone.utc) + timedelta(hours=501)
        end_dt = start_dt + timedelta(hours=2)
        r2 = client.post("/reservations", json={
            "space_id": sample_space["id"],
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "purpose": "Conflicto intencional",
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert r2.status_code == 409
        assert "disponible" in r2.json()["detail"].lower() or "conflicto" in r2.json()["detail"].lower() or "horario" in r2.json()["detail"].lower()

    def test_horarios_adyacentes_no_conflicto(self, client, student_token, sample_space):
        """RES-03-C: reservas adyacentes (sin solapamiento) deben aceptarse."""
        r1 = make_reservation(client, student_token, sample_space["id"],
                               start_offset_h=600, duration_h=2)
        assert r1.status_code == 201

        # Adjacent: starts exactly when first ends
        start_dt = datetime.now(timezone.utc) + timedelta(hours=602)
        end_dt = start_dt + timedelta(hours=2)
        r2 = client.post("/reservations", json={
            "space_id": sample_space["id"],
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "purpose": "Reserva adyacente",
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert r2.status_code == 201

    def test_reserva_pasada_rechazada(self, client, student_token, sample_space):
        """RES-01-C: start_time en el pasado retorna 422 (servicio) o similar."""
        past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        end = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        resp = client.post("/reservations", json={
            "space_id": sample_space["id"],
            "start_time": past,
            "end_time": end,
            "purpose": "Reserva pasada",
        }, headers={"Authorization": f"Bearer {student_token}"})
        # 422 from schema or 422 from service
        assert resp.status_code in (422, 409, 400)


# ─── Consulta de Disponibilidad (RES-04) ────────────────────────────────────

class TestDisponibilidad:
    """Spec: RES-04"""

    def test_disponibilidad_positiva(self, client, student_token, sample_space):
        """RES-04-A: espacio libre retorna available=true."""
        start = future_dt(1000)
        end = future_dt(1001)
        resp = client.get(
            f"/reservations/availability?space_id={sample_space['id']}&start_time={start}&end_time={end}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["available"] is True
        assert resp.json()["conflicts"] == []

    def test_disponibilidad_negativa(self, client, student_token, sample_space):
        """RES-04-B: espacio ocupado retorna available=false con conflictos."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=2000, duration_h=2)
        assert r.status_code == 201

        start = future_dt(2000)
        end = future_dt(2002)
        resp = client.get(
            f"/reservations/availability?space_id={sample_space['id']}&start_time={start}&end_time={end}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["available"] is False
        assert len(resp.json()["conflicts"]) >= 1


# ─── Aprobación (APR-02) ────────────────────────────────────────────────────

class TestAprobacion:
    """Spec: APR-02"""

    def test_aprobar_reserva_pendiente(self, client, student_token, admin_token, sample_space):
        """APR-02-A: admin aprueba reserva PENDING."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=3000, duration_h=1)
        rid = r.json()["id"]
        resp = client.put(f"/admin/reservations/{rid}/approve",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "APPROVED"
        assert resp.json()["approved_by"] is not None

    def test_aprobar_reserva_no_pending(self, client, student_token, admin_token, sample_space):
        """APR-02-D: no se puede aprobar reserva que ya fue aprobada."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=4000, duration_h=1)
        rid = r.json()["id"]
        client.put(f"/admin/reservations/{rid}/approve",
                   headers={"Authorization": f"Bearer {admin_token}"})
        # Try to approve again
        resp = client.put(f"/admin/reservations/{rid}/approve",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 409

    def test_aprobar_reserva_inexistente(self, client, admin_token):
        """APR-02-C: ID inexistente retorna 404."""
        resp = client.put("/admin/reservations/99999/approve",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404

    def test_estudiante_no_puede_aprobar(self, client, student_token, sample_space):
        """USR-03-A: estudiante no puede aprobar reservas."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=5000, duration_h=1)
        rid = r.json()["id"]
        resp = client.put(f"/admin/reservations/{rid}/approve",
                          headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 403


# ─── Rechazo (APR-03) ───────────────────────────────────────────────────────

class TestRechazo:
    """Spec: APR-03"""

    def test_rechazar_con_motivo(self, client, student_token, admin_token, sample_space):
        """APR-03-A: rechazar con motivo válido."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=6000, duration_h=1)
        rid = r.json()["id"]
        resp = client.put(f"/admin/reservations/{rid}/reject",
                          json={"reason": "El espacio requiere mantenimiento ese día"},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"
        assert resp.json()["rejection_reason"] is not None

    def test_rechazar_sin_motivo(self, client, student_token, admin_token, sample_space):
        """APR-03-B: rechazo sin motivo retorna 422."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=7000, duration_h=1)
        rid = r.json()["id"]
        resp = client.put(f"/admin/reservations/{rid}/reject",
                          json={"reason": ""},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 422

    def test_rechazar_reserva_aprobada(self, client, student_token, admin_token, sample_space):
        """APR-03-C: no se puede rechazar una reserva APPROVED."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=8000, duration_h=1)
        rid = r.json()["id"]
        client.put(f"/admin/reservations/{rid}/approve",
                   headers={"Authorization": f"Bearer {admin_token}"})
        resp = client.put(f"/admin/reservations/{rid}/reject",
                          json={"reason": "Cambio de decisión"},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 409


# ─── Cancelación (HST-02) ───────────────────────────────────────────────────

class TestCancelacion:
    """Spec: HST-02"""

    def test_cancelacion_exitosa_por_propietario(self, client, student_token, sample_space):
        """HST-02-A: propietario cancela reserva futura."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=9000, duration_h=1)
        rid = r.json()["id"]
        resp = client.delete(f"/reservations/{rid}",
                             headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    def test_cancelacion_doble_rechazada(self, client, student_token, sample_space):
        """HST-02-D: no se puede cancelar una reserva ya cancelada."""
        r = make_reservation(client, student_token, sample_space["id"],
                             start_offset_h=10000, duration_h=1)
        rid = r.json()["id"]
        client.delete(f"/reservations/{rid}",
                      headers={"Authorization": f"Bearer {student_token}"})
        resp = client.delete(f"/reservations/{rid}",
                             headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 409


# ─── Historial (HST-01) ─────────────────────────────────────────────────────

class TestHistorial:
    """Spec: HST-01"""

    def test_historial_vacio(self, client, student_token):
        """HST-01-B: usuario sin reservas retorna lista vacía."""
        resp = client.get("/users/me/reservations",
                          headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_historial_con_reservas(self, client, student_token, sample_space):
        """HST-01-A: historial muestra reservas del usuario."""
        make_reservation(client, student_token, sample_space["id"],
                         start_offset_h=11000, duration_h=1)
        resp = client.get("/users/me/reservations",
                          headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
