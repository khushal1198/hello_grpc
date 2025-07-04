"""
Handler for processing user-related requests with JWT authentication.
"""

import logging
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from khushal_hello_grpc.src.user_service.storage.user_store import UserStore

logger = logging.getLogger(__name__)

# JWT configuration (should move to config file)
JWT_SECRET = "your-secret-key"  # CHANGE THIS IN PRODUCTION
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class UserHandler:
    """Handler for processing user registration and authentication"""
    
    def __init__(self, user_store: UserStore):
        """Initialize with storage backend"""
        self.user_store = user_store
        logger.info("UserHandler initialized with storage backend")
    
    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Register a new user.
        
        Returns:
            Tuple of (success: bool, message: str, user_id: Optional[str])
        """
        try:
            # Basic validation
            if not username or not email or not password:
                return False, "All fields are required", None
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user
            user = self.user_store.create_user(
                username=username,
                email=email,
                password_hash=password_hash
            )
            
            if user:
                logger.info(f"Created new user: {user}")
                return True, "User registered successfully", user.id
            else:
                return False, "Username or email already exists", None
                
        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            return False, f"Registration failed: {str(e)}", None
    
    def login_user(self, identifier: str, password: str, is_email: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate user and generate JWT tokens.
        
        Returns:
            Tuple of (success: bool, message: str, tokens: Optional[Dict[str, Any]])
            tokens contains: access_token, refresh_token, user profile
        """
        try:
            # Get user by identifier
            user = (self.user_store.get_user_by_email(identifier) if is_email 
                   else self.user_store.get_user_by_username(identifier))
            
            if not user:
                return False, "Invalid credentials", None
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                return False, "Invalid credentials", None
            
            # Update last login
            self.user_store.update_last_login(user.id, datetime.now())
            
            # Generate tokens
            access_token = self._create_access_token(user.id)
            refresh_token = self._create_refresh_token(user.id)
            
            # Return success with tokens and profile
            return True, "Login successful", {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.to_profile_dict()
            }
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False, f"Login failed: {str(e)}", None
    
    def get_user_profile(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get user profile by ID.
        
        Returns:
            Tuple of (success: bool, message: str, profile: Optional[Dict[str, Any]])
        """
        try:
            user = self.user_store.get_user_by_id(user_id)
            if user:
                return True, "Profile retrieved", user.to_profile_dict()
            else:
                return False, "User not found", None
                
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return False, f"Failed to get profile: {str(e)}", None
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Verify JWT token and return user_id if valid.
        
        Returns:
            Tuple of (is_valid: bool, user_id: Optional[str])
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return True, payload.get("sub")
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            plain_password.encode(),
            hashed_password.encode()
        )
    
    def _create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def _create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM) 