from fastapi import FastAPI
from app.api.endpoints import users
from app.api.endpoints import auth

app = FastAPI(title="Sistema Médico API", version="1.0.0")

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido al Backend del Sistema Médico!"}