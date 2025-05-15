# syntax=docker/dockerfile:1

# --- Runtime Stage: Python 3.11 with gRPC ---
FROM python:3.11-slim

# Add labels for better container management
LABEL org.opencontainers.image.source="https://github.com/khushalpujara/hello_grpc"
LABEL org.opencontainers.image.description="gRPC Hello World Service"
LABEL org.opencontainers.image.licenses="MIT"

# Set the working directory inside the container
WORKDIR /app

# Install Python dependencies (from lock file for reproducibility)
COPY requirements_lock.txt ./
RUN pip install --no-cache-dir -r requirements_lock.txt \
    # grpcio-tools is needed for proto code generation
    && pip install --no-cache-dir grpcio-tools

# Copy the full Python package source tree (including __init__.py files)
COPY khushal_hello_grpc/ ./khushal_hello_grpc/

# Copy proto definitions into the image for code generation
COPY protos/hello.proto /app/protos/hello.proto

# Generate Python gRPC code from the proto file
# - Outputs to the correct package directory
# - Touches __init__.py to ensure it's a package
# - Patches hello_pb2_grpc.py to use relative imports (required for Bazel-style package structure)
RUN python -m grpc_tools.protoc -I/app/protos \
    --python_out=/app/khushal_hello_grpc/src/generated \
    --grpc_python_out=/app/khushal_hello_grpc/src/generated \
    /app/protos/hello.proto \
    && touch /app/khushal_hello_grpc/src/generated/__init__.py \
    && sed -i 's/import hello_pb2 as hello__pb2/from . import hello_pb2 as hello__pb2/' \
    /app/khushal_hello_grpc/src/generated/hello_pb2_grpc.py

# Copy the Bazel-built server binary (adjust path if needed)
COPY khushal_hello_grpc/src/server/server.py ./
COPY khushal_hello_grpc/src/server/impl ./impl
COPY khushal_hello_grpc/src/generated ../generated

# Expose the gRPC port
EXPOSE 50051

ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import grpc; grpc.insecure_channel('localhost:50051').connect()"

# Entrypoint: run the gRPC server
ENTRYPOINT ["python", "khushal_hello_grpc/src/server/server.py"] 