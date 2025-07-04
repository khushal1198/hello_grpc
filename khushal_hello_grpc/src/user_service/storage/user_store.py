"""
User-specific storage implementations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from khushal_hello_grpc.src.common.storage import DatabaseStore, ConnectionPool
from khushal_hello_grpc.src.user_service.models.user_models import User


class UserStore(ABC):
    """Abstract interface for user storage operations"""
    
    @abstractmethod
    def create_user(self, username: str, email: str, password_hash: str) -> Optional[User]:
        """Create a new user"""
        pass
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    def update_last_login(self, user_id: str, login_time: datetime) -> bool:
        """Update user's last login timestamp"""
        pass


class PostgresUserStorage(UserStore):
    """PostgreSQL implementation of user storage"""
    
    def __init__(self, connection_pool: ConnectionPool):
        """Initialize with database connection pool"""
        self._store = DatabaseStore(
            cls=User,
            table_name="users",
            connection_pool=connection_pool
        )
    
    def create_user(self, username: str, email: str, password_hash: str) -> Optional[User]:
        """Create a new user in the database"""
        try:
            # Check if username or email already exists
            if self.get_user_by_username(username) or self.get_user_by_email(email):
                return None
                
            user = User.from_dict({
                "username": username,
                "email": email,
                "password_hash": password_hash
            })
            
            created = self._store.create(user.to_dict())
            return User.from_dict(created) if created else None
            
        except Exception as e:
            import logging
            logging.error(f"Failed to create user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            data = self._store.get_by_id(user_id)
            return User.from_dict(data) if data else None
        except Exception as e:
            import logging
            logging.error(f"Failed to get user by ID: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            results = self._store.get_by_field("username", username)
            return User.from_dict(results[0]) if results else None
        except Exception as e:
            import logging
            logging.error(f"Failed to get user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            results = self._store.get_by_field("email", email)
            return User.from_dict(results[0]) if results else None
        except Exception as e:
            import logging
            logging.error(f"Failed to get user by email: {e}")
            return None
    
    def update_last_login(self, user_id: str, login_time: datetime) -> bool:
        """Update user's last login timestamp"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
                
            updated_data = user.to_dict()
            updated_data["last_login"] = login_time.isoformat()
            
            success = self._store.update(user_id, updated_data)
            return bool(success)
            
        except Exception as e:
            import logging
            logging.error(f"Failed to update last login: {e}")
            return False


def create_user_store(connection_pool: ConnectionPool) -> UserStore:
    """Factory function to create UserStore instance"""
    return PostgresUserStorage(connection_pool) 