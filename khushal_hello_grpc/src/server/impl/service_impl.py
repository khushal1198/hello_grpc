from khushal_hello_grpc.src.generated import hello_pb2
from khushal_hello_grpc.src.generated import hello_pb2_grpc

class HelloService(hello_pb2_grpc.HelloServiceServicer):
    def SayHello(self, request, context):
        # Business logic goes here!
        return hello_pb2.HelloReply(message="Hello World") 