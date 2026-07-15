from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.db.database import get_db
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.schemas.token import Token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    repo = UserRepository(db)
    # form_data.username se asocia ahora directamente al username de la base de datos
    user = repo.get_user_by_username(form_data.username)
    
    if not user:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos.")
    
    hashed_password_str = str(user.hashed_password)
    if not verify_password(form_data.password, hashed_password_str):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos.")
    
    user_is_active = bool(user.is_active)
    if not user_is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo.")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # El Token guardará el username en su subject
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }