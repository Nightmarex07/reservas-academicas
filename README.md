# Sistema de Gestión de Reservas de Espacios Académicos

Sistema web integral para centralizar y administrar la reserva de espacios académicos (laboratorios, auditorios y salas de cómputo) en una institución universitaria.

Desarrollado bajo la metodología **Spec-Driven Development (SDD)** utilizando **OpenSpec**, garantizando trazabilidad total entre el plan de ingeniería, las especificaciones formales, la implementación de software y las pruebas automatizadas.

---

## Estructura del Repositorio

```text
reservas-academicas/
├── PLAN_INGENIERIA.md         # Etapa 1: Plan de ingeniería de software
├── RESULTADOS_PRUEBAS.md      # Etapa 2 (Fase 5): Matriz de trazabilidad y reporte de pruebas
├── docker-compose.yml         # Contenedores para PostgreSQL 16, Redis 7, Backend y MailHog
├── openspec/                  # Especificaciones OpenSpec (Etapa 2)
│   ├── config.yaml            # Configuración global del proyecto y reglas EARS/BDD
│   ├── specs/                 # Especificaciones canónicas del sistema
│   │   ├── user-management/   # Registro, roles, JWT
│   │   ├── space-management/  # Espacios, catálogo, capacidad
│   │   ├── reservation-core/  # Reservas, solapamientos, regla de 4 horas
│   │   ├── reservation-approval/ # Aprobación y rechazo administrativo
│   │   ├── reservation-history/  # Historial y cancelación
│   │   └── notifications/     # Eventos y correos asíncronos
│   └── changes/               # Ciclo de cambios (SDD)
│       ├── revision-inicial/  # Fase 2: Revisión de consistencia
│       └── regla-4-horas/     # Fase 4: Solicitud de cambio de duración máxima
└── backend/                   # Implementación FastAPI (Etapa 2, Fase 3 y 4)
    ├── main.py                # Entrada principal y documentación OpenAPI
    ├── config.py              # Configuración y variables de entorno
    ├── database.py            # Sesión SQLAlchemy y pooling
    ├── models.py              # Modelos ORM (User, Space, Reservation)
    ├── schemas.py             # Esquemas Pydantic v2 (con validador de 4h)
    ├── core/                  # Autenticación, JWT y RBAC
    ├── services/              # Lógica de reservas y notificaciones asíncronas
    ├── routers/               # Endpoints REST (auth, users, spaces, reservations, admin)
    ├── requirements.txt       # Dependencias Python
    └── tests/                 # Suite de pruebas automatizadas (pytest)
        ├── test_auth.py       # Pruebas de usuarios y autenticación (USR-01..04)
        ├── test_spaces.py     # Pruebas de espacios académicos (SPC-01..03)
        └── test_reservations.py # Pruebas del motor de reservas y regla de 4h (RES-01..04, APR, HST)
```

---

## Especificaciones y Metodología SDD (OpenSpec)

El proyecto utiliza **OpenSpec** como única fuente de verdad:

1. **Requisitos EARS:** Formulación formal con `SHALL`, `MUST` y `SHOULD`.
2. **Escenarios BDD:** Casos de prueba unívocos con `GIVEN`, `WHEN`, `THEN`.
3. **Gestión de Cambios (Fase 4):** La regla de negocio institucional (*máximo 4 horas consecutivas*) fue incorporada mediante una propuesta de cambio formal (`openspec/changes/regla-4-horas/`), con su delta spec correspondiente antes de modificar el código y las pruebas.

Para consultar las especificaciones en la terminal:
```bash
# Listar especificaciones canónicas
openspec list --specs

# Listar cambios activos
openspec list
```

---

## Ejecución del Backend y Pruebas Automatizadas

### 1. Entorno Local con Python

```bash
# Clonar o ubicarse en la raíz del proyecto
cd reservas-academicas

# Activar el entorno virtual existente o crear uno
python -m venv .venv
.venv\Scripts\activate   # En Windows
# source .venv/bin/activate  # En Linux/macOS

# Instalar dependencias
pip install -r backend/requirements.txt

# Ejecutar la suite completa de pruebas
pytest -v backend/tests
```

### 2. Documentación Interactiva de la API (Swagger UI)

Al iniciar el servidor:
```bash
cd backend
uvicorn main:app --reload
```
Acceder a la documentación generada automáticamente en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Despliegue con Docker Compose (Producción / Staging)

```bash
docker-compose up -d
```
Servicios levantados:
- **FastAPI API:** `http://localhost:8000`
- **PostgreSQL 16:** `localhost:5432`
- **Redis 7:** `localhost:6379`
- **MailHog (Bandeja de correos de prueba):** `http://localhost:8025`
