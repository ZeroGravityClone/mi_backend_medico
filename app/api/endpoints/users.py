from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
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
    if user_to_delete.id == current_admin.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario.")
    repo.delete_user(user_to_delete)