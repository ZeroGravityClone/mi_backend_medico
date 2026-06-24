from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from typing import List, Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        # El uso de Optional[User] le dice a Pylance que puede devolver None o User
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_in: UserCreate) -> User:
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

    def get_all_users(self) -> List[User]:
        return self.db.query(User).all()

    def delete_user(self, db_user: User) -> None:
        self.db.delete(db_user)
        self.db.commit()