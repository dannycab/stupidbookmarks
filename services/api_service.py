"""API service for StupidBookmarks."""

import secrets
import hashlib
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from models.models import APIKey, User

class APIService:
    """Service for handling API operations."""
    
    def create_api_key(self, db: Session, user_id: int, name: str) -> APIKey:
        """Create a new API key."""
        # Generate a random API key
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_preview = raw_key[:8] + "..."
        
        api_key = APIKey(
            name=name,
            key_hash=key_hash,
            key_preview=key_preview,
            user_id=user_id
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        # Store the raw key temporarily for display
        api_key.raw_key = raw_key
        
        return api_key
    
    def get_api_keys(self, db: Session, user_id: int) -> List[APIKey]:
        """Get all API keys for a user."""
        return db.query(APIKey).filter(APIKey.user_id == user_id).all()
    
    def delete_api_key(self, db: Session, key_id: int, user_id: int) -> bool:
        """Delete an API key."""
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        
        if api_key:
            db.delete(api_key)
            db.commit()
            return True
        return False
    
    def authenticate_api_key(self, db: Session, raw_key: Optional[str]) -> Optional[User]:
        """Authenticate an API key and return the associated user."""
        if not raw_key:
            return None
        
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.active == True
        ).first()
        
        if api_key:
            # Update last used timestamp
            api_key.last_used = datetime.now()
            db.commit()
            return api_key.user
        
        return None
