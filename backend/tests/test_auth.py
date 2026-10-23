"""
Tests for user-management spec.
Covers: USR-01 (registro), USR-02 (login/JWT), USR-03 (roles), USR-04 (perfil).
"""
import pytest


class TestRegistro:
    """Spec: USR-01"""

    def test_registro_exitoso(self, client):
        """USR-01-A: registro con datos válidos retorna 201."""
        resp = client.post("/auth/register", json={
            "full_name": "Juan Pérez",
            "email": "juan@universidad.edu",
            "password": "password123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "juan@universidad.edu"
        assert data["role"] == "STUDENT"
        assert "hashed_password" not in data

    def test_correo_duplicado(self, client):
        """USR-01-B: correo ya registrado retorna 409."""
        payload = {"full_name": "Test", "email": "dup@uni.edu", "password": "pass1234"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409
        assert "ya está registrado" in resp.json()["detail"]

    def test_contraseña_corta(self, client):
        """USR-01-C: contraseña < 8 caracteres retorna 422."""
        resp = client.post("/auth/register", json={
            "full_name": "X", "email": "x@uni.edu", "password": "short"
        })
        assert resp.status_code == 422

    def test_rol_por_defecto_student(self, client):
        """USR-01: el rol por defecto es STUDENT."""
        resp = client.post("/auth/register", json={
            "full_name": "Nuevo", "email": "nuevo@uni.edu", "password": "password123"
        })
        assert resp.json()["role"] == "STUDENT"


class TestLogin:
    """Spec: USR-02"""

    def test_login_exitoso(self, client, registered_student):
        """USR-02-A: login con credenciales válidas retorna tokens."""
        resp = client.post("/auth/login", json={
            "email": "ana@universidad.edu", "password": "password123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_credenciales_invalidas(self, client, registered_student):
        """USR-02-B: password incorrecto retorna 401."""
        resp = client.post("/auth/login", json={
            "email": "ana@universidad.edu", "password": "wrongpass"
        })
        assert resp.status_code == 401
        assert "Credenciales inválidas" in resp.json()["detail"]

    def test_correo_inexistente(self, client):
        """USR-02-B: correo no registrado retorna 401."""
        resp = client.post("/auth/login", json={
            "email": "ghost@uni.edu", "password": "anypass123"
        })
        assert resp.status_code == 401

    def test_refresh_token(self, client, registered_student):
        """USR-02-C: refresh token válido emite nuevo access_token."""
        login = client.post("/auth/login", json={
            "email": "ana@universidad.edu", "password": "password123"
        }).json()
        resp = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_token_invalido(self, client):
        """USR-02-D: refresh token inválido retorna 401."""
        resp = client.post("/auth/refresh", json={"refresh_token": "not.a.valid.token"})
        assert resp.status_code == 401


class TestRoles:
    """Spec: USR-03"""

    def test_acceso_denegado_a_admin_endpoint(self, client, student_token):
        """USR-03-A: estudiante no puede acceder a endpoint admin."""
        resp = client.get(
            "/admin/reservations",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert resp.status_code == 403

    def test_sin_token_retorna_401(self, client):
        """USR-04-B: sin Bearer token retorna 401."""
        resp = client.get("/users/me")
        assert resp.status_code == 401


class TestPerfil:
    """Spec: USR-04"""

    def test_perfil_propio(self, client, student_token, registered_student):
        """USR-04-A: usuario autenticado obtiene su perfil."""
        resp = client.get("/users/me", headers={"Authorization": f"Bearer {student_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "ana@universidad.edu"
        assert data["role"] == "STUDENT"
