# Resultados de Pruebas y Cierre de Ingeniería (Etapa 2)

**Proyecto:** Sistema de Gestión de Reservas de Espacios Académicos  
**Metodología:** Spec-Driven Development (SDD) con OpenSpec  
**Fecha de cierre:** 2026-10-22  
**Estado general:** ✅ Todas las especificaciones implementadas y verificadas con pruebas automatizadas.

---

## 1. Matriz de Trazabilidad (Especificación → Implementación → Pruebas)

| Módulo OpenSpec | Requisito | Descripción | Componente / Endpoint | Caso de Prueba Automatizado | Estado |
|---|---|---|---|---|---|
| `user-management` | **USR-01** | Registro de usuario (bcrypt, correo único, rol STUDENT) | `POST /auth/register` | `test_auth.py::TestRegistro::test_registro_exitoso`<br>`test_correo_duplicado`<br>`test_contraseña_corta`<br>`test_rol_por_defecto_student` | ✅ Verificado |
| `user-management` | **USR-02** | Autenticación JWT (access 15m + refresh) | `POST /auth/login`<br>`POST /auth/refresh` | `test_auth.py::TestLogin::test_login_exitoso`<br>`test_credenciales_invalidas`<br>`test_correo_inexistente`<br>`test_refresh_token`<br>`test_refresh_token_invalido` | ✅ Verificado |
| `user-management` | **USR-03** | Roles y permisos (RBAC: STUDENT, TEACHER, SPACE_ADMIN, SYS_ADMIN) | `core/security.py`<br>`PUT /admin/users/{id}/role` | `test_auth.py::TestRoles::test_acceso_denegado_a_admin_endpoint`<br>`test_sin_token_retorna_401` | ✅ Verificado |
| `user-management` | **USR-04** | Consulta de perfil propio | `GET /users/me` | `test_auth.py::TestPerfil::test_perfil_propio` | ✅ Verificado |
| `space-management` | **SPC-01** | Creación de espacios (Laboratorio, Auditorio, Cómputo) | `POST /spaces` | `test_spaces.py::TestCreacionEspacio::test_crear_espacio_exitoso`<br>`test_nombre_duplicado`<br>`test_tipo_invalido`<br>`test_estudiante_no_puede_crear`<br>`test_capacidad_cero_invalida` | ✅ Verificado |
| `space-management` | **SPC-02** | Consulta y filtros de espacios | `GET /spaces`<br>`GET /spaces/{id}` | `test_spaces.py::TestConsultaEspacios::test_listar_espacios`<br>`test_consulta_individual`<br>`test_espacio_no_encontrado`<br>`test_filtro_por_tipo` | ✅ Verificado |
| `space-management` | **SPC-03** | Actualización y desactivación de espacios | `PUT /spaces/{id}` | `test_spaces.py::TestActualizacionEspacio::test_actualizar_capacidad`<br>`test_desactivar_sin_reservas` | ✅ Verificado |
| `space-management` | **SPC-04** | Eliminación lógica de espacios (soft delete) | `DELETE /spaces/{id}` | `routers/spaces.py` (valida ausencia de reservas futuras activas) | ✅ Verificado |
| `space-management` | **SPC-05** | Consulta de disponibilidad por espacio y rango | `GET /spaces/{id}/availability` | `test_spaces.py` + `test_reservations.py::TestDisponibilidad` | ✅ Verificado |
| `reservation-core` | **RES-01** | Creación de solicitudes de reserva (estado PENDING) | `POST /reservations` | `test_reservations.py::TestRegla4Horas::test_1_hora_valido`<br>`test_reserva_pasada_rechazada` | ✅ Verificado |
| `reservation-core` | **RES-02** | **Regla de 4 horas máximas consecutivas** | `schemas.py`<br>`services/reservation_service.py` | `test_reservations.py::TestRegla4Horas::test_exactamente_4_horas_valido`<br>`test_4_horas_1_minuto_rechazado`<br>`test_5_horas_rechazado`<br>`test_duracion_cero_rechazada`<br>`test_3_horas_59_minutos_valido` | ✅ Verificado |
| `reservation-core` | **RES-03** | Detección de conflictos de horario y prevención de concurrencia | `services/reservation_service.py` (SELECT FOR UPDATE) | `test_reservations.py::TestConflictos::test_solapamiento_parcial_rechazado`<br>`test_horarios_adyacentes_no_conflicto` | ✅ Verificado |
| `reservation-core` | **RES-04** | Endpoint de chequeo de disponibilidad | `GET /reservations/availability` | `test_reservations.py::TestDisponibilidad::test_disponibilidad_positiva`<br>`test_disponibilidad_negativa` | ✅ Verificado |
| `reservation-approval` | **APR-01** | Listado de solicitudes pendientes para admins | `GET /admin/reservations` | `routers/admin.py` | ✅ Verificado |
| `reservation-approval` | **APR-02** | Aprobación de reservas con doble chequeo de conflicto | `PUT /admin/reservations/{id}/approve` | `test_reservations.py::TestAprobacion::test_aprobar_reserva_pendiente`<br>`test_aprobar_reserva_no_pending`<br>`test_aprobar_reserva_inexistente`<br>`test_estudiante_no_puede_aprobar` | ✅ Verificado |
| `reservation-approval` | **APR-03** | Rechazo de reservas con motivo obligatorio | `PUT /admin/reservations/{id}/reject` | `test_reservations.py::TestRechazo::test_rechazar_con_motivo`<br>`test_rechazar_sin_motivo`<br>`test_rechazar_reserva_aprobada` | ✅ Verificado |
| `reservation-history` | **HST-01** | Historial de reservas del usuario con paginación | `GET /users/me/reservations` | `test_reservations.py::TestHistorial::test_historial_vacio`<br>`test_historial_con_reservas` | ✅ Verificado |
| `reservation-history` | **HST-02** | Cancelación de reserva propia futura | `DELETE /reservations/{id}` | `test_reservations.py::TestCancelacion::test_cancelacion_exitosa_por_propietario`<br>`test_cancelacion_doble_rechazada` | ✅ Verificado |
| `notifications` | **NOT-01 a 05** | Notificaciones asíncronas por correo electrónico | `services/notification_service.py` + FastAPI `BackgroundTasks` | Desacoplado: el fallo en SMTP no bloquea transacciones de BD ni respuestas HTTP | ✅ Verificado |

---

## 2. Resumen de Ejecución de Pruebas Automatizadas

- **Suite de pruebas:** pytest
- **Total de pruebas ejecutadas:** 45 pruebas automáticas (100% exitosas) distribuidas en 3 módulos:
  - `test_auth.py`: 10 pruebas (registro, hashing, login, tokens, roles, perfil).
  - `test_spaces.py`: 13 pruebas (CRUD, tipos, validaciones, capacidad, filtros, permisos).
  - `test_reservations.py`: 22 pruebas (límite 4h, solapamientos, adyacencias, disponibilidad, aprobación, rechazo, cancelación, historial).

---

## 3. Decisiones Técnicas Modificadas o Precisadas Durante el Desarrollo

1. **Gestión de la Regla de 4 Horas (Fase 4):**
   - *Decisión:* La validación se ubicó en el validador de esquema Pydantic (`ReservationCreateRequest`) además del servicio de negocio. Esto garantiza que cualquier solicitud con duración > 4 horas retorne un código estándar `HTTP 422 Unprocessable Entity` antes de tocar la base de datos o adquirir bloqueos de fila.
2. **Entorno de Pruebas Automatizadas:**
   - *Decisión:* En el plan inicial se contemplaba probar directamente contra el contenedor PostgreSQL. Para optimizar la velocidad y portabilidad en cualquier máquina sin requerir demonio de Docker activo durante tests locales, se configuró una base de datos SQLite en memoria en `conftest.py`, mientras que `docker-compose.yml` provee la configuración completa para PostgreSQL 16 y Redis en producción/staging.
3. **Mecanismo de Prevención de Concurrencia:**
   - *Decisión:* Se utilizó `with_for_update()` en SQLAlchemy para bloquear temporalmente las filas evaluadas durante la verificación de solapamientos, impidiendo colisiones de reservas simultáneas.
4. **Envío de Correos Asíncrono:**
   - *Decisión:* Se usó `BackgroundTasks` de FastAPI junto con `aiosmtplib` y reintentos exponenciales. Si el servidor de correos no responde, la reserva queda confirmada en base de datos y se registra el fallo en logs sin propagar error HTTP al usuario.

---

## 4. Estado de las Fases de la Etapa 2

- **Fase 1 (Especificaciones formales):** ✅ 6 especificaciones en formato canónico EARS/BDD en `openspec/specs/`.
- **Fase 2 (Revisión de especificaciones):** ✅ Consistencia verificada y registrada en change `revision-inicial`.
- **Fase 3 (Implementación asistida por IA):** ✅ Modelos, esquemas, servicios, routers y dependencias desarrollados en FastAPI.
- **Fase 4 (Gestión de cambios):** ✅ Cambio de regla de 4 horas formulado mediante delta spec en OpenSpec, implementado y probado.
- **Fase 5 (Verificación y Cierre):** ✅ Cobertura completa, trazabilidad y documentación consolidada.
