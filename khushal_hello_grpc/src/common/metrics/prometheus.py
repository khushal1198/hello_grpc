"""
Basic Prometheus metrics utilities for gRPC service.

Simple metric definitions for direct prometheus_client usage.
"""

import logging
import time
import functools
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)


# Basic metrics - you can use these as templates
REQUEST_COUNT = Counter(
    'grpc_requests_total',
    'Total gRPC requests',
    ['method', 'status']
)

REQUEST_DURATION = Histogram(
    'grpc_request_duration_seconds',
    'gRPC request duration',
    ['method']
)

ACTIVE_REQUESTS = Gauge(
    'grpc_active_requests',
    'Currently active gRPC requests'
)

# Custom business metrics for substring detection
SPECIAL_REQUESTS_TOTAL = Counter(
    'grpc_special_requests_total',
    'Special gRPC requests based on content',
    ['pattern_type', 'method']
)

# Database metrics
DATABASE_OPERATIONS_TOTAL = Counter(
    'database_operations_total',
    'Total database operations',
    ['operation', 'table', 'status']
)

logger.info("Basic Prometheus metrics initialized")


def track_metrics(method_name=None, analyze_content=True):
    """
    Decorator to automatically track metrics for gRPC methods.
    
    Usage:
        @track_metrics()
        def handle_say_hello(self, request, context):
            return self._process_request(request)
        
        @track_metrics("CustomMethod")
        def custom_handler(self, request, context):
            return "response"
    
    :param method_name: Override method name for metrics (auto-detected if None)
    :param analyze_content: Whether to analyze request content for patterns
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract method name from function or use override
            actual_method_name = method_name or func.__name__.replace('handle_', '').replace('_', '')
            
            # Try to extract request data for content analysis
            request = None
            if len(args) >= 2:  # self, request, [context]
                request = args[1]
            
            start_time = time.time()
            status = "success"
            
            # Track active requests
            ACTIVE_REQUESTS.inc()
            
            try:
                # Call the actual function
                result = func(*args, **kwargs)
                
                # Analyze request content if enabled and request available
                if analyze_content and request and hasattr(request, 'name'):
                    _analyze_request_content(request.name, actual_method_name)
                
                return result
                
            except Exception as e:
                status = "error"
                logger.error(f"Error in {actual_method_name}: {e}")
                raise
            
            finally:
                # Record metrics
                duration = time.time() - start_time
                
                REQUEST_COUNT.labels(method=actual_method_name, status=status).inc()
                REQUEST_DURATION.labels(method=actual_method_name).observe(duration)
                ACTIVE_REQUESTS.dec()
                
                logger.debug(f"Metrics recorded for {actual_method_name}: {status} in {duration:.3f}s")
        
        return wrapper
    return decorator


def track_database_operation(operation, table):
    """
    Decorator to track database operations.
    
    Usage:
        @track_database_operation("insert", "grpc_requests")
        def store_request(self, name, response):
            return self.db.insert(...)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                status = "success" if result else "error"
                DATABASE_OPERATIONS_TOTAL.labels(
                    operation=operation, 
                    table=table, 
                    status=status
                ).inc()
                return result
            except Exception as e:
                DATABASE_OPERATIONS_TOTAL.labels(
                    operation=operation,
                    table=table,
                    status="error"
                ).inc()
                raise
        return wrapper
    return decorator


def _analyze_request_content(content: str, method: str):
    """Analyze request content and emit conditional metrics"""
    if not content:
        return
    
    content_lower = content.lower()
    
    # Emit metric if 'admin' substring found
    if 'admin' in content_lower:
        SPECIAL_REQUESTS_TOTAL.labels(pattern_type='admin_keyword', method=method).inc()
    
    # Emit metric if 'test' substring found  
    if 'test' in content_lower:
        SPECIAL_REQUESTS_TOTAL.labels(pattern_type='test_keyword', method=method).inc()
    
    # Emit metric for long names
    if len(content) > 20:
        SPECIAL_REQUESTS_TOTAL.labels(pattern_type='long_name', method=method).inc()
    
    # Emit metric for names with numbers
    if any(c.isdigit() for c in content):
        SPECIAL_REQUESTS_TOTAL.labels(pattern_type='contains_numbers', method=method).inc()
    
    # Emit metric for names with special characters
    special_chars = set('<>&"\';()[]{}')
    if any(char in content for char in special_chars):
        SPECIAL_REQUESTS_TOTAL.labels(pattern_type='special_characters', method=method).inc() 