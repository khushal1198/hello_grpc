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
        logger.info("Initializing UserHandler with user storage backend")
        self.user_store = user_store
        
        # JWT configuration (should be moved to config in production)
        self.jwt_secret = "your-secret-key-change-in-production"
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        logger.info("UserHandler initialized successfully")
    
    def register_user(self, username: str, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Register a new user with password hashing"""
        logger.info(f"Starting user registration for username: {username}, email: {email}")
        
        try:
            # Validate input
            logger.info("Validating registration input...")
            if not username or not email or not password:
                logger.warning("Registration failed: Missing required fields")
                return None
            
            if len(password) < 6:
                logger.warning("Registration failed: Password too short")
                return None
            
            # Hash password
            logger.info("Hashing password...")
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            logger.info("Password hashed successfully")
            
            # Create user
            logger.info("Creating user in storage...")
            user = self.user_store.create_user(username, email, password_hash)
            
            if user:
                logger.info(f"User created successfully: {user.id}")
                # Generate tokens
                logger.info("Generating JWT tokens...")
                access_token = self._generate_access_token(user.id)
                refresh_token = self._generate_refresh_token(user.id)
                logger.info("JWT tokens generated successfully")
                
                return {
                    "user": user.to_profile_dict(),
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }
            else:
                logger.warning("User creation failed - user already exists or database error")
                return None
                
        except Exception as e:
            logger.error(f"Error during user registration: {e}", exc_info=True)
            return None
    
    def login_user(self, username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return tokens"""
        logger.info(f"Starting user login for: {username_or_email}")
        
        try:
            # Find user by username or email
            logger.info("Looking up user...")
            user = None
            if "@" in username_or_email:
                logger.info("Searching by email...")
                user = self.user_store.get_user_by_email(username_or_email)
            else:
                logger.info("Searching by username...")
                user = self.user_store.get_user_by_username(username_or_email)
            
            if not user:
                logger.warning(f"Login failed: User not found for {username_or_email}")
                return None
            
            logger.info(f"User found: {user.id}")
            
            # Verify password
            logger.info("Verifying password...")
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                logger.warning("Login failed: Invalid password")
                return None
            
            logger.info("Password verified successfully")
            
            # Generate tokens
            logger.info("Generating JWT tokens...")
            access_token = self._generate_access_token(user.id)
            refresh_token = self._generate_refresh_token(user.id)
            logger.info("JWT tokens generated successfully")
            
            return {
                "user": user.to_profile_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            
        except Exception as e:
            logger.error(f"Error during user login: {e}", exc_info=True)
            return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        logger.info(f"Getting user profile for ID: {user_id}")
        
        try:
            logger.info("Looking up user by ID...")
            user = self.user_store.get_user_by_id(user_id)
            
            if user:
                logger.info(f"User profile found: {user.id}")
                return user.to_profile_dict()
            else:
                logger.warning(f"User profile not found for ID: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}", exc_info=True)
            return None
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user ID"""
        logger.info("Verifying JWT token...")
        
        try:
            logger.info("Decoding JWT token...")
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            user_id = payload.get("user_id")
            
            if user_id:
                logger.info(f"Token verified successfully for user: {user_id}")
                return user_id
            else:
                logger.warning("Token verification failed: No user_id in payload")
                return None
                
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Token verification failed: Invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}", exc_info=True)
            return None
    
    def _generate_access_token(self, user_id: str) -> str:
        """Generate access token"""
        logger.info(f"Generating access token for user: {user_id}")
        
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "type": "access"
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        logger.info("Access token generated successfully")
        return token
    
    def _generate_refresh_token(self, user_id: str) -> str:
        """Generate refresh token"""
        logger.info(f"Generating refresh token for user: {user_id}")
        
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "type": "refresh"
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        logger.info("Refresh token generated successfully")
        return token 