"""
User-specific storage implementations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import logging
import json
import uuid

from khushal_hello_grpc.src.common.storage import DatabaseStore, ConnectionPool
from khushal_hello_grpc.src.user_service.models.user_models import User

logger = logging.getLogger(__name__)

class UserStore(ABC):
    """Abstract base class for user storage operations"""
    
    @abstractmethod
    def create_user(self, username: str, email: str, password_hash: str) -> Optional[User]:
        """Create a new user"""
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
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    def update_user(self, user: User) -> Optional[User]:
        """Update user information"""
        pass
    
    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        pass


class PostgresUserStorage(UserStore):
    """PostgreSQL implementation of user storage"""
    
    def __init__(self, connection_pool: ConnectionPool):
        """Initialize with database connection pool"""
        logger.info("Initializing PostgresUserStorage with connection pool")
        self._store = DatabaseStore(
            cls=User,
            table_name="users",
            connection_pool=connection_pool
        )
        logger.info("PostgresUserStorage initialized successfully")
    
    def create_user(self, username: str, email: str, password_hash: str) -> Optional[User]:
        """Create a new user in the database"""
        logger.info(f"Starting create_user for username: {username}, email: {email}")
        try:
            # Check if username or email already exists
            logger.info("Checking if username already exists...")
            if self.get_user_by_username(username):
                logger.warning(f"Username {username} already exists")
                return None
            
            logger.info("Checking if email already exists...")
            if self.get_user_by_email(email):
                logger.warning(f"Email {email} already exists")
                return None
            
            # Create new user with all required fields
            logger.info("Creating new user object...")
            now = datetime.now()
            user = User(
                id=str(uuid.uuid4()),
                created_ts=now,
                last_updated_ts=now,
                username=username,
                email=email,
                password_hash=password_hash
            )
            logger.info(f"Created user object with ID: {user.id}")
            
            # Insert into database
            logger.info("Inserting user into database...")
            result = self._store.insert(user)
            logger.info(f"Database insert result: {result}")
            
            if result:
                logger.info(f"User created successfully: {user.id}")
                return user
            else:
                logger.error("Database insert returned None/False")
                return None
                
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        logger.info(f"Looking up user by username: {username}")
        try:
            logger.info("Calling database store get method with username filter...")
            user = self._store.get(filters={"username": username})
            logger.info(f"Database query returned: {user}")
            
            if user:
                logger.info(f"Found user: {user.id}")
                return user
            else:
                logger.info("No user found with that username")
                return None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}", exc_info=True)
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        logger.info(f"Looking up user by email: {email}")
        try:
            logger.info("Calling database store get method with email filter...")
            user = self._store.get(filters={"email": email})
            logger.info(f"Database query returned: {user}")
            
            if user:
                logger.info(f"Found user: {user.id}")
                return user
            else:
                logger.info("No user found with that email")
                return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}", exc_info=True)
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        logger.info(f"Looking up user by ID: {user_id}")
        try:
            logger.info("Calling database store get method with ID filter...")
            user = self._store.get(filters={"id": user_id})
            logger.info(f"Database query returned: {user}")
            
            if user:
                logger.info(f"Found user: {user.id}")
                return user
            else:
                logger.info("No user found with that ID")
                return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}", exc_info=True)
            return None
    
    def update_user(self, user: User) -> Optional[User]:
        """Update user information"""
        logger.info(f"Updating user: {user.id}")
        try:
            # Since User is immutable, we need to delete and recreate
            logger.info("Deleting existing user record...")
            if self.delete_user(user.id):
                logger.info("Inserting updated user record...")
                result = self._store.insert(user)
                if result:
                    logger.info("User updated successfully")
                    return user
                else:
                    logger.error("Failed to insert updated user")
                    return None
            else:
                logger.error("Failed to delete existing user for update")
                return None
        except Exception as e:
            logger.error(f"Error updating user: {e}", exc_info=True)
            return None
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        logger.info(f"Deleting user: {user_id}")
        try:
            logger.info("Calling database store delete method...")
            result = self._store.delete(filters={"id": user_id})
            logger.info(f"Delete operation result: {result}")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}", exc_info=True)
            return False


def create_user_store(connection_pool: ConnectionPool) -> UserStore:
    """Factory function to create a user store instance"""
    logger.info("Creating PostgresUserStorage instance")
    return PostgresUserStorage(connection_pool) 