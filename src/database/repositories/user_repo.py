from typing import Optional, List
from sqlalchemy.orm import Session
from database.models import User

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == user_id).first()

    def create(self, username: str, password_hash: str, role: str = 'Articled Assistant', email: str = None) -> User:
        user = User(username=username, password_hash=password_hash, role=role, email=email)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
