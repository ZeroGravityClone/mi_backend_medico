from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from typing import List, Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_in: UserCreate) -> User:
        hashed_pw = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username, 
            hashed_password=hashed_pw, 
            role=user_in.role,
            permissions=user_in.permissions
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_user(self, db_user: User, user_in: UserUpdate) -> User:
        """Actualiza datos, rol, contraseña o permisos de un usuario."""
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
        for field, value in update_data.items():
            setattr(db_user, field, value)
            
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_all_users(self) -> List[User]:
        return self.db.query(User).all()

    def delete_user(self, db_user: User) -> None:
        self.db.delete(db_user)
        self.db.commit()