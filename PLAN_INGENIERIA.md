# PLAN DE INGENIERÍA DE SOFTWARE
## Sistema de Gestión de Reservas de Espacios Académicos

**Modalidad:** Individual  
**Metodología:** Spec-Driven Development (SDD) con OpenSpec  
**Fecha:** 2026-10-22  

---

## 1. Análisis del Problema

### 1.1 Identificación de la Problemática

La institución universitaria gestiona actualmente sus reservas de espacios académicos (laboratorios, auditorios y salas de cómputo) mediante correos electrónicos y hojas de cálculo. Este enfoque manual genera los siguientes problemas críticos:

| Problema | Impacto |
|---|---|
| **Duplicidad de solicitudes** | Dos o más actores reservan el mismo espacio simultáneamente sin notificarse. |
| **Conflictos de horario** | No existe un mecanismo centralizado que bloquee una franja horaria ya ocupada. |
| **Opacidad en disponibilidad** | Consultar si un espacio está libre requiere revisar varias hojas y enviar correos, proceso lento y propenso a errores. |
| **Trazabilidad nula** | No hay historial consolidado de reservas pasadas ni métricas de uso. |
| **Escalabilidad limitada** | Con el crecimiento de la institución el proceso manual se vuelve inmanejable. |

### 1.2 Necesidades de la Institución

1. **Centralización:** un único repositorio de verdad para todas las reservas.
2. **Control de conflictos en tiempo real:** validación automática de solapamientos horarios.
3. **Consulta de disponibilidad:** vista de calendario por espacio, edificio y fecha.
4. **Notificaciones:** confirmación, recordatorio y cancelación automáticos.
5. **Gestión administrativa:** aprobar, rechazar o cancelar reservas por parte de administradores.
6. **Trazabilidad:** historial completo de reservas y reportes de uso por espacio.
7. **Roles diferenciados:** distintos niveles de acceso para estudiantes, docentes y administradores.

### 1.3 Actores Involucrados

```
┌─────────────────────────────────────────────────────────────┐
│                      ACTORES DEL SISTEMA                    │
├──────────────────┬──────────────────────────────────────────┤
│ Actor            │ Responsabilidades / Acciones             │
├──────────────────┼──────────────────────────────────────────┤
│ Estudiante       │ Solicitar reservas, consultar            │
│                  │ disponibilidad, cancelar propias         │
├──────────────────┼──────────────────────────────────────────┤
│ Docente          │ Reservar para clases/prácticas,          │
│                  │ prioridad sobre estudiantes              │
├──────────────────┼──────────────────────────────────────────┤
│ Administrador    │ CRUD completo de espacios, aprobar o     │
│ de Espacios      │ rechazar solicitudes, gestionar          │
│                  │ mantenimientos, generar reportes         │
├──────────────────┼──────────────────────────────────────────┤
│ Administrador    │ Gestión de usuarios, roles y             │
│ del Sistema      │ configuración global                     │
├──────────────────┼──────────────────────────────────────────┤
│ Sistema de       │ Actor externo: recibe notificaciones     │
│ Correo (SMTP)    │ disparadas por el sistema                │
└──────────────────┴──────────────────────────────────────────┘
```

### 1.4 Alcance y Limitaciones

**Dentro del alcance (in-scope):**
- Gestión de reservas de laboratorios, auditorios y salas de cómputo.
- Autenticación y autorización con roles (estudiante, docente, administrador).
- Consulta de disponibilidad con vista de calendario.
- Notificaciones por correo electrónico.
- Panel administrativo para gestión de espacios y reportes básicos.
- API RESTful consumible por clientes web.

**Fuera del alcance (out-of-scope):**
- Integración con sistemas de nómina o carné universitario (se deja para fases futuras).
- Pagos o tarifas por uso de espacios.
- Aplicación móvil nativa (el frontend web será responsivo).
- Gestión de inventario del equipamiento interno de cada espacio.
- Videoconferencia o streaming desde los espacios.

---

## 2. Propuesta de Solución

### 2.1 Descripción General

Se propone desarrollar una **aplicación web fullstack** con arquitectura cliente-servidor, donde el backend expone una API RESTful y el frontend ofrece una interfaz reactiva. El sistema centralizará todas las reservas, aplicará validaciones de conflicto en el servidor y notificará a los actores mediante correo electrónico.

