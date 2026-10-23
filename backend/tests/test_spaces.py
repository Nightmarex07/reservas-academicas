"""
Tests for space-management spec.
Covers: SPC-01 (creación), SPC-02 (consulta), SPC-03 (actualización), SPC-04 (eliminación).
"""
import pytest


class TestCreacionEspacio:
    """Spec: SPC-01"""

    def test_crear_espacio_exitoso(self, client, admin_token):
        """SPC-01-A: admin crea espacio con datos válidos."""
        resp = client.post("/spaces", json={
            "name": "Auditorio Principal",
            "type": "AUDITORIUM",
            "capacity": 200,
            "location": "Edificio Central",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Auditorio Principal"
        assert data["type"] == "AUDITORIUM"
        assert data["is_active"] is True

    def test_nombre_duplicado(self, client, admin_token, sample_space):
        """SPC-01-B: nombre duplicado retorna 409."""
        resp = client.post("/spaces", json={
            "name": sample_space["name"],
            "type": "LABORATORY",
            "capacity": 10,
            "location": "Otro lugar",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 409
        assert "Ya existe" in resp.json()["detail"]

    def test_tipo_invalido(self, client, admin_token):
        """SPC-01-C: tipo de espacio inválido retorna 422."""
        resp = client.post("/spaces", json={
            "name": "Test", "type": "CLASSROOM", "capacity": 10, "location": "X"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 422

    def test_estudiante_no_puede_crear(self, client, student_token):
        """SPC-01-D: estudiante recibe 403 al intentar crear espacio."""
        resp = client.post("/spaces", json={
            "name": "Intento", "type": "LABORATORY", "capacity": 5, "location": "X"
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 403

    def test_capacidad_cero_invalida(self, client, admin_token):
        """Capacidad 0 debe retornar 422."""
        resp = client.post("/spaces", json={
            "name": "Test Cap", "type": "LABORATORY", "capacity": 0, "location": "X"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 422


class TestConsultaEspacios:
    """Spec: SPC-02"""

    def test_listar_espacios(self, client, student_token, sample_space):
        """SPC-02-A: listar espacios activos."""
        resp = client.get("/spaces?is_active=true",
                          headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_consulta_individual(self, client, student_token, sample_space):
        """SPC-02-B: consultar espacio por ID."""
        resp = client.get(f"/spaces/{sample_space['id']}",
                          headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == sample_space["id"]

    def test_espacio_no_encontrado(self, client, student_token):
        """SPC-02-C: ID inexistente retorna 404."""
        resp = client.get("/spaces/99999",
                          headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 404
        assert "no encontrado" in resp.json()["detail"].lower()

    def test_filtro_por_tipo(self, client, admin_token, sample_space):
        """Filtrar por tipo LABORATORY."""
        resp = client.get("/spaces?type=LABORATORY",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        for space in resp.json():
            assert space["type"] == "LABORATORY"


class TestActualizacionEspacio:
    """Spec: SPC-03"""

    def test_actualizar_capacidad(self, client, admin_token, sample_space):
        """SPC-03-A: actualizar capacidad."""
        resp = client.put(f"/spaces/{sample_space['id']}", json={"capacity": 50},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["capacity"] == 50

    def test_desactivar_sin_reservas(self, client, admin_token, sample_space):
        """SPC-03: desactivar espacio sin reservas activas."""
        resp = client.put(f"/spaces/{sample_space['id']}", json={"is_active": False},
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False
