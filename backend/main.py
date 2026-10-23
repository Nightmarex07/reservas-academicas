from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, users, spaces, reservations, admin
from config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="""
API REST para el Sistema de Gestión de Reservas de Espacios Académicos.

## Módulos
- **Autenticación**: registro, login, refresh de tokens JWT
- **Usuarios**: perfil propio, historial de reservas
- **Espacios**: CRUD de laboratorios, auditorios y salas de cómputo
- **Reservas**: creación, validación de conflictos, cancelación
- **Administración**: aprobación/rechazo, reportes de uso

## Especificaciones
Las especificaciones formales están en `openspec/specs/`.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(spaces.router)
app.include_router(reservations.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": settings.APP_NAME, "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