```
┌──────────────┐      HTTPS/JSON      ┌─────────────────┐
│   Frontend   │◄────────────────────►│  Backend API    │
│  (React SPA) │                      │  (FastAPI)      │
└──────────────┘                      └────────┬────────┘
                                               │
                              ┌────────────────┼────────────────┐
                              │                │                │
                       ┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
                       │ PostgreSQL  │  │    Redis    │  │   SMTP     │
                       │  (datos)    │  │  (caché /   │  │  (correo)  │
                       └─────────────┘  │   sesiones) │  └────────────┘
                                        └─────────────┘
```

### 2.2 Funcionalidades Prioritarias

Ordenadas por valor de negocio (MoSCoW):

**Must Have (esenciales):**
1. Registro e inicio de sesión con JWT.
2. CRUD de espacios académicos (solo administrador).
3. Creación de reservas con validación de conflictos.
4. Consulta de disponibilidad por espacio y rango de fechas.
5. Cancelación de reservas propias.

**Should Have (importantes):**
6. Notificaciones por correo (confirmación, cancelación, recordatorio).
7. Panel de administración para aprobar/rechazar solicitudes.
8. Historial de reservas por usuario.
9. Vista de calendario con disponibilidad visual.

**Could Have (deseables):**
10. Reportes de uso por espacio y período.
11. Búsqueda y filtrado avanzado de espacios.
12. Gestión de mantenimientos (bloquear espacio por mantenimiento).

**Won't Have (fuera de alcance actual):**
13. Integración con sistemas externos (LDAP, ERP).
14. Aplicación móvil nativa.

### 2.3 Organización en Módulos

```
reservas-academicas/
├── backend/
│   ├── auth/           # Autenticación, JWT, roles
│   ├── users/          # Gestión de usuarios
│   ├── spaces/         # Espacios académicos (CRUD)
│   ├── reservations/   # Lógica de reservas y conflictos
│   ├── notifications/  # Envío de correos
│   └── reports/        # Generación de reportes
└── frontend/
    ├── auth/           # Login / registro
    ├── spaces/         # Catálogo de espacios
    ├── reservations/   # Formulario y lista de reservas
    ├── calendar/       # Vista de disponibilidad
    └── admin/          # Panel administrativo
```

### 2.4 Estrategia de Desarrollo Progresivo

Se adopta un enfoque **incremental por capas**, priorizando el núcleo funcional antes de añadir características periféricas:

| Incremento | Contenido |
|---|---|
| **I-0** | Infraestructura base: repositorio, CI, BD, entornos |
| **I-1** | Autenticación y gestión de usuarios |
| **I-2** | CRUD de espacios y consulta de disponibilidad |
| **I-3** | Motor de reservas con validación de conflictos |
| **I-4** | Notificaciones y panel administrativo |
| **I-5** | Reportes, historial y mejoras de UX |

---

## 3. Decisiones de Arquitectura y Tecnología

### 3.1 Arquitectura Seleccionada

**Arquitectura elegida:** Monolito Modular con API RESTful

**Justificación:**
- El sistema tiene un dominio acotado y un equipo unipersonal; los microservicios agregarían complejidad operativa sin beneficio real en esta escala.
- El monolito modular permite separación clara de responsabilidades (módulos independientes) con la posibilidad de extraer servicios en el futuro si la carga lo justifica.
- Facilita el desarrollo, pruebas y despliegue en una sola unidad.

### 3.2 Stack Tecnológico Propuesto

| Capa | Tecnología | Versión |
|---|---|---|
| **Backend** | Python + FastAPI | 3.11 / 0.111+ |
| **ORM** | SQLAlchemy + Alembic | 2.x |
| **Base de datos** | PostgreSQL | 16 |
| **Caché / Sesiones** | Redis | 7 |
| **Autenticación** | JWT (python-jose) + bcrypt | — |
| **Correo** | SMTP + aiosmtplib | — |
| **Frontend** | React + TypeScript + Vite | 18 / 5+ |
| **UI Components** | Tailwind CSS + shadcn/ui | — |
| **Estado global** | Zustand | — |
| **Calendario** | FullCalendar | 6 |
| **Testing backend** | pytest + pytest-asyncio | — |
| **Testing frontend** | Vitest + Testing Library | — |
| **Contenedores** | Docker + Docker Compose | — |
| **CI/CD** | GitHub Actions | — |

