"""Authentication service for StupidBookmarks."""

import hashlib
import secrets
import os
from typing import Optional
from fastapi import Request, Response
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from models.models import User

pwd_context = CryptContext(schemes=["bcrypt"])

class AuthService:
    """Service for handling authentication."""
    
    def __init__(self):
        self.session_key = "stupidbookmarks_session"
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_user(self, db: Session, user_id: Optional[int] = None) -> Optional[User]:
        """Get user by ID or get the default admin user."""
        if user_id:
            return db.query(User).filter(User.id == user_id).first()
        return db.query(User).first()
    
    def create_default_user(self, db: Session, password: str = None) -> User:
        """Create the default admin user."""
        if password is None:
            # Use environment variable if available, otherwise fallback to "admin"
            password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")
            
        hashed_password = self.hash_password(password)
        user = User(username="admin", password_hash=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def authenticate(self, db: Session, password: str) -> Optional[User]:
        """Authenticate user with password."""
        user = self.get_user(db)
        if user and self.verify_password(password, user.password_hash):
            return user
        return None
    
    def create_session(self, response: Response, user_id: int):
        """Create a user session."""
        session_token = secrets.token_urlsafe(32)
        # In a real app, you'd store this in Redis or database
        # For simplicity, we'll use a simple cookie-based session
        response.set_cookie(
            key=self.session_key,
            value=f"{user_id}:{session_token}",
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
    
    def clear_session(self, response: Response):
        """Clear user session."""
        response.delete_cookie(key=self.session_key)
    
    def get_current_user(self, request: Request, db: Session) -> Optional[User]:
        """Get current user from session."""
        session_cookie = request.cookies.get(self.session_key)
        if not session_cookie:
            return None
        
        try:
            user_id_str, _ = session_cookie.split(":", 1)
            user_id = int(user_id_str)
            return self.get_user(db, user_id)
        except (ValueError, AttributeError):
            return None
    
    def change_password(self, db: Session, user_id: int, new_password: str) -> bool:
        """Change user password."""
        user = self.get_user(db, user_id)
        if user:
            user.password_hash = self.hash_password(new_password)
            db.commit()
            return True
        return False
