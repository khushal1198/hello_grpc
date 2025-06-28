# gRPC Requests PostgreSQL Schema

Simple schema for storing gRPC requests in PostgreSQL.

## Schema

**Table:** `grpc_requests`

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) PRIMARY KEY | UUID string |
| `created_ts` | TIMESTAMP WITH TIME ZONE NOT NULL | Creation timestamp |
| `last_updated_ts` | TIMESTAMP WITH TIME ZONE NOT NULL | Last update timestamp |
| `request_name` | TEXT NOT NULL | gRPC request name |
| `response_message` | TEXT NOT NULL | Response message |
| `metadata` | JSONB | JSON metadata |

## Usage

Apply schema:
```bash
psql -h <host> -p <port> -U <user> -d <database> -f grpc_requests_schema.sql
```

Example queries:
```sql
-- Recent requests
SELECT * FROM grpc_requests ORDER BY created_ts DESC LIMIT 10;

-- Filter by name
SELECT * FROM grpc_requests WHERE request_name = 'health_check';

-- JSON queries
SELECT * FROM grpc_requests WHERE metadata->>'service' = 'HelloService';
``` 