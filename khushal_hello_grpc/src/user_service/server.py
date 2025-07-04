"""
User Service - Main server implementation
"""

import grpc
import threading
import time
import os
import signal
import sys
import logging
from concurrent import futures

from khushal_hello_grpc.src.user_service.impl.user_service_impl import UserService
from khushal_hello_grpc.src.generated import user_pb2_grpc
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

# Import typed configuration system and stage management
from khushal_hello_grpc.src.user_service.config import get_config
from khushal_hello_grpc.src.common.utils import Stage, get_stage

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import PostgreSQL connection pool and storage factory
from khushal_hello_grpc.src.common.storage import (
    ENHANCED_POSTGRES_AVAILABLE,
    PostgresConnectionPool,
    create_postgres_pool,
    SimplePostgresConnectionPool
)
from khushal_hello_grpc.src.user_service.storage import create_user_store
from khushal_hello_grpc.src.user_service.handlers import UserHandler

# Set up logging for the server
logger = logging.getLogger(__name__)

# Global variables for cleanup
connection_pool = None
user_service = None
user_handler = None

def cleanup_resources():
    """Cleanup database connections and other resources"""
    global connection_pool, user_service, user_handler
    
    logger.info("Cleaning up server resources...")
    
    if user_service and hasattr(user_service, 'cleanup'):
        try:
            user_service.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up UserService: {e}")
    
    if connection_pool and hasattr(connection_pool, 'close'):
        try:
            connection_pool.close()
            logger.info("Database connection pool closed successfully")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    cleanup_resources()
    sys.exit(0)

def status_logger():
    """Log server status every 10 seconds"""
    server_port = 50052  # Different port from hello service
    while True:
        logger.info(f"User Service running on port {server_port}... (Ctrl+C to stop)")
        time.sleep(10)

def serve():
    global connection_pool, user_service, user_handler
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Get current stage and typed configuration
        stage = get_stage()
        config = get_config()
        
        logger.info(f"Starting User Service with Handler pattern architecture (stage: {stage})...")
        
        # Use different port from hello service
        server_port = 50052
        server_workers = 10
        server_host = "[::]"
        
        logger.info(f"Connecting to database: {config.database.url.replace(config.database.url.split('@')[0].split('//')[-1], '***')}")
        logger.info(f"Using schema: {config.database.schema}")
        
        # Step 1: Create PostgreSQL connection pool
        logger.info("Creating PostgreSQL connection pool...")
        
        if ENHANCED_POSTGRES_AVAILABLE and create_postgres_pool:
            try:
                connection_pool = create_postgres_pool(
                    database_url=config.database.url,
                    schema=config.database.schema,
                    pool_size=config.database.pool.size,
                    max_overflow=config.database.pool.max_overflow
                )
                if connection_pool:
                    logger.info("Using advanced PostgreSQL connection pool with SQLAlchemy")
                else:
                    raise Exception("Advanced pool creation returned None")
            except Exception as e:
                logger.warning(f"Advanced PostgreSQL pool failed, falling back to simple: {e}")
                connection_pool = SimplePostgresConnectionPool(
                    database_url=config.database.url,
                    schema=config.database.schema
                )
                logger.info("Using simple PostgreSQL connection pool")
        else:
            connection_pool = SimplePostgresConnectionPool(
                database_url=config.database.url,
                schema=config.database.schema
            )
            logger.info("Using simple PostgreSQL connection pool")
        
        # Step 2: Create user store using the connection pool
        logger.info("Creating user storage...")
        user_store = create_user_store(connection_pool=connection_pool)
        
        # Step 3: Create UserHandler with the storage
        logger.info("Creating UserHandler with storage backend...")
        user_handler = UserHandler(user_store=user_store)
        
        # Step 4: Create UserService with injected UserHandler
        logger.info("Initializing UserService with UserHandler dependency injection...")
        user_service = UserService(user_handler=user_handler)
        
        # Step 5: Create gRPC server
        logger.info(f"Creating gRPC server with {server_workers} worker threads...")
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=server_workers))
        user_pb2_grpc.add_UserServiceServicer_to_server(user_service, server)
        
        # Add gRPC health checking
        logger.info("Adding health check service...")
        health_servicer = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
        health_servicer.set('', health_pb2.HealthCheckResponse.SERVING)
        health_servicer.set('UserService', health_pb2.HealthCheckResponse.SERVING)
        
        server.add_insecure_port(f'{server_host}:{server_port}')
        
        # Start status logger in background thread
        status_thread = threading.Thread(target=status_logger, daemon=True)
        status_thread.start()
        
        logger.info("User Service ready with Handler pattern architecture!")
        logger.info("Architecture: Server → Storage → UserHandler → UserService → gRPC")
        logger.info(f"Server listening on {server_host}:{server_port}...")
        server.start()
        
        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        finally:
            cleanup_resources()
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        cleanup_resources()
        raise

if __name__ == "__main__":
    serve() 