### 3.3 Estrategia de Persistencia de Datos

- **PostgreSQL** como base de datos principal: soporte ACID, consultas complejas sobre rangos de tiempo (`TSRANGE`), índices eficientes.
- **Migraciones con Alembic:** cada cambio de esquema se versionará; sin modificaciones manuales a la base de datos.
- **Redis** para caché de disponibilidad y almacenamiento de tokens de refresco; reduce carga a la base de datos en consultas frecuentes.
- **Respaldo:** estrategia `pg_dump` programada (alcance futuro en producción).

### 3.4 Organización de Componentes

```
Backend (FastAPI)
├── main.py              # Punto de entrada, registro de routers
├── config.py            # Variables de entorno (pydantic-settings)
├── database.py          # Sesión SQLAlchemy
├── models/              # Modelos ORM
├── schemas/             # Pydantic schemas (request/response)
├── routers/             # Endpoints HTTP agrupados por módulo
├── services/            # Lógica de negocio (sin HTTP)
├── repositories/        # Acceso a datos (patrón Repository)
├── core/                # Seguridad, dependencias, utilidades
└── tests/               # Pruebas unitarias e integración

Frontend (React)
├── src/
│   ├── api/             # Clientes HTTP (axios / fetch wrappers)
│   ├── components/      # Componentes reutilizables
│   ├── pages/           # Vistas enrutadas
│   ├── stores/          # Estado global (Zustand)
│   ├── hooks/           # Custom hooks
│   └── utils/           # Funciones auxiliares
```

### 3.5 Comparación de Decisiones Técnicas

#### Decisión 1: Framework de Backend

| Opción | Ventajas | Desventajas | Decisión |
|---|---|---|---|
| **FastAPI** ✅ | Validación automática, docs OpenAPI integradas, async nativo, alto rendimiento | Ecosistema más pequeño que Django | **Elegido** |
| Django REST Framework | Ecosistema maduro, ORM propio, admin panel incluido | Overhead elevado, sync por defecto, opinionado | Descartado |
| Node.js + Express | Gran ecosistema JS, mismo lenguaje que frontend | Menor tipado, callback hell sin TypeScript estricto | Descartado |

**Justificación:** FastAPI genera documentación OpenAPI automáticamente, lo que es compatible con la filosofía SDD: las especificaciones de la API estarán siempre sincronizadas con la implementación.

#### Decisión 2: Base de Datos

| Opción | Ventajas | Desventajas | Decisión |
|---|---|---|---|
| **PostgreSQL** ✅ | ACID, TSRANGE, índices avanzados, open source | Requiere servidor dedicado | **Elegido** |
| MySQL / MariaDB | Popular, fácil de administrar | Soporte de tipos avanzados limitado, TSRANGE no nativo | Descartado |
| SQLite | Zero configuración | No apto para concurrencia de escritura; no es viable en producción | Descartado |

#### Decisión 3: Estrategia de Frontend

| Opción | Ventajas | Desventajas | Decisión |
|---|---|---|---|
| **React + TypeScript** ✅ | Gran ecosistema, tipado estático, SPA reactiva | Curva inicial de configuración | **Elegido** |
| Vue 3 + TypeScript | API de composición elegante, menos boilerplate | Ecosistema de componentes más pequeño | Descartado |
| Server-Side Rendering (Next.js) | SEO, carga inicial rápida | Complejidad adicional; el sistema es interno (sin SEO crítico) | Descartado |

---

## 4. Estrategia de Desarrollo

### 4.1 Metodología de Trabajo

Se aplicará **Spec-Driven Development (SDD)** dentro de un marco de trabajo **iterativo e incremental**:

1. **Especificar** → Redactar la spec del módulo en OpenSpec antes de codificar.
2. **Validar** → Revisar la spec (contratos de API, modelos de datos, flujos).
3. **Implementar** → Delegar generación de código al agente IA con la spec como referencia.
4. **Verificar** → Ejecutar pruebas automáticas; revisar manualmente el código generado.
5. **Integrar** → Commit, PR y revisión de integración.

### 4.2 Etapas de Implementación

