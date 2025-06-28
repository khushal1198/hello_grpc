-- gRPC Requests Table Schema

CREATE TABLE IF NOT EXISTS grpc_requests (
    id VARCHAR(36) PRIMARY KEY,
    created_ts TIMESTAMP WITH TIME ZONE NOT NULL,
    last_updated_ts TIMESTAMP WITH TIME ZONE NOT NULL,
    request_name TEXT NOT NULL,
    response_message TEXT NOT NULL,
    metadata JSONB
); 