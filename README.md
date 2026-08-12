# 🩺 SAD-TH — Backend (Sistema de Archivo Digital - Talento Humano)

API RESTful de alto rendimiento y arquitectura limpia desarrollada para la modernización y transformación del archivo físico histórico de Talento Humano del **Hospital General del Sur Dr. Pedro Iturbe** (más de 1,000 expedientes físicos).

El sistema evoluciona el modelo tradicional de CRUD a una **Plataforma de Gestión Documental Electrónica (DMS/GED)** alimentada por un pipeline de automatización con Inteligencia Artificial Multimodal (Visión).

---

## 🚀 Características Principales

* **Ingesta Multimodal e Indexación Inteligente por IA:** Integración con modelos de visión en Groq (`meta-llama/llama-4-scout-17b-16e-instruct` y `openai/gpt-oss-20b`) a 750-1000 tps. Convierte PDFs e imágenes en memoria (Base64 con `PyMuPDF`) para auto-registrar trabajadores, extraer cédula, nombre, cargo, fechas y clasificar el tipo de documento.
* **Capa de Normalización y Validación de Datos:** Normalización automática de fechas a estándar ISO `YYYY-MM-DD` y validación de consistencia entre el texto leído en el papel y la base de datos mediante algoritmos de coincidencia difusa (*Fuzzy Matching*).
* **Auditoría y Semaforización Automática:** Motor de auditoría en segundo plano que analiza los documentos existentes de un expediente, evalúa reglas de negocio del hospital y determina el estatus (`COMPLETO`, `PENDIENTE`, `CRÍTICO`) generando las observaciones de documentos faltantes.
* **Control de Custodia Física y Préstamos:** Módulo de trazabilidad de carpetas prestadas con validación de doble salida (bloquea la salida de expedientes que ya están fuera de la bóveda) y cálculo de estados (`ACTIVO`, `DEVUELTO`, `VENCIDO`, `PRÓXIMO A VENCER`).
* **Centro de Alertas de Expurgo:** Consultas automatizadas para detectar expedientes que han cumplido su límite de retención legal (5 años) sugiriendo acciones de destrucción o archivo permanente.
* **Seguridad y Permisos Granulares (RBAC/ABAC):** Autenticación sin estado con JWT, hashing de contraseñas con Bcrypt y control de accesos basado en un campo JSON de permisos dinámicos por usuario (pestañas y estatus laborales permitidos).
* **Arquitectura Portable y Híbrida:** Configuración agnóstica de base de datos (PostgreSQL/MySQL) y capacidad de servir el frontend compilado (`dist`) de forma monolítica estática para ejecutar en hardware legacy con consumo inferior a 350MB de RAM.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
| :--- | :--- |
| **Lenguaje** | Python 3.8+ |
| **Framework Web** | FastAPI, Uvicorn |
| **Bases de Datos** | PostgreSQL (Producción), MySQL / MariaDB (XAMPP) |
| **ORM & Migraciones** | SQLAlchemy 2.0, Alembic |
| **Motor de IA** | Groq API (`llama-4-scout`, `gpt-oss-20b`) |
| **Procesamiento de PDF/Imágenes** | PyMuPDF (`fitz`), PyPDF |
| **Seguridad & Tokens** | Passlib, Bcrypt, Python-Jose (JWT) |
| **Validación de Datos** | Pydantic V2, Pydantic-Settings |

---

## 📋 Endpoints Principales de la API

### Autenticación y Usuarios (`/auth`, `/users`)
* `POST /auth/login` — Autenticación OAuth2 con generación de JWT.
* `GET /users/me` — Perfil del usuario autenticado.
* `GET /users/` — Listar todos los usuarios del sistema (Solo ADMIN).
* `POST /users/` — Registrar un nuevo usuario.
* `PUT /users/{user_id}` — Modificar rol, datos o permisos granulares JSON (Solo ADMIN).
* `DELETE /users/{user_id}` — Eliminar usuario (Solo ADMIN).

### Expedientes de Personal (`/patients`)
* `GET /patients/` — Obtener expedientes paginados.
* `POST /patients/` — Crear expediente de trabajador manualmente.
* `PUT /patients/{id}` — Actualizar expediente (Solo ADMIN).
* `DELETE /patients/{id}` — Eliminar expediente (Solo ADMIN).
* `POST /patients/auto-register` — **Auto-registro inteligente por IA** mediante escaneo de carpeta.
* `POST /patients/{id}/audit` — **Auditoría automática por IA** para detectar documentos faltantes.

### Gestión Documental (`/patients/{id}/documents`)
* `POST /patients/{id}/documents` — Subida e indexación manual de documento.
* `POST /patients/{id}/documents/auto` — **Auto-clasificación visual por IA** de documento adjunto.
* `GET /patients/{id}/documents` — Obtener expediente documental completo.
* `GET /patients/documents/all` — Listado global de todos los documentos indexados.
* `PUT /patients/documents/{document_id}` — Modificar metadata de indexación.
* `DELETE /patients/documents/{document_id}` — Eliminar registro e imagen física del disco.

### Préstamos y Custodia (`/loans`)
* `POST /loans/` — Registrar salida física de carpeta (Con protección de doble salida).
* `GET /loans/` — Bitácora histórica de préstamos.
* `PUT /loans/{id}/return` — Registrar devolución de expediente.
* `PUT /loans/{id}` — Modificar registro de préstamo.
* `DELETE /loans/{id}` — Eliminar registro de bitácora.

### Alertas e Indicadores (`/alerts`)
* `GET /alerts/summary` — Resumen dinámico de préstamos vencidos, por vencer y expurgos legales.

---

## 📦 Instalación y Configuración Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/ZeroGravityClone/mi_backend_medico.git
cd mi_backend_medico
