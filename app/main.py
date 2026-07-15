import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # <-- IMPORTANTE PARA LOS ARCHIVOS

from app.api.endpoints.users import router as users_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.patients import router as patients_router
from app.api.endpoints.ai import router as ai_router
from app.api.endpoints.loans import router as loans_router

# Crear la carpeta automáticamente en Windows 10 si no existe al arrancar
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="Sistema Médico API", version="1.0.0")

# --- CONFIGURACIÓN DE CORS ---
origins = [
    "http://localhost:3000",      
    "http://localhost:5173",      
    "http://127.0.0.1:5173",      
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],     
    allow_headers=["*"],     
)
# -----------------------------

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(patients_router)
app.include_router(ai_router)
app.include_router(loans_router)

# Montar la carpeta de archivos subidos para poder ver los PDFs/JPGs desde React
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --- NUEVO CÓDIGO CORREGIDO PARA MOSTRAR REACT ---
# Montamos la carpeta "dist" en la ruta principal "/" para servir la interfaz web.
# Esta instrucción debe ser obligatoriamente la última línea del archivo para evitar bloqueos.
app.mount("/", StaticFiles(directory="dist", html=True), name="static")