"""
User service data models.
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from khushal_hello_grpc.src.common.storage.models import Storable


@dataclass(frozen=True)
class User(Storable["User"]):
    """Model for storing user data with password hashing"""
    
    # Application-specific fields
    username: str
    email: str
    password_hash: str
    last_login: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            # Required Storable fields
            "id": self.id,
            "created_ts": self.created_ts,
            "last_updated_ts": self.last_updated_ts,
            # Application fields
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create from database row dictionary"""
        return cls(
            # Required Storable fields
            id=data.get("id", str(uuid.uuid4())),
            created_ts=data.get("created_ts", datetime.now()),
            last_updated_ts=data.get("last_updated_ts", datetime.now()),
            # Application fields
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None
        )
    
    def to_profile_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses (excludes sensitive data)"""
        return {
            "user_id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_ts.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    def __str__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')" 