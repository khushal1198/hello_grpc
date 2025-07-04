# PostgreSQL Database Schemas

Database schemas for the gRPC services.

## Tables

### 1. gRPC Requests Table (`grpc_requests_schema.sql`)
- `id` (VARCHAR 36) - Primary key
- `created_ts` - Creation timestamp
- `last_updated_ts` - Last update timestamp
- `request_name` - gRPC request name
- `response_message` - Response message
- `metadata` - JSON metadata

### 2. Users Table (`users_schema.sql`)
- `id` (UUID) - Primary key (auto-generated)
- `created_ts` - Account creation timestamp
- `last_updated_ts` - Last update timestamp
- `username` (VARCHAR 50) - Unique username
- `email` (VARCHAR 255) - Unique email address
- `password_hash` - Bcrypt hashed password
- `last_login` - Last login timestamp

## Usage

```bash
# Apply schemas
psql -h localhost -p 5432 -U dev_user -d myapp -f grpc_requests_schema.sql
psql -h localhost -p 5432 -U dev_user -d myapp -f users_schema.sql
``` 