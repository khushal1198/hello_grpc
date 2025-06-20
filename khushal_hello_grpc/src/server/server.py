import grpc
import threading
import time
from concurrent import futures
from khushal_hello_grpc.src.server.impl.service_impl import HelloService
from khushal_hello_grpc.src.generated import hello_pb2_grpc
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

def status_printer():
    """Print server status every 10 seconds"""
    while True:
        print("gRPC server running on port 50051...")
        time.sleep(10)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hello_pb2_grpc.add_HelloServiceServicer_to_server(HelloService(), server)
    # Add gRPC health checking
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    # Set the health status to SERVING for all services
    health_servicer.set('', health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set('HelloService', health_pb2.HealthCheckResponse.SERVING)
    server.add_insecure_port('[::]:50051')
    
    # Start status printer in background thread
    status_thread = threading.Thread(target=status_printer, daemon=True)
    status_thread.start()
    
    print("gRPC server starting on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve() 