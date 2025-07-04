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
            
            # Use insert method instead of create
            user_id = self._store.insert(user)
            if user_id:
                return self.get_user_by_id(user_id)
            return None
            
        except Exception as e:
            import logging
            logging.error(f"Failed to create user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            # Use get method with filters instead of get_by_id
            return self._store.get(filters={"id": user_id})
        except Exception as e:
            import logging
            logging.error(f"Failed to get user by ID: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            # Use get method with filters instead of get_by_field
            return self._store.get(filters={"username": username})
        except Exception as e:
            import logging
            logging.error(f"Failed to get user by username: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            # Use get method with filters instead of get_by_field
            return self._store.get(filters={"email": email})
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
                
            # Create updated user object
            updated_user = User.from_dict({
                **user.to_dict(),
                "last_login": login_time,
                "last_updated_ts": datetime.now()
            })
            
            # Delete old record and insert new one (since User is immutable)
            self._store.delete(filters={"id": user_id})
            new_id = self._store.insert(updated_user)
            return bool(new_id)
            
        except Exception as e:
            import logging
            logging.error(f"Failed to update last login: {e}")
            return False


def create_user_store(connection_pool: ConnectionPool) -> UserStore:
    """Factory function to create UserStore instance"""
    return PostgresUserStorage(connection_pool) 