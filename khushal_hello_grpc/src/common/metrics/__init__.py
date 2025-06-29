"""
Basic Prometheus metrics utilities.

Use decorators for automatic tracking:

    from khushal_hello_grpc.src.common.metrics import track_metrics
    
    @track_metrics()
    def handle_request(self, request, context):
        return "response"

Or import prometheus_client directly if needed:

    from prometheus_client import Counter, Gauge, Histogram
    my_counter = Counter('my_requests_total', 'My requests', ['method'])
    my_counter.labels(method='GET').inc()
"""

from khushal_hello_grpc.src.common.metrics.prometheus import (
    # Decorators
    track_metrics,
    track_database_operation,
    
    # Basic example metrics (optional to use)
    REQUEST_COUNT,
    REQUEST_DURATION,
    ACTIVE_REQUESTS,
    SPECIAL_REQUESTS_TOTAL,
    DATABASE_OPERATIONS_TOTAL,
)

__all__ = [
    'track_metrics',
    'track_database_operation',
    'REQUEST_COUNT',
    'REQUEST_DURATION',
    'ACTIVE_REQUESTS',
    'SPECIAL_REQUESTS_TOTAL',
    'DATABASE_OPERATIONS_TOTAL',
] 