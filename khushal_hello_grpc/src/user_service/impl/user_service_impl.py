"""
User service implementation using gRPC.
"""

import logging
from datetime import datetime

from khushal_hello_grpc.src.generated import user_pb2
from khushal_hello_grpc.src.generated import user_pb2_grpc
from khushal_hello_grpc.src.user_service.handlers.user_handler import UserHandler

logger = logging.getLogger(__name__)


class UserService(user_pb2_grpc.UserServiceServicer):
    """gRPC service implementation for user management"""
    
    def __init__(self, user_handler: UserHandler):
        """Initialize with handler dependency"""
        self.user_handler = user_handler
        logger.info("UserService initialized with UserHandler")
    
    def Register(self, request, context):
        """Handle user registration"""
        logger.info(f"Processing registration request for username: {request.username}")
        
        success, message, user_id = self.user_handler.register_user(
            username=request.username,
            email=request.email,
            password=request.password
        )
        
        return user_pb2.RegisterResponse(
            success=success,
            message=message,
            user_id=user_id if user_id else ""
        )
    
    def Login(self, request, context):
        """Handle user login"""
        # Determine if login is by email or username
        identifier = request.identifier.email if request.identifier.HasField('email') else request.identifier.username
        is_email = request.identifier.HasField('email')
        
        logger.info(f"Processing login request for {'email' if is_email else 'username'}: {identifier}")
        
        success, message, tokens = self.user_handler.login_user(
            identifier=identifier,
            password=request.password,
            is_email=is_email
        )
        
        if not success:
            return user_pb2.LoginResponse(
                success=False,
                message=message
            )
        
        # Create UserProfile message
        user_data = tokens["user"]
        user_profile = user_pb2.UserProfile(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"] if user_data["last_login"] else ""
        )
        
        return user_pb2.LoginResponse(
            success=True,
            message=message,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            user=user_profile
        )
    
    def GetUserProfile(self, request, context):
        """Handle user profile retrieval"""
        logger.info(f"Processing profile request for user_id: {request.user_id}")
        
        # First verify the token from metadata
        auth_header = dict(context.invocation_metadata()).get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            context.abort(401, 'Missing or invalid authorization token')
        
        token = auth_header.split(' ')[1]
        is_valid, token_user_id = self.user_handler.verify_token(token)
        
        if not is_valid:
            context.abort(401, 'Invalid or expired token')
        
        if token_user_id != request.user_id:
            context.abort(403, 'Not authorized to access this profile')
        
        success, message, profile_data = self.user_handler.get_user_profile(request.user_id)
        
        if not success:
            return user_pb2.UserProfileResponse(
                success=False,
                message=message
            )
        
        # Create UserProfile message
        user_profile = user_pb2.UserProfile(
            user_id=profile_data["user_id"],
            username=profile_data["username"],
            email=profile_data["email"],
            created_at=profile_data["created_at"],
            last_login=profile_data["last_login"] if profile_data["last_login"] else ""
        )
        
        return user_pb2.UserProfileResponse(
            success=True,
            message=message,
            profile=user_profile
        )
    
    def cleanup(self):
        """Cleanup method for any service-level resources"""
        logger.info("UserService cleanup completed") 