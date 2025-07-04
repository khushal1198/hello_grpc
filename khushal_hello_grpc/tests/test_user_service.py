import grpc
import threading
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from khushal_hello_grpc.src.user_service.impl.user_service_impl import UserService
from khushal_hello_grpc.src.user_service.handlers.user_handler import UserHandler
from khushal_hello_grpc.src.user_service.models.user_models import User
from khushal_hello_grpc.src.generated import user_pb2, user_pb2_grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc
import bcrypt
import jwt
from datetime import datetime, timedelta


class DummyContext:
    """Mock gRPC context for testing"""
    def __init__(self):
        self.code = None
        self.details = None
        self.invocation_metadata = []
        
    def set_code(self, code):
        self.code = code
        
    def set_details(self, details):
        self.details = details
        
    def invocation_metadata(self):
        return self.invocation_metadata


class TestUserHandler:
    """Test the UserHandler business logic"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_storage = Mock()
        self.handler = UserHandler(self.mock_storage)
        
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = self.handler._hash_password(password)
        
        # Verify it's properly hashed
        assert hashed != password
        assert bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
    def test_verify_password(self):
        """Test password verification"""
        password = "test_password_123"
        hashed = self.handler._hash_password(password)
        
        # Correct password should verify
        assert self.handler._verify_password(password, hashed)
        
        # Wrong password should not verify
        assert not self.handler._verify_password("wrong_password", hashed)
        
    def test_create_access_token(self):
        """Test JWT access token creation"""
        user_id = "test-user-id"
        username = "testuser"
        
        token = self.handler._create_access_token(user_id, username)
        
        # Verify token structure
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Decode and verify payload
        payload = jwt.decode(token, self.handler.access_secret, algorithms=['HS256'])
        assert payload['user_id'] == user_id
        assert payload['username'] == username
        assert payload['type'] == 'access'
        
    def test_create_refresh_token(self):
        """Test JWT refresh token creation"""
        user_id = "test-user-id"
        username = "testuser"
        
        token = self.handler._create_refresh_token(user_id, username)
        
        # Verify token structure
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Decode and verify payload
        payload = jwt.decode(token, self.handler.refresh_secret, algorithms=['HS256'])
        assert payload['user_id'] == user_id
        assert payload['username'] == username
        assert payload['type'] == 'refresh'
        
    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        user_id = "test-user-id"
        username = "testuser"
        
        # Create a valid token
        token = self.handler._create_access_token(user_id, username)
        
        # Verify it
        payload = self.handler._verify_token(token, 'access')
        assert payload['user_id'] == user_id
        assert payload['username'] == username
        
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        # Test with invalid token
        result = self.handler._verify_token("invalid.token.here", 'access')
        assert result is None
        
        # Test with expired token
        expired_payload = {
            'user_id': 'test-user-id',
            'username': 'testuser',
            'type': 'access',
            'exp': datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, self.handler.access_secret, algorithm='HS256')
        result = self.handler._verify_token(expired_token, 'access')
        assert result is None
        
    def test_register_user_success(self):
        """Test successful user registration"""
        # Mock storage to return None (user doesn't exist)
        self.mock_storage.get_by_username.return_value = None
        self.mock_storage.get_by_email.return_value = None
        
        # Mock successful user creation
        created_user = User(
            user_id="test-user-id",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            last_login=None
        )
        self.mock_storage.create.return_value = created_user
        
        # Test registration
        result = self.handler.register_user("testuser", "test@example.com", "password123")
        
        # Verify result
        assert result['success'] is True
        assert result['user_id'] == "test-user-id"
        assert "successfully registered" in result['message'].lower()
        
        # Verify storage calls
        self.mock_storage.get_by_username.assert_called_once_with("testuser")
        self.mock_storage.get_by_email.assert_called_once_with("test@example.com")
        self.mock_storage.create.assert_called_once()
        
    def test_register_user_duplicate_username(self):
        """Test registration with duplicate username"""
        # Mock storage to return existing user
        existing_user = User(
            user_id="existing-user-id",
            username="testuser",
            email="other@example.com",
            password_hash="hashed_password",
            last_login=None
        )
        self.mock_storage.get_by_username.return_value = existing_user
        
        # Test registration
        result = self.handler.register_user("testuser", "test@example.com", "password123")
        
        # Verify result
        assert result['success'] is False
        assert "username already exists" in result['message'].lower()
        
    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email"""
        # Mock storage to return None for username but existing user for email
        self.mock_storage.get_by_username.return_value = None
        existing_user = User(
            user_id="existing-user-id",
            username="otheruser",
            email="test@example.com",
            password_hash="hashed_password",
            last_login=None
        )
        self.mock_storage.get_by_email.return_value = existing_user
        
        # Test registration
        result = self.handler.register_user("testuser", "test@example.com", "password123")
        
        # Verify result
        assert result['success'] is False
        assert "email already exists" in result['message'].lower()