```
Etapa 0 — Infraestructura y Configuración
├── Repositorio Git + .gitignore + README
├── Docker Compose (postgres, redis, backend, frontend)
├── Pipeline CI (GitHub Actions)
└── Variables de entorno y configuración base

Etapa 1 — Autenticación y Usuarios
├── Spec: auth.yaml, users.yaml
├── Modelos: User, Role
├── Endpoints: /auth/register, /auth/login, /auth/refresh
└── Pruebas: registro, login, JWT expirado

Etapa 2 — Gestión de Espacios
├── Spec: spaces.yaml
├── Modelos: Space, SpaceType
├── Endpoints: CRUD /spaces
└── Pruebas: creación, actualización, eliminación, listado

Etapa 3 — Motor de Reservas
├── Spec: reservations.yaml
├── Modelos: Reservation, ReservationStatus
├── Lógica: detección de conflictos de horario
├── Endpoints: /reservations (CRUD + disponibilidad)
└── Pruebas: conflictos, cancelación, estados

Etapa 4 — Notificaciones y Administración
├── Spec: notifications.yaml, admin.yaml
├── Cola de tareas asíncronas (BackgroundTasks FastAPI)
├── Templates de correo (HTML)
└── Panel admin: aprobar/rechazar reservas

Etapa 5 — Reportes y Refinamiento
├── Spec: reports.yaml
├── Endpoints de estadísticas de uso
├── Frontend: mejoras UX, calendario visual
└── Pruebas end-to-end
```

### 4.3 Orden de Desarrollo de Funcionalidades

```
[I-0] Infraestructura
    └──► [I-1] Autenticación
              └──► [I-2] Espacios
                        └──► [I-3] Reservas ◄── (núcleo crítico)
                                  └──► [I-4] Notificaciones + Admin
                                            └──► [I-5] Reportes + UX
```

### 4.4 Dependencias entre Componentes

| Componente | Depende de |
|---|---|
| `reservations` | `spaces`, `users`, `auth` |
| `notifications` | `reservations`, `users` |
| `reports` | `reservations`, `spaces` |
| `admin` | `auth` (rol administrador), `spaces`, `reservations` |
| Frontend `calendar` | API `reservations` |

### 4.5 Criterios de Terminación por Etapa (Definition of Done)

Una etapa se considera **terminada** cuando:
- ✅ Especificaciones en OpenSpec revisadas y aprobadas.
- ✅ Todos los endpoints del módulo retornan los status codes correctos.
- ✅ Cobertura de pruebas unitarias ≥ 80 % en la lógica de negocio del módulo.
- ✅ Pruebas de integración del módulo pasan sin errores.
- ✅ Sin vulnerabilidades críticas detectadas por linter de seguridad (`bandit`).
- ✅ Código revisado y mergeado en rama principal vía PR.
- ✅ Documentación OpenAPI actualizada y accesible en `/docs`.

---

## 5. Estrategia de Calidad

### 5.1 Tipos de Pruebas

| Tipo | Herramienta | Qué cubre |
|---|---|---|
| **Unitarias** | pytest | Lógica de negocio pura: detección de conflictos, validaciones, transformaciones |
| **Integración** | pytest + TestClient (FastAPI) | Endpoints HTTP completos con BD de prueba en memoria (SQLite) |
| **Contrato de API** | Validación OpenSpec | Respuestas del servidor cumplen el schema definido en la spec |
| **Frontend (unitarias)** | Vitest + Testing Library | Componentes React aislados con mocks |
| **End-to-End** | Playwright | Flujos críticos: registro → reserva → cancelación en navegador real |
| **Rendimiento** | Locust | Pruebas de carga en endpoint de disponibilidad (50 usuarios concurrentes) |
| **Seguridad** | bandit (Python) | Análisis estático de vulnerabilidades en el backend |

### 5.2 Identificación de Riesgos

