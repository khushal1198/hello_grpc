load("@rules_python//python:defs.bzl", "py_binary", "py_library")
load("@my_pip_deps//:requirements.bzl", "requirement")

genrule(
    name = "generate_hello_grpc",
    srcs = ["protos/hello.proto"],
    outs = [
        "generated/hello_pb2.py",
        "generated/hello_pb2_grpc.py",
        "generated/__init__.py",
    ],
    cmd = "mkdir -p $(@D)/generated && touch $(@D)/generated/__init__.py && python3 -m grpc_tools.protoc -Iprotos --python_out=$(@D)/generated --grpc_python_out=$(@D)/generated $(location protos/hello.proto)",
    tools = [requirement("grpcio-tools")],
)

py_library(
    name = "hello_generated",
    srcs = [
        "generated/hello_pb2.py",
        "generated/hello_pb2_grpc.py",
        "generated/__init__.py",
    ],
    imports = ["generated"],
    deps = [requirement("protobuf")],
)

py_binary(
    name = "hello_server",
    srcs = ["server/server.py"],
    main = "server/server.py",
    deps = [":hello_generated", requirement("grpcio")],
) 