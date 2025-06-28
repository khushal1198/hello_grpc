"""
Common storage layer for the gRPC service.

Provides generic DatabaseStore interface, specific implementations, and distributed locking.
Features both simple and production-ready PostgreSQL implementations.
"""

# Core database operations
from khushal_hello_grpc.src.common.storage.database import DatabaseStore, PostgresConnectionPool as SimplePostgresConnectionPool, retry

# Try enhanced PostgreSQL features (SQLAlchemy, etc.)
try:
    from khushal_hello_grpc.src.common.storage.postgres import (
        PostgresConnectionPool,
        create_postgres_pool
    )
    ENHANCED_POSTGRES_AVAILABLE = True
except ImportError as e:
    # Log what's missing
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Enhanced PostgreSQL features not available: {e}")
    
    # Create stub implementations
    PostgresConnectionPool = None
    create_postgres_pool = None
    ENHANCED_POSTGRES_AVAILABLE = False

# Storage models and utilities  
from khushal_hello_grpc.src.common.storage.models import (
    Storable,
    ConnectionPool
)

# Distributed locking
from khushal_hello_grpc.src.common.storage.lock_manager import (
    DistributedLockManager,
    PostgresLockManager,
    create_lock_manager
)

from khushal_hello_grpc.src.common.storage.models import (
    DatabaseType, 
    PostgresConfig, DatabaseConfig, AdditionalFilter,
    CREATED_TS_FIELD, ID_FIELD, LAST_UPDATED_TS_FIELD
)

__all__ = [
    # Core storage
    "DatabaseStore",
    "SimplePostgresConnectionPool",
    "ConnectionPool", 
    "Storable",
    "DatabaseType",
    "PostgresConfig",
    "DatabaseConfig",
    "AdditionalFilter",
    "CREATED_TS_FIELD",
    "ID_FIELD", 
    "LAST_UPDATED_TS_FIELD",
    
    # Advanced PostgreSQL (if available)
    "PostgresConnectionPool",
    "create_postgres_pool",
    "ENHANCED_POSTGRES_AVAILABLE",
    
    # Distributed locking
    "DistributedLockManager",
    "PostgresLockManager", 
    "create_lock_manager",
    
    # Utilities
    "retry"
] 