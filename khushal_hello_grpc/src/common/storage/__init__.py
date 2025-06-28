"""
Common storage layer for the gRPC service.

Provides generic DatabaseStore interface, specific implementations, and distributed locking.
Features both simple and production-ready PostgreSQL implementations.
"""

from .database import DatabaseStore, PostgresConnectionPool as SimplePostgresConnectionPool, retry

# Import advanced PostgreSQL implementation if available
try:
    from .postgres import (
        PostgresConnectionPool, PostgresConnection, PostgresCursor,
        StatementExecutor, PostgresUpdateNode, UpdateStatementInput,
        create_postgres_pool
    )
    ADVANCED_POSTGRES_AVAILABLE = True
except ImportError:
    ADVANCED_POSTGRES_AVAILABLE = False
    PostgresConnectionPool = None
    PostgresConnection = None
    PostgresCursor = None
    StatementExecutor = None
    PostgresUpdateNode = None
    UpdateStatementInput = None
    create_postgres_pool = None

from .models import (
    ConnectionPool, Storable, DatabaseType, 
    PostgresConfig, DatabaseConfig, AdditionalFilter,
    CREATED_TS_FIELD, ID_FIELD, LAST_UPDATED_TS_FIELD
)
from .lock_manager import (
    DistributedLockManager, PostgresLockManager, InMemoryLockManager, 
    create_lock_manager
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
    "PostgresConnection",
    "PostgresCursor", 
    "StatementExecutor",
    "PostgresUpdateNode",
    "UpdateStatementInput",
    "create_postgres_pool",
    "ADVANCED_POSTGRES_AVAILABLE",
    
    # Distributed locking
    "DistributedLockManager",
    "PostgresLockManager", 
    "InMemoryLockManager",
    "create_lock_manager",
    
    # Utilities
    "retry"
] 