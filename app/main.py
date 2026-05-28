from fastapi import FastAPI

app = FastAPI(title="Sistema Médico API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "¡Bienvenido al Backend del Sistema Médico!"}