| # | Riesgo | Probabilidad | Impacto | Severidad |
|---|---|---|---|---|
| R1 | **Condición de carrera en reservas:** dos usuarios reservan el mismo espacio en el mismo instante. | Media | Alto | 🔴 Alta |
| R2 | **Código IA incorrecto:** el agente genera lógica errónea que pasa desapercibida sin revisión. | Alta | Alto | 🔴 Alta |
| R3 | **Fuga de información de roles:** un usuario con rol estudiante accede a endpoints de administrador. | Baja | Alto | 🟠 Media-Alta |
| R4 | **Tokens JWT comprometidos:** tokens con larga expiración sin mecanismo de invalidación. | Media | Alto | 🔴 Alta |
| R5 | **Pérdida de datos en migración:** error en script Alembic destruye datos en ambiente de prueba. | Baja | Alto | 🟠 Media-Alta |
| R6 | **Dependencia de disponibilidad del servicio SMTP:** fallos de correo bloquean el flujo de reserva. | Media | Medio | 🟡 Media |
| R7 | **Alcance no controlado (scope creep):** adición de features fuera del plan inicial. | Alta | Medio | 🟠 Media-Alta |

### 5.3 Estrategias de Mitigación

| Riesgo | Estrategia |
|---|---|
| **R1 — Condición de carrera** | Usar transacciones con nivel de aislamiento `SERIALIZABLE` y bloqueos optimistas (`SELECT FOR UPDATE`) en PostgreSQL al crear una reserva. |
| **R2 — Código IA incorrecto** | Revisión manual obligatoria de todo código generado; pruebas automáticas como red de seguridad; el estudiante es responsable del código entregado. |
| **R3 — Fuga de roles** | Middleware de autorización centralizado con decoradores de permisos; pruebas de acceso no autorizado (HTTP 403) en cada endpoint protegido. |
| **R4 — Tokens JWT** | Tokens de acceso de corta duración (15 min) + refresh tokens almacenados en Redis con capacidad de revocación; lista negra de tokens invalidados. |
| **R5 — Migración de datos** | Ambiente de BD de prueba separado; script de rollback para cada migración Alembic; nunca ejecutar migraciones en producción sin respaldo. |
| **R6 — SMTP** | Las notificaciones son asíncronas y no bloquean la confirmación de la reserva; implementar reintentos con backoff exponencial. |
| **R7 — Scope creep** | Backlog priorizado con MoSCoW; cualquier nueva funcionalidad pasa por evaluación de impacto antes de incluirse en una etapa activa. |

### 5.4 Mecanismos de Verificación de Requisitos

- **Trazabilidad spec → test:** cada funcionalidad en la spec de OpenSpec tendrá al menos un caso de prueba asociado.
- **Pipeline CI:** las pruebas se ejecutan automáticamente en cada push; el merge a `main` está bloqueado si alguna prueba falla.
- **Revisión de cobertura:** reporte de cobertura generado con `pytest-cov`; umbral mínimo del 80 % en lógica de negocio.
- **Checklist de criterios de aceptación:** cada historia de usuario tiene criterios de aceptación explícitos derivados de la spec.
- **Revisión de endpoints con Postman/Swagger UI:** validación manual de contratos de API contra la documentación generada.

---

## 6. Uso de SDD e Inteligencia Artificial

### 6.1 ¿Cómo se Utilizará OpenSpec?

OpenSpec se utilizará como **herramienta de especificación formal** que actúa como contrato entre el plan de ingeniería y la implementación:

1. **Una spec por módulo:** cada módulo del sistema (auth, spaces, reservations, etc.) tendrá su propio archivo de spec.
2. **Antes del código:** la spec de cada módulo se redactará y revisará _antes_ de escribir o generar cualquier línea de código.
3. **Fuente de verdad:** la spec define contratos de API (endpoints, parámetros, respuestas, errores), modelos de datos y reglas de negocio.
4. **Validación continua:** las respuestas reales del sistema se validarán contra la spec en las pruebas de contrato.

```
PLAN_INGENIERIA.md
    │
    ▼
specs/
├── auth.spec          ← OpenSpec
├── spaces.spec        ← OpenSpec
├── reservations.spec  ← OpenSpec
├── notifications.spec ← OpenSpec
└── reports.spec       ← OpenSpec
    │
    ▼
Código generado / implementado
    │
    ▼
Pruebas (validan contra spec)
```

### 6.2 ¿Cómo se Transformará el Plan en Especificaciones?

El proceso de transformación seguirá estos pasos:

1. **Identificar el módulo:** tomar un módulo del plan (ej. `reservations`).
2. **Extraer contratos:** del plan identificar entidades, operaciones y reglas de negocio.
3. **Redactar la spec OpenSpec:** definir:
   - Entidades y sus campos (tipos, validaciones, restricciones).
   - Operaciones (nombre, parámetros de entrada, resultado esperado, errores posibles).
   - Flujos y reglas (ej. "no se puede reservar si el espacio está ocupado en ese horario").
