import grpc
import threading
import time
from khushal_hello_grpc.src.server.impl.service_impl import HelloService
from khushal_hello_grpc.src.generated import hello_pb2
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

class DummyContext:
    def set_code(self, code): pass
    def set_details(self, details): pass


def test_say_hello():
    service = HelloService()
    request = hello_pb2.HelloRequest(name="Test")
    response = service.SayHello(request, DummyContext())
    assert response.message == "Hello World"


def test_server_startup_and_health_check():
    """Integration test that starts the server and tests health check"""
    import sys
    import os
    # Add the server module to path for testing
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    # Import server module
    from khushal_hello_grpc.src.server.server import serve
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Test health check
        with grpc.insecure_channel('localhost:50051') as channel:
            health_stub = health_pb2_grpc.HealthStub(channel)
            
            # Test overall health
            response = health_stub.Check(health_pb2.HealthCheckRequest())
            assert response.status == health_pb2.HealthCheckResponse.SERVING
            
            # Test HelloService health
            response = health_stub.Check(health_pb2.HealthCheckRequest(service="HelloService"))
            assert response.status == health_pb2.HealthCheckResponse.SERVING
            
            # Test hello service
            hello_stub = hello_pb2_grpc.HelloServiceStub(channel)
            request = hello_pb2.HelloRequest(name="Integration Test")
            response = hello_stub.SayHello(request)
            assert response.message == "Hello World"
            
    except Exception as e:
        # Clean up and re-raise
        raise e
    finally:
        # Server will be cleaned up when thread exits (daemon=True)
        pass 