import logging
from khushal_hello_grpc.src.generated import hello_pb2
from khushal_hello_grpc.src.generated import hello_pb2_grpc
from khushal_hello_grpc.src.server.handlers import RequestHandler

logger = logging.getLogger(__name__)

class HelloService(hello_pb2_grpc.HelloServiceServicer):
    def __init__(self, request_handler: RequestHandler):
        """
        Initialize HelloService with dependency injection.
        
        :param request_handler: RequestHandler instance for processing requests
        """
        self.request_handler = request_handler
        logger.info("HelloService initialized with RequestHandler")
    
    def SayHello(self, request, context):
        """
        gRPC SayHello method - delegates to RequestHandler for all processing.
        
        This is a thin protocol adapter that just handles gRPC specifics.
        """
        # Delegate all processing to the handler
        response_message = self.request_handler.handle_say_hello(request, context)
        
        # Return gRPC response
        return hello_pb2.HelloReply(message=response_message)
    
    def cleanup(self):
        """Cleanup method for any service-level resources"""
        logger.info("HelloService cleanup completed")
        # Note: RequestHandler and storage cleanup is managed at the server level 