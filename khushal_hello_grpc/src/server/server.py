import grpc
import threading
import time
import os
import signal
import sys
import logging
from concurrent import futures
from khushal_hello_grpc.src.server.impl.service_impl import HelloService
from khushal_hello_grpc.src.generated import hello_pb2_grpc
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

# Import typed configuration system and stage management
from khushal_hello_grpc.src.server.config import get_config
from khushal_hello_grpc.src.common.utils import Stage, get_stage

# Configure basic logging (will enhance later)
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
from khushal_hello_grpc.src.server.storage import create_grpc_request_store
from khushal_hello_grpc.src.server.handlers import RequestHandler

# Set up logging for the server
logger = logging.getLogger(__name__)

# Global variables for cleanup
connection_pool = None
hello_service = None
request_handler = None

def cleanup_resources():
    """Cleanup database connections and other resources"""
    global connection_pool, hello_service, request_handler
    
    logger.info("Cleaning up server resources...")
    
    if hello_service and hasattr(hello_service, 'cleanup'):
        try:
            hello_service.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up HelloService: {e}")
    
    if request_handler:
        logger.info("Cleaning up RequestHandler...")
        # RequestHandler doesn't need explicit cleanup, but we track it
    
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
    server_port = 50051  # Hardcoded for now
    while True:
        logger.info(f"gRPC server running on port {server_port}... (Ctrl+C to stop)")
        time.sleep(10)

def serve():
    global connection_pool, hello_service, request_handler
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Get current stage and typed configuration
        stage = get_stage()
        config = get_config()
        
        logger.info(f"Starting gRPC server with Handler pattern architecture (stage: {stage})...")
        
        # Extract database configuration with full type safety
        database_url = config.database.url
        schema = config.database.schema
        pool_size = config.database.pool.size
        max_overflow = config.database.pool.max_overflow
        
        # Hardcoded server settings for now
        server_port = 50051
        server_workers = 10
        server_host = "[::]"
        
        logger.info(f"Connecting to database: {database_url.replace(database_url.split('@')[0].split('//')[-1], '***')}")
        logger.info(f"Using schema: {schema}")
        
        # Step 1: Create PostgreSQL connection pool using storage layer factories
        logger.info("Creating PostgreSQL connection pool...")
        
        # Try advanced implementation first
        if ENHANCED_POSTGRES_AVAILABLE and create_postgres_pool:
            try:
                connection_pool = create_postgres_pool(
                    database_url=database_url,
                    schema=schema,
                    pool_size=pool_size,
                    max_overflow=max_overflow
                )
                if connection_pool:
                    logger.info("Using advanced PostgreSQL connection pool with SQLAlchemy")
                else:
                    raise Exception("Advanced pool creation returned None")
            except Exception as e:
                logger.warning(f"Advanced PostgreSQL pool failed, falling back to simple: {e}")
                connection_pool = SimplePostgresConnectionPool(
                    database_url=database_url,
                    schema=schema
                )
                logger.info("Using simple PostgreSQL connection pool")
        else:
            # Use simple implementation
            connection_pool = SimplePostgresConnectionPool(
                database_url=database_url,
                schema=schema
            )
            logger.info("Using simple PostgreSQL connection pool")
        
        # Step 2: Create gRPC request store using the connection pool
        logger.info("Creating gRPC request storage...")
        grpc_store = create_grpc_request_store(connection_pool=connection_pool)
        
        # Step 3: Create RequestHandler with the storage
        logger.info("Creating RequestHandler with storage backend...")
        request_handler = RequestHandler(grpc_store=grpc_store)
        
        # Step 4: Create HelloService with injected RequestHandler
        logger.info("Initializing HelloService with RequestHandler dependency injection...")
        hello_service = HelloService(request_handler=request_handler)
        
        # Step 5: Create gRPC server
        logger.info(f"Creating gRPC server with {server_workers} worker threads...")
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=server_workers))
        hello_pb2_grpc.add_HelloServiceServicer_to_server(hello_service, server)
        
        # Add gRPC health checking (enabled for now)
        logger.info("Adding health check service...")
        health_servicer = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
        # Set the health status to SERVING for all services
        health_servicer.set('', health_pb2.HealthCheckResponse.SERVING)
        health_servicer.set('HelloService', health_pb2.HealthCheckResponse.SERVING)
        
        server.add_insecure_port(f'{server_host}:{server_port}')
        
        # Start status logger in background thread
        status_thread = threading.Thread(target=status_logger, daemon=True)
        status_thread.start()
        
        logger.info("gRPC server ready with Handler pattern architecture!")
        logger.info("Architecture: Server → Storage → RequestHandler → HelloService → gRPC")
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