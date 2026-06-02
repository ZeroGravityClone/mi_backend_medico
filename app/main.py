from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints.users import router as users_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.patients import router as patients_router
from app.api.endpoints.ai import router as ai_router

app = FastAPI(title="Sistema Médico API", version="1.0.0")

# --- CONFIGURACIÓN DE CORS ---

origins = [
    "http://localhost:3000",      # Puerto clásico de React
    "http://localhost:5173",      # Puerto estándar de React usando Vite
    "http://127.0.0.1:5173",      # Puerto localhost para desarrollo
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

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido al Backend del Sistema Médico!"}