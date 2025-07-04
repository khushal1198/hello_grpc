# User Authentication Service

A secure gRPC-based user authentication service built with Python, featuring JWT token management, bcrypt password hashing, and PostgreSQL integration.

## Overview

The User Service provides complete authentication functionality for the expense tracking application, including user registration, login, profile management, and secure token-based authentication.

## Features

- **Secure Password Hashing**: Uses bcrypt for password storage
- **JWT Token Management**: Issues access tokens (30 min) and refresh tokens (7 days)
- **User Registration**: Create new accounts with username/email validation
- **Login Authentication**: Authenticate with username/email + password
- **Profile Management**: Retrieve user profile information
- **Database Integration**: PostgreSQL with proper schema management
- **gRPC API**: High-performance protocol buffer-based communication

## Database Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## gRPC Service Definition

The service is defined in `protos/user.proto` with the following endpoints:

### Service: `khushal_hello_grpc.user.UserService`

#### 1. Register
- **Request**: `RegisterRequest`
  - `username` (string): Unique username
  - `email` (string): Unique email address
  - `password` (string): Plain text password (hashed server-side)
- **Response**: `RegisterResponse`
  - `success` (bool): Registration success status
  - `message` (string): Success/error message
  - `user_id` (string): UUID of created user (if successful)

#### 2. Login
- **Request**: `LoginRequest`
  - `credential` (oneof): Either username or email
  - `password` (string): Plain text password
- **Response**: `LoginResponse`
  - `success` (bool): Login success status
  - `message` (string): Success/error message
  - `access_token` (string): JWT access token (30 min expiry)
  - `refresh_token` (string): JWT refresh token (7 days expiry)
  - `user_id` (string): UUID of authenticated user

#### 3. GetUserProfile
- **Request**: `UserProfileRequest`
  - `user_id` (string): UUID of user (validated against JWT)
- **Response**: `UserProfileResponse`
  - `success` (bool): Request success status
  - `message` (string): Success/error message
  - `username` (string): User's username
  - `email` (string): User's email
  - `created_ts` (string): Account creation timestamp

## Quick Start

### Build and Run
```bash
# Build the service
bazel build //khushal_hello_grpc/src/user_service:user_service

# Run the service (Port 50052)
bazel run //khushal_hello_grpc/src/user_service:user_service
```

### Docker
```bash
# Build Docker image
docker build -f docker/Dockerfile.user -t user_service:latest .

# Run container
docker run -p 50052:50052 user_service:latest
```

## API Examples

### Using grpcurl

**Register a new user:**
```bash
grpcurl -plaintext -d '{
  "username": "john_doe", 
  "email": "john@example.com", 
  "password": "securePassword123"
}' localhost:50052 khushal_hello_grpc.user.UserService/Register
```

**Login with username:**
```bash
grpcurl -plaintext -d '{
  "username": "john_doe", 
  "password": "securePassword123"
}' localhost:50052 khushal_hello_grpc.user.UserService/Login
```

**Login with email:**
```bash
grpcurl -plaintext -d '{
  "email": "john@example.com", 
  "password": "securePassword123"
}' localhost:50052 khushal_hello_grpc.user.UserService/Login
```

**Get user profile (requires JWT token):**
```bash
grpcurl -plaintext \
  -H "authorization: Bearer YOUR_JWT_ACCESS_TOKEN" \
  -d '{"user_id": "your-user-uuid"}' \
  localhost:50052 khushal_hello_grpc.user.UserService/GetUserProfile
```

### Example Response

**Successful Login Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "userId": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Architecture

The User Service follows a clean architecture pattern:

```
khushal_hello_grpc/src/user_service/
├── server.py                    # gRPC server entry point
├── models/
│   └── user_models.py          # User data model
├── storage/
│   └── user_store.py           # Database abstraction layer
├── handlers/
│   └── user_handler.py         # Business logic layer
├── impl/
│   └── user_service_impl.py    # gRPC service implementation
└── config/
    ├── dev.yaml                # Development configuration
    └── prod.yaml               # Production configuration
```

### Key Components

#### 1. Models (`models/user_models.py`)
- `User` class extending `Storable` base class
- Immutable dataclass with proper serialization methods
- Fields: username, email, password_hash, last_login

#### 2. Storage (`storage/user_store.py`)
- Abstract `UserStore` interface
- `PostgresUserStorage` implementation using connection pooling
- CRUD operations with proper error handling

#### 3. Handlers (`handlers/user_handler.py`)
- `UserHandler` class containing business logic
- JWT token generation and validation
- Password hashing with bcrypt
- User authentication and authorization

#### 4. Service Implementation (`impl/user_service_impl.py`)
- `UserService` class extending generated gRPC servicer
- Request/response handling and validation
- Error handling and logging
- Authentication middleware for protected endpoints

## Security Features

### Password Security
- **bcrypt hashing**: Industry-standard password hashing with salt
- **No plaintext storage**: Passwords are hashed immediately upon registration
- **Secure comparison**: Uses bcrypt's built-in timing-attack-resistant comparison