class TestUserService:
    """Test the UserService gRPC implementation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_handler = Mock()
        self.service = UserService(self.mock_handler)
        
    def test_register_success(self):
        """Test successful registration via gRPC"""
        # Mock handler response
        self.mock_handler.register_user.return_value = {
            'success': True,
            'message': 'User successfully registered',
            'user_id': 'test-user-id'
        }
        
        # Create request
        request = user_pb2.RegisterRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        # Call service
        response = self.service.Register(request, DummyContext())
        
        # Verify response
        assert response.success is True
        assert response.user_id == "test-user-id"
        assert "successfully registered" in response.message.lower()
        
        # Verify handler was called correctly
        self.mock_handler.register_user.assert_called_once_with(
            "testuser", "test@example.com", "password123"
        )
        
    def test_register_failure(self):
        """Test registration failure via gRPC"""
        # Mock handler response
        self.mock_handler.register_user.return_value = {
            'success': False,
            'message': 'Username already exists',
            'user_id': None
        }
        
        # Create request
        request = user_pb2.RegisterRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        # Call service
        response = self.service.Register(request, DummyContext())
        
        # Verify response
        assert response.success is False
        assert "username already exists" in response.message.lower()
        assert response.user_id == ""
        
    def test_login_with_username_success(self):
        """Test successful login with username"""
        # Mock handler response
        self.mock_handler.login_user.return_value = {
            'success': True,
            'message': 'Login successful',
            'user_id': 'test-user-id',
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token'
        }
        
        # Create request
        request = user_pb2.LoginRequest(
            username="testuser",
            password="password123"
        )
        
        # Call service
        response = self.service.Login(request, DummyContext())
        
        # Verify response
        assert response.success is True
        assert response.access_token == "test-access-token"
        assert response.refresh_token == "test-refresh-token"
        
    def test_login_with_email_success(self):
        """Test successful login with email"""
        # Mock handler response
        self.mock_handler.login_user.return_value = {
            'success': True,
            'message': 'Login successful',
            'user_id': 'test-user-id',
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token'
        }
        
        # Create request
        request = user_pb2.LoginRequest(
            email="test@example.com",
            password="password123"
        )
        
        # Call service
        response = self.service.Login(request, DummyContext())
        
        # Verify response
        assert response.success is True
        assert response.access_token == "test-access-token"
        
    def test_get_user_profile_success(self):
        """Test successful profile retrieval"""
        # Mock handler response
        self.mock_handler.get_user_profile.return_value = {
            'success': True,
            'message': 'Profile retrieved successfully',
            'username': 'testuser',
            'email': 'test@example.com',
            'created_ts': '2023-01-01T00:00:00Z'
        }
        
        # Create request
        request = user_pb2.UserProfileRequest(user_id="test-user-id")
        
        # Mock context with authorization header
        context = DummyContext()
        context.invocation_metadata = [('authorization', 'Bearer test-token')]
        
        # Call service
        response = self.service.GetUserProfile(request, context)
        
        # Verify response
        assert response.success is True
        assert response.profile.username == "testuser"
        assert response.profile.email == "test@example.com"


class TestUserServiceIntegration:
    """Integration tests for the User Service"""
    
    def test_proto_generation(self):
        """Test that proto files are generated correctly"""
        # Test that we can import the generated proto modules
        from khushal_hello_grpc.src.generated import user_pb2, user_pb2_grpc
        
        # Test that key classes exist
        assert hasattr(user_pb2, 'RegisterRequest')
        assert hasattr(user_pb2, 'RegisterResponse')
        assert hasattr(user_pb2, 'LoginRequest')
        assert hasattr(user_pb2, 'LoginResponse')
        assert hasattr(user_pb2, 'UserProfileRequest')
        assert hasattr(user_pb2, 'UserProfileResponse')
        assert hasattr(user_pb2_grpc, 'UserServiceServicer')
        assert hasattr(user_pb2_grpc, 'UserServiceStub')
        
    def test_create_proto_messages(self):
        """Test creating proto messages"""
        # Test RegisterRequest
        register_req = user_pb2.RegisterRequest(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        assert register_req.username == "testuser"
        assert register_req.email == "test@example.com"
        assert register_req.password == "password123"
        
        # Test LoginRequest with username
        login_req = user_pb2.LoginRequest(
            username="testuser",
            password="password123"
        )
        assert login_req.username == "testuser"
        assert login_req.password == "password123"
        
        # Test LoginRequest with email
        login_req_email = user_pb2.LoginRequest(
            email="test@example.com",
            password="password123"
        )
        assert login_req_email.email == "test@example.com"
        assert login_req_email.password == "password123"
        
    def test_user_model_creation(self):
        """Test User model creation and methods"""
        user = User(
            user_id="test-user-id",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            last_login=datetime.utcnow()
        )
        
        # Test basic attributes
        assert user.user_id == "test-user-id"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        
        # Test to_dict method
        user_dict = user.to_dict()
        assert user_dict['user_id'] == "test-user-id"
        assert user_dict['username'] == "testuser"
        assert user_dict['email'] == "test@example.com"
        
        # Test to_profile_dict method
        profile_dict = user.to_profile_dict()
        assert profile_dict['user_id'] == "test-user-id"
        assert profile_dict['username'] == "testuser"
        assert profile_dict['email'] == "test@example.com"
        assert 'password_hash' not in profile_dict  # Should not include password
        
    @pytest.mark.integration
    def test_user_service_server_startup(self):
        """Integration test: verify User Service can start up"""
        # This test verifies the server can import all dependencies and start
        # We'll mock the database connection to avoid needing a real DB
        
        with patch('khushal_hello_grpc.src.user_service.server.create_user_store') as mock_create_store, \
             patch('khushal_hello_grpc.src.user_service.server.grpc.server') as mock_grpc_server:
            
            # Mock the store creation
            mock_store = Mock()
            mock_create_store.return_value = mock_store
            
            # Mock the gRPC server
            mock_server_instance = Mock()
            mock_grpc_server.return_value = mock_server_instance
            
            # Import and test server creation
            from khushal_hello_grpc.src.user_service.server import create_server
            
            # This should not raise any import errors
            server = create_server()
            assert server is not None
            
            # Verify the server was configured correctly
            mock_grpc_server.assert_called_once()
            mock_create_store.assert_called_once()
            
    def test_build_verification(self):
        """Test that all User Service components can be imported"""
        # Test that all major components can be imported without errors
        from khushal_hello_grpc.src.user_service.models.user_models import User
        from khushal_hello_grpc.src.user_service.handlers.user_handler import UserHandler
        from khushal_hello_grpc.src.user_service.impl.user_service_impl import UserService
        from khushal_hello_grpc.src.user_service.storage.user_store import UserStore, PostgresUserStorage
        from khushal_hello_grpc.src.generated import user_pb2, user_pb2_grpc
        
        # Test that classes can be instantiated (with mocks where needed)
        mock_storage = Mock()
        handler = UserHandler(mock_storage)
        service = UserService(handler)
        
        # Verify they have expected methods
        assert hasattr(handler, 'register_user')
        assert hasattr(handler, 'login_user')
        assert hasattr(handler, 'get_user_profile')
        assert hasattr(service, 'Register')
        assert hasattr(service, 'Login')
        assert hasattr(service, 'GetUserProfile') 