4. **Revisar y validar la spec** antes de proceder con la implementación.
5. **Versionar la spec** en Git (`specs/` directory) junto con el módulo implementado.

### 6.3 ¿Qué Actividades se Delegarán a la IA?

| Actividad | Delegada a IA | Responsable final |
|---|---|---|
| Generación de modelos ORM a partir de la spec | ✅ Sí | Estudiante (revisión) |
| Generación de Pydantic schemas | ✅ Sí | Estudiante (revisión) |
| Generación de endpoints CRUD básicos | ✅ Sí | Estudiante (revisión) |
| Generación de pruebas unitarias base | ✅ Sí | Estudiante (revisión y ampliación) |
| Generación de migraciones Alembic | ✅ Sí | Estudiante (revisión) |
| Lógica de detección de conflictos de reserva | ⚠️ Parcial | Estudiante (diseño + revisión) |
| Decisiones de arquitectura | ❌ No | Estudiante |
| Diseño de la spec OpenSpec | ❌ No | Estudiante |
| Revisión y aprobación de código | ❌ No | Estudiante |
| Definición de criterios de aceptación | ❌ No | Estudiante |
| Resolución de deuda técnica | ⚠️ Parcial | Estudiante |

### 6.4 ¿Cómo se Verificará el Código Generado?

El código generado por la IA pasará por un proceso de verificación en cuatro capas:

1. **Revisión de lectura (Code Review manual):**
   - ¿El código implementa exactamente lo que describe la spec?
   - ¿Hay lógica de negocio incorrecta o simplificaciones peligrosas?
   - ¿Se respetan los patrones arquitectónicos definidos?

2. **Análisis estático:**
   - `ruff` para linting y formato en Python.
   - `mypy` para verificación de tipos.
   - `bandit` para detección de vulnerabilidades.
   - `eslint` + `tsc` para el frontend.

3. **Pruebas automatizadas:**
   - Ejecutar suite completa de pruebas unitarias e integración.
   - Verificar que la cobertura no disminuya.
   - Las pruebas fallidas bloquean el commit vía pre-commit hooks.

4. **Validación de contrato:**
   - Ejecutar el cliente contra la spec OpenSpec.
   - Verificar que los status codes y estructuras de respuesta coincidan exactamente.

### 6.5 ¿Qué Decisiones Serán Responsabilidad del Estudiante?

El estudiante asume responsabilidad exclusiva sobre:

1. **Decisiones de arquitectura:** selección y justificación del stack, patrones y estructura de módulos.
2. **Diseño de especificaciones:** qué contratos define cada spec, qué reglas de negocio son correctas.
3. **Definición del modelo de datos:** entidades, relaciones, restricciones e índices.
4. **Priorización de funcionalidades:** qué entra en cada incremento y en qué orden.
5. **Aceptación o rechazo del código generado:** el estudiante es el criterio final de calidad.
6. **Resolución de ambigüedades del dominio:** cuando el sistema puede interpretarse de distintas formas, el estudiante decide.
7. **Definición de criterios de aceptación y pruebas de aceptación.**
8. **Gestión del repositorio:** estructura de branches, convenciones de commit, tags de versión.

> **Principio rector:** La IA es una herramienta de productividad; el estudiante es el ingeniero responsable del sistema. Todo código entregado es responsabilidad del estudiante, independientemente de su origen.

---

## Resumen Ejecutivo

| Aspecto | Decisión |
|---|---|
| **Arquitectura** | Monolito Modular con API RESTful |
| **Backend** | Python 3.11 + FastAPI |
| **Base de datos** | PostgreSQL 16 + Redis |
| **Frontend** | React 18 + TypeScript + Vite |
| **Metodología** | SDD con OpenSpec + Desarrollo Incremental |
| **Calidad** | pytest + Playwright + CI/CD con GitHub Actions |
| **Gestión de IA** | Delegación controlada con revisión humana obligatoria |
| **Incrementos** | 6 incrementos (I-0 a I-5) |

---

*Documento elaborado como parte de la Etapa 1 del proyecto. Debe ser registrado en un commit independiente antes de proceder con las especificaciones OpenSpec y la implementación.*
