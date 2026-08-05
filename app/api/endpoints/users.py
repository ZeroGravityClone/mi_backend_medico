from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.repositories.user_repository import UserRepository
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_user_by_username(user_in.username):
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado.")
    return repo.create_user(user_in)

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[UserResponse])
def read_all_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    repo = UserRepository(db)
    return repo.get_all_users()

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    repo = UserRepository(db)
    user_to_delete = repo.get_user_by_id(user_id)
    
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    if str(user_to_delete.id) == str(current_admin.id):
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario.")
        
    repo.delete_user(user_to_delete)

@router.put("/{user_id}", response_model=UserResponse)
def update_user_by_admin(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Permite al administrador modificar rol, nombre, contraseña o permisos granulares de un usuario."""
    repo = UserRepository(db)
    user_to_update = repo.get_user_by_id(user_id)
    
    if not user_to_update:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
        
    if user_in.username and user_in.username != user_to_update.username:
        existing = repo.get_user_by_username(user_in.username)
        if existing:
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")
            
    return repo.update_user(user_to_update, user_in)