### JWT Token Security
- **Short-lived access tokens**: 30-minute expiry for security
- **Long-lived refresh tokens**: 7-day expiry for user convenience
- **Secure secrets**: JWT signing keys (update for production!)
- **Bearer token authentication**: Standard Authorization header format

### Database Security
- **UUID primary keys**: Prevents enumeration attacks
- **Unique constraints**: Username and email uniqueness enforced at DB level
- **Prepared statements**: Protection against SQL injection (via SQLAlchemy)

## Configuration

The service uses YAML configuration files:

### Development (`config/dev.yaml`)
```yaml
database:
  host: localhost
  port: 5432
  database: expense_tracker_dev
  username: dev_user
  password: dev_password
  pool_size: 5
  max_overflow: 10

jwt:
  access_secret: dev_access_secret_key
  refresh_secret: dev_refresh_secret_key
  access_expiry_minutes: 30
  refresh_expiry_days: 7

server:
  port: 50052
  max_workers: 10
```

### Production (`config/prod.yaml`)
```yaml
database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  database: ${DB_NAME}
  username: ${DB_USER}
  password: ${DB_PASSWORD}
  pool_size: 20
  max_overflow: 30

jwt:
  access_secret: ${JWT_ACCESS_SECRET}
  refresh_secret: ${JWT_REFRESH_SECRET}
  access_expiry_minutes: 30
  refresh_expiry_days: 7

server:
  port: 50052
  max_workers: 50
```

## Dependencies

The service requires the following Python packages:

```
# Core gRPC
grpcio==1.71.0
grpcio-tools==1.71.0
protobuf==5.29.4

# Authentication
PyJWT==2.10.1
bcrypt==4.3.0

# Database
psycopg2-binary==2.9.10
sqlalchemy==2.0.36

# Configuration
pydantic==2.10.4
PyYAML==6.0.2

# Utilities
python-dotenv==1.0.1
```

## Error Handling

The service provides comprehensive error handling:

### Registration Errors
- **Username exists**: Returns error if username is already taken
- **Email exists**: Returns error if email is already registered
- **Invalid input**: Validates username/email format and password strength

### Login Errors
- **Invalid credentials**: Returns generic error for security (no user enumeration)
- **Account not found**: Same generic error message
- **Server errors**: Proper logging with user-friendly messages

### Authentication Errors
- **Missing token**: Returns unauthenticated error
- **Invalid token**: Returns unauthenticated error with details
- **Expired token**: Specific error message for token expiry
- **Malformed authorization**: Proper Bearer token format validation

## Development

### Running Tests
```bash
# Run all tests
bazel test //khushal_hello_grpc/tests:test_server

# Run with coverage
bazel coverage //khushal_hello_grpc/tests:test_server
```

### Database Setup
1. Install PostgreSQL
2. Create database and user
3. Update configuration files
4. Run migrations (if applicable)

### Adding New Endpoints
1. Update `protos/user.proto` with new RPC methods
2. Regenerate proto files: `bazel build //khushal_hello_grpc/src/generated:generated`
3. Implement business logic in `UserHandler`
4. Add gRPC method to `UserService`
5. Add tests for new functionality

## Production Deployment

### Environment Variables
Set the following environment variables for production:

```bash
# Database
export DB_HOST=your-postgres-host
export DB_PORT=5432
export DB_NAME=expense_tracker
export DB_USER=your-db-user
export DB_PASSWORD=your-db-password

# JWT Secrets (use strong, random values!)
export JWT_ACCESS_SECRET=your-very-secure-access-secret
export JWT_REFRESH_SECRET=your-very-secure-refresh-secret
```

### Docker Deployment
```bash
# Build production image
docker build -f docker/Dockerfile.user -t user_service:prod .

# Run with environment variables
docker run -p 50052:50052 \
  -e DB_HOST=your-db-host \
  -e DB_PASSWORD=your-db-password \
  -e JWT_ACCESS_SECRET=your-secret \
  user_service:prod
```

### Kubernetes Deployment
The service is automatically deployed via GitHub Actions to Kubernetes. See the main project's CI/CD documentation for details.

## Monitoring and Logging

The service includes:
- **Structured logging**: JSON format for production
- **Health checks**: Docker health check endpoint
- **Error tracking**: Comprehensive error logging
- **Performance metrics**: Request timing and success rates

## Security Considerations for Production

1. **Update JWT secrets**: Use cryptographically secure random strings
2. **Enable TLS**: Use TLS encryption for gRPC communication
3. **Rate limiting**: Implement rate limiting for authentication endpoints
4. **Input validation**: Additional validation for edge cases
5. **Audit logging**: Log all authentication events
6. **Token rotation**: Implement refresh token rotation
7. **Password policies**: Enforce strong password requirements

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update this documentation for any API changes
4. Use type hints and docstrings for new functions
5. Run linters and formatters before submitting changes

## License

This project is part of the hello_grpc demonstration application. 