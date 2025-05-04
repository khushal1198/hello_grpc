from src.server.impl.service_impl import HelloService
from src.generated import hello_pb2

class DummyContext:
    def set_code(self, code): pass
    def set_details(self, details): pass


def test_say_hello():
    service = HelloService()
    request = hello_pb2.HelloRequest(name="Test")
    response = service.SayHello(request, DummyContext())
    assert response.message == "Hello World" 