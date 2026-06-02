from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.token import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Valida el token JWT y retorna el usuario actual si es válido."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")  # type: ignore
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    repo = UserRepository(db)
    user = repo.get_user_by_email(str(token_data.email))
    if user is None:
        raise credentials_exception
        
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Valida que el usuario actual tenga rol ADMIN."""
    
    if str(current_user.role).upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos suficientes para realizar esta acción."
        )
    return current_user