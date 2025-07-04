"""
User service implementation using gRPC.
"""

import logging
import grpc
from datetime import datetime

from khushal_hello_grpc.src.generated import user_pb2
from khushal_hello_grpc.src.generated.user_pb2_grpc import UserServiceServicer
from khushal_hello_grpc.src.user_service.handlers.user_handler import UserHandler

logger = logging.getLogger(__name__)


class UserService(UserServiceServicer):
    """gRPC User Service implementation"""
    
    def __init__(self, user_handler: UserHandler):
        """Initialize with UserHandler dependency injection"""
        logger.info("Initializing UserService with UserHandler")
        self.user_handler = user_handler
        logger.info("UserService initialized successfully")
    
    def Register(self, request, context):
        """Handle user registration requests"""
        logger.info(f"Processing registration request for username: {request.username}")
        
        try:
            # Log request details (excluding password)
            logger.info(f"Registration request - username: {request.username}, email: {request.email}")
            
            # Call handler to register user
            logger.info("Calling UserHandler.register_user...")
            result = self.user_handler.register_user(
                username=request.username,
                email=request.email,
                password=request.password
            )
            
            if result:
                logger.info("User registration successful")
                return user_pb2.RegisterResponse(
                    success=True,
                    message="User registered successfully",
                    user_id=result["user"]["user_id"]
                )
            else:
                logger.warning("User registration failed - user already exists or validation error")
                return user_pb2.RegisterResponse(
                    success=False,
                    message="Username or email already exists",
                    user_id=""
                )
                
        except Exception as e:
            logger.error(f"Error processing registration request: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Registration failed: {str(e)}")
            return user_pb2.RegisterResponse(
                success=False,
                message=f"Registration failed: {str(e)}",
                user_id=""
            )
    
    def Login(self, request, context):
        """Handle user login requests"""
        # Handle the oneof identifier field
        if request.HasField("username"):
            identifier = request.username
        elif request.HasField("email"):
            identifier = request.email
        else:
            logger.warning("Login request missing identifier")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Username or email required')
            return user_pb2.LoginResponse(
                success=False,
                message="Username or email required",
                access_token="",
                refresh_token=""
            )
            
        logger.info(f"Processing login request for: {identifier}")
        
        try:
            # Log request details (excluding password)
            logger.info(f"Login request - identifier: {identifier}")
            
            # Call handler to authenticate user
            logger.info("Calling UserHandler.login_user...")
            result = self.user_handler.login_user(
                username_or_email=identifier,
                password=request.password
            )
            
            if result:
                logger.info("User login successful")
                # Create UserProfile object
                user_profile = user_pb2.UserProfile(
                    user_id=result["user"]["user_id"],
                    username=result["user"]["username"],
                    email=result["user"]["email"],
                    created_at=result["user"]["created_at"],
                    last_login=result["user"]["last_login"] if result["user"]["last_login"] else ""
                )
                
                return user_pb2.LoginResponse(
                    success=True,
                    message="Login successful",
                    access_token=result["access_token"],
                    refresh_token=result["refresh_token"],
                    user=user_profile
                )
            else:
                logger.warning("User login failed - invalid credentials")
                return user_pb2.LoginResponse(
                    success=False,
                    message="Invalid credentials",
                    access_token="",
                    refresh_token=""
                )
                
        except Exception as e:
            logger.error(f"Error processing login request: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Login failed: {str(e)}")
            return user_pb2.LoginResponse(
                success=False,
                message=f"Login failed: {str(e)}",
                access_token="",
                refresh_token=""
            )
    
    def GetUserProfile(self, request, context):
        """Handle user profile requests"""
        logger.info(f"Processing profile request for user: {request.user_id}")
        
        try:
            # First verify the token from metadata
            auth_header = dict(context.invocation_metadata()).get('authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                logger.warning("Profile request failed - missing authorization header")
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details('Missing or invalid authorization token')
                return user_pb2.UserProfileResponse(
                    success=False,
                    message="Authentication required"
                )
            
            token = auth_header.split(' ')[1]
            logger.info("Verifying authentication token...")
            token_user_id = self.user_handler.verify_token(token)
            
            if not token_user_id:
                logger.warning("Profile request failed - invalid token")
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details('Invalid or expired token')
                return user_pb2.UserProfileResponse(
                    success=False,
                    message="Invalid or expired token"
                )
            
            # Ensure user can only access their own profile
            if token_user_id != request.user_id:
                logger.warning("Profile request failed - access denied")
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details('Not authorized to access this profile')
                return user_pb2.UserProfileResponse(
                    success=False,
                    message="Access denied"
                )
            
            # Call handler to get user profile
            logger.info("Calling UserHandler.get_user_profile...")
            result = self.user_handler.get_user_profile(request.user_id)
            
            if result:
                logger.info("User profile retrieved successfully")
                # Create UserProfile object
                user_profile = user_pb2.UserProfile(
                    user_id=result["user_id"],
                    username=result["username"],
                    email=result["email"],
                    created_at=result["created_at"],
                    last_login=result["last_login"] if result["last_login"] else ""
                )
                
                return user_pb2.UserProfileResponse(
                    success=True,
                    message="Profile retrieved successfully",
                    profile=user_profile
                )
            else:
                logger.warning("User profile not found")
                return user_pb2.UserProfileResponse(
                    success=False,
                    message="User not found"
                )
                
        except Exception as e:
            logger.error(f"Error processing profile request: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Profile request failed: {str(e)}")
            return user_pb2.UserProfileResponse(
                success=False,
                message=f"Profile request failed: {str(e)}"
            )
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up UserService resources")
        pass 