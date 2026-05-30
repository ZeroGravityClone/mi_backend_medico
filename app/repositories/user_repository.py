from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User:
        """Busca un usuario por su email."""
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user_in: UserCreate) -> User:
        """Crea un nuevo usuario con contraseña encriptada."""

        hashed_pw = get_password_hash(user_in.password)
        
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_pw,
            role=user_in.role
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user