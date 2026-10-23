# User Management and Authentication Specification

## Purpose
Define los requisitos para el registro, autenticación, gestión de roles y emisión de tokens JWT del sistema de reservas académicas.

## Requirements

### Requirement: USR-01 Registro de Usuario
El sistema SHALL permitir que cualquier persona se registre proporcionando nombre completo, correo institucional único y contraseña segura.

**Restricciones:**
- El correo electrónico MUST ser único en el sistema.
- La contraseña MUST tener mínimo 8 caracteres.
- La contraseña SHALL almacenarse como hash bcrypt (nunca en texto plano).
- El rol por defecto SHALL ser `STUDENT`.

#### Scenario: USR-01-A Registro exitoso
- **GIVEN** un correo institucional no registrado y una contraseña de 8+ caracteres
- **WHEN** se envía `POST /auth/register` con nombre, correo y contraseña
- **THEN** el sistema SHALL retornar HTTP 201 con los datos del usuario (sin contraseña) y el rol asignado

#### Scenario: USR-01-B Correo duplicado
- **GIVEN** un correo ya registrado en el sistema
- **WHEN** se envía `POST /auth/register` con ese correo
- **THEN** el sistema SHALL retornar HTTP 409 con mensaje `"El correo ya está registrado"`

#### Scenario: USR-01-C Contraseña inválida
- **GIVEN** una contraseña de menos de 8 caracteres
- **WHEN** se envía `POST /auth/register`
- **THEN** el sistema SHALL retornar HTTP 422 con detalle de la validación fallida

### Requirement: USR-02 Autenticación con JWT
El sistema SHALL autenticar usuarios mediante correo y contraseña, emitiendo un token de acceso (15 min) y un token de refresco (7 días).

**Restricciones:**
- El token de acceso SHALL ser un JWT firmado con HS256.
- El token de refresco SHALL almacenarse en Redis con TTL de 7 días.
- Tras 5 intentos fallidos consecutivos, el sistema SHOULD bloquear la cuenta temporalmente (15 min).

#### Scenario: USR-02-A Login exitoso
- **GIVEN** un usuario registrado con credenciales válidas
- **WHEN** se envía `POST /auth/login` con correo y contraseña correctos
- **THEN** el sistema SHALL retornar HTTP 200 con `access_token`, `refresh_token` y `token_type: bearer`

#### Scenario: USR-02-B Credenciales inválidas
- **GIVEN** credenciales incorrectas (correo inexistente o contraseña errónea)
- **WHEN** se envía `POST /auth/login`
- **THEN** el sistema SHALL retornar HTTP 401 con mensaje `"Credenciales inválidas"`

#### Scenario: USR-02-C Renovación de token
- **GIVEN** un `refresh_token` válido y no expirado
- **WHEN** se envía `POST /auth/refresh`
- **THEN** el sistema SHALL retornar HTTP 200 con un nuevo `access_token`

#### Scenario: USR-02-D Refresh token expirado
- **GIVEN** un `refresh_token` expirado o inválido
- **WHEN** se envía `POST /auth/refresh`
- **THEN** el sistema SHALL retornar HTTP 401 con mensaje `"Token de refresco inválido o expirado"`

### Requirement: USR-03 Roles y Permisos
El sistema SHALL implementar control de acceso basado en roles (RBAC) con cuatro roles distintos: `STUDENT`, `TEACHER`, `SPACE_ADMIN`, `SYS_ADMIN`.

#### Scenario: USR-03-A Acceso denegado por rol insuficiente
- **GIVEN** un usuario con rol `STUDENT`
- **WHEN** intenta acceder a `PUT /admin/reservations/{id}/approve`
- **THEN** el sistema SHALL retornar HTTP 403 con mensaje `"No tienes permisos para esta acción"`

#### Scenario: USR-03-B Cambio de rol por administrador
- **GIVEN** un `SYS_ADMIN` autenticado y un `user_id` existente
- **WHEN** se envía `PUT /admin/users/{user_id}/role` con el nuevo rol
- **THEN** el sistema SHALL retornar HTTP 200 con los datos actualizados del usuario

### Requirement: USR-04 Consulta del Perfil Propio
El sistema SHALL permitir que cualquier usuario autenticado consulte su propio perfil.

#### Scenario: USR-04-A Consulta exitosa
- **GIVEN** un usuario con token de acceso válido
- **WHEN** se envía `GET /users/me`
- **THEN** el sistema SHALL retornar HTTP 200 con nombre, correo, rol y fecha de registro

#### Scenario: USR-04-B Sin token
- **GIVEN** una solicitud sin header `Authorization`
- **WHEN** se envía `GET /users/me`
- **THEN** el sistema SHALL retornar HTTP 401 con mensaje `"No autenticado"`
