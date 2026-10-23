# Sistema de Gestión de Reservas de Espacios Académicos

Sistema web para centralizar la gestión de reservas de laboratorios, auditorios y salas de cómputo en una institución universitaria.

## Estructura del Proyecto

```
reservas-academicas/
├── PLAN_INGENIERIA.md   # Etapa 1: Planificación de ingeniería
├── specs/               # Especificaciones OpenSpec (Etapa 2)
├── backend/             # API REST con FastAPI (Etapa 3+)
└── frontend/            # SPA con React + TypeScript (Etapa 3+)
```

## Metodología

Este proyecto sigue **Spec-Driven Development (SDD)** con OpenSpec:
1. Plan de ingeniería → 2. Especificaciones → 3. Implementación → 4. Pruebas

## Stack Tecnológico

- **Backend:** Python 3.11 + FastAPI + PostgreSQL + Redis
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Testing:** pytest + Playwright
- **CI/CD:** GitHub Actions
