# Python gRPC Service with Bazel: Project Guide

## Prerequisites

- **Docker**: Required for building and running container images.
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS/Windows)
  - Or follow the [official Docker Engine install guide](https://docs.docker.com/engine/install/) (Linux)

## Overview
This project is a minimal, production-grade Python gRPC service built and managed with Bazel. It demonstrates best practices for Bazel Python projects, including:
- Modern dependency management with bzlmod (`MODULE.bazel`)
- gRPC service definition and code generation
- Clean Bazel package structure
- Robust handling of Python imports and generated code
- **Multi-service architecture with Hello, User Authentication, and Web UI**
- **Containerization with Docker** (see below)
- **Automated CI/CD with GitHub Actions** (see below)

---

## Quickstart Commands

### Build and run Hello Service (Port 50051)
```sh
# Build the Hello server
bazel build //khushal_hello_grpc/src/server:hello_server

# Run the Hello server
bazel run //khushal_hello_grpc/src/server:hello_server
```

### Build and run User Service (Port 50052) 🆕
```sh
# Build the User service
bazel build //khushal_hello_grpc/src/user_service:user_service

# Run the User service  
bazel run //khushal_hello_grpc/src/user_service:user_service
```

> **📖 For detailed User Service documentation** (authentication, JWT tokens, API examples), see [`khushal_hello_grpc/src/user_service/README.md`](khushal_hello_grpc/src/user_service/README.md)

### Build and run UI Service (Port 8081)
```sh
# Build the UI server
bazel build //khushal_hello_grpc/src/ui/server:ui_server

# Run the UI server
bazel run //khushal_hello_grpc/src/ui/server:ui_server
```

### Run tests
```sh
bazel test //khushal_hello_grpc/tests:test_server
```

### Update Python dependencies
```sh
python3 -m piptools compile requirements.in --output-file=requirements_lock.txt --allow-unsafe
```
> **Note:** We use `requirements_lock.txt` (not the default `requirements.txt`) to ensure fully reproducible builds for Bazel. The `--output-file` flag is required because piptools by default writes to `requirements.txt`, but Bazel bzlmod expects a lock file with a custom name. The `--allow-unsafe` flag is necessary for Bazel because some dependencies (like grpcio-tools) require "unsafe" packages (such as setuptools) to be present in the lock file.

---

## Service Architecture 🏗️

This project includes **three services** working together:

### 1. **Hello Service** (Port 50051)
- **Purpose**: Simple greeting service for demonstrations
- **Proto**: `hello.proto` 
- **Endpoints**: `SayHello(HelloRequest) → HelloReply`

### 2. **User Service** (Port 50052) 🆕
- **Purpose**: User authentication and management with JWT tokens
- **Proto**: `user.proto`
- **Features**: User registration, login, profile management, secure password hashing
- **📖 Full Documentation**: [`khushal_hello_grpc/src/user_service/README.md`](khushal_hello_grpc/src/user_service/README.md)

### 3. **UI Service** (Port 8081)
- **Purpose**: Web interface for testing both Hello and User services
- **Framework**: aiohttp with static file serving
- **Features**: Health monitoring, real-time gRPC calls, modern responsive UI

---

## Web UI for Testing gRPC Calls

This project includes a web-based UI that allows you to interact with your gRPC services through a browser. The UI provides:

- **Real-time gRPC calls**: Send requests to both Hello and User services
- **Authentication testing**: Register users, login, test JWT tokens
- **Server health monitoring**: Check if gRPC servers are running and healthy
- **Beautiful interface**: Modern, responsive design with real-time status updates
- **Connection status**: Visual indicator showing connection to the gRPC servers

### How to use the UI:

1. **Start the Hello Service** (in one terminal):
   ```sh
   bazel run //khushal_hello_grpc/src/server:hello_server
   ```

2. **Start the User Service** (in another terminal):
   ```sh
   bazel run //khushal_hello_grpc/src/user_service:user_service
   ```

3. **Start the UI server** (in a third terminal):
   ```sh
   bazel run //khushal_hello_grpc/src/ui/server:ui_server
   ```

4. **Open your browser** and go to:
   ```
   http://localhost:8081/static/index.html
   ```

5. **Test the services**:
   - **Hello Service**: Enter a name and click "Send Hello Request"
   - **User Service**: Register a new user, login to get JWT tokens
   - **Health Checks**: Monitor both services' health status
   - **Authentication**: Test protected endpoints with JWT tokens

### How the UI works:

- **UI Server**: Runs on port 8081, serves static files and acts as a proxy
- **gRPC Clients**: Makes actual gRPC calls to services on ports 50051 and 50052
- **Web Interface**: Modern HTML/CSS/JS frontend with real-time updates
- **Fallback Mode**: If gRPC servers are unavailable, shows helpful error messages

The UI automatically detects connection status and provides helpful feedback for debugging.

---

## Testing

Tests are located in `khushal_hello_grpc/tests` and use pytest. Bazel's test runner handles pytest automatically.

```sh
# Run all tests
bazel test //khushal_hello_grpc/tests:test_server

# Run with verbose output
bazel test //khushal_hello_grpc/tests:test_server --test_output=all

# Run with coverage
bazel coverage //khushal_hello_grpc/tests:test_server
```

### Writing Tests
1. Place test files in the `khushal_hello_grpc/tests` directory
2. Name test files with `test_` prefix (e.g., `test_server.py`)
3. Name test functions with `test_` prefix
4. Use pytest fixtures and assertions

Example test structure:
```python
def test_hello_service():
    # Arrange
    service = HelloService()
    
    # Act
    response = service.SayHello(request)
    
    # Assert
    assert response.message == "Hello, World!"
```

### Test Dependencies
- Tests use pytest (included in requirements_lock.txt)
- No need to add pytest to BUILD.bazel deps - Bazel's test runner handles pytest automatically
- Use `requirement("pytest")` only if you need specific pytest features

---

## Docker Containerization (Production/CI/CD)

This project includes Dockerfiles for all three services:

### Build all Docker images
```sh
# Hello Service
docker build -f docker/Dockerfile.grpc -t hello_server:latest .

# User Service 🆕
docker build -f docker/Dockerfile.user -t user_service:latest .

# UI Service  
docker build -f docker/Dockerfile.ui -t ui_server:latest .
```

### Run individual containers
```sh
# Hello Service (port 50051)
docker run -p 50051:50051 hello_server:latest

# User Service (port 50052) 🆕
docker run -p 50052:50052 user_service:latest

# UI Service (port 8081)
docker run -p 8081:8081 ui_server:latest
```

### Run all services with Docker Compose
```sh
# Start all services
docker-compose -f docker/docker-compose.yml up --build

# Services will be available on:
# - Hello Service: localhost:50051
# - User Service: localhost:50052  🆕
# - UI Service: localhost:8081
```

#### How the Dockerfiles work:
1. **Install dependencies** from `requirements_lock.txt` (including authentication libs like PyJWT, bcrypt)
2. **Copy your full Python package** and both proto files into the image
3. **Generate Python gRPC code** for both `hello.proto` and `user.proto` at build time
4. **Patch generated files** to use relative imports (avoids import errors)
5. **Set `PYTHONPATH`** so your code can use absolute imports
6. **Health checks** for all services
7. **Entrypoint** runs the respective service

---

## Project Structure
```
hello_grpc/
├── khushal_hello_grpc/
│   ├── src/
│   │   ├── server/                    # Hello Service (Port 50051)
│   │   │   ├── server.py
│   │   │   └── impl/
│   │   │       └── service_impl.py
│   │   ├── user_service/              # 🆕 User Service (Port 50052)
│   │   │   ├── server.py
│   │   │   ├── README.md             # 📖 Detailed User Service docs
│   │   │   ├── models/user_models.py
│   │   │   ├── storage/user_store.py
│   │   │   ├── handlers/user_handler.py
│   │   │   ├── impl/user_service_impl.py
│   │   │   └── config/(dev|prod).yaml
│   │   ├── ui/                        # UI Service (Port 8081)
│   │   │   ├── server/server.py
│   │   │   └── frontend/static/
│   │   │       ├── index.html
│   │   │       ├── style.css
│   │   │       └── client.js
│   │   ├── generated/                 # 🔧 Unified proto generation
│   │   │   ├── BUILD.bazel           # Simplified: one 'generated' target  
│   │   │   └── generate_grpc.py      # Handles both hello & user protos
│   │   └── common/                    # Shared utilities
│   │       ├── storage/              # Database abstractions
│   │       ├── utils/                # Environment management
│   │       └── metrics/              # Prometheus metrics
│   └── tests/
│       ├── test_server.py
│       └── BUILD.bazel
├── protos/
│   ├── BUILD.bazel
│   ├── hello.proto                    # Hello Service definition
│   └── user.proto                     # 🆕 User Service definition
├── docker/                            # 🐳 Container definitions
│   ├── Dockerfile.grpc                # Hello Service container
│   ├── Dockerfile.user                # 🆕 User Service container
│   ├── Dockerfile.ui                  # UI Service container
│   └── docker-compose.yml             # Multi-service orchestration
├── .github/
│   └── workflows/
│       └── docker-build.yml           # 🚀 CI/CD for all services
├── MODULE.bazel
├── requirements.in                     # 🔐 Now includes PyJWT, bcrypt
├── requirements_lock.txt
└── README.md
```

---

## What are MODULE.bazel and MODULE.bazel.lock?
- **MODULE.bazel**: This file is the root configuration for Bazel's new dependency management system, called bzlmod. It declares your project's external dependencies (like `rules_python`), configures toolchains, and sets up extensions (such as pip integration for Python). Think of it as the Bazel equivalent of a `pyproject.toml` or `package.json` for your build and dependency setup.
- **MODULE.bazel.lock**: This file is automatically generated by Bazel when you run builds. It locks the exact versions and resolved dependency graph for all modules and extensions declared in `MODULE.bazel`. You should add this file to your `.gitignore` because it is machine-generated and will be recreated as needed.

---

## Why Bazel? Why BUILD.bazel Files?
- **Bazel** provides reproducible, hermetic builds and enforces clear package boundaries.
- Each directory with a `BUILD.bazel` is a Bazel package. This ensures:
  - Code in one package can only depend on other packages via Bazel targets (not direct file paths).
  - Dependencies are explicit and controlled.
- `BUILD.bazel` files define how code is built, what dependencies it has, and what is visible to other packages.

---

## Why `__init__.py` Files?
- Every Python package directory (e.g., `server/`, `server/impl/`, `generated/`) must have an `__init__.py` file.
- This makes the directory a Python package, enabling absolute imports and correct module resolution.
- Without `__init__.py`, Python and Bazel may not recognize the directory as a package, leading to import errors.

---

## Proto Generation and the `genrule` 🔧

### Simplified Unified Approach
We use a **unified proto generation** system that's both simple and powerful:

- **One Tool**: `generate_grpc.py` handles both `hello.proto` and `user.proto`
- **One Target**: All services use `//khushal_hello_grpc/src/generated:generated`
- **Two Genrules**: Separate generation for each proto, unified library target

### Why We Use a `genrule`
- The `genrule` in `generated/BUILD.bazel` runs `grpc_tools.protoc` to generate both proto libraries
- We patch the generated files to use relative imports so they work as packages under Bazel
- This ensures all generated code can be imported as `from khushal_hello_grpc.src.generated import hello_pb2, user_pb2` in your code

#### Example simplified `genrule`:
```python
# Generate User Service protos
genrule(
    name = "generate_user_grpc",
    srcs = ["//protos:user.proto"],
    outs = ["user_pb2.py", "user_pb2_grpc.py"],
    cmd = "$(location :generate_grpc_tool) $(location //protos:user.proto) $(@D)",
    tools = [":generate_grpc_tool"],
)

# Unified library for all generated code
py_library(
    name = "generated",
    srcs = [
        "hello_pb2.py", "hello_pb2_grpc.py",
        "user_pb2.py", "user_pb2_grpc.py", 
        "__init__.py",
    ],
    deps = [requirement("protobuf")],
    visibility = ["//visibility:public"],
)
```

---

## Python Imports: Best Practices
- Always use **absolute imports** in your code, e.g.:
  ```python
  from khushal_hello_grpc.src.generated import hello_pb2, hello_pb2_grpc, user_pb2, user_pb2_grpc
  from khushal_hello_grpc.src.server.impl.service_impl import HelloService
  from khushal_hello_grpc.src.user_service.impl.user_service_impl import UserService
  ```
- Never import generated files as top-level modules (e.g., `import hello_pb2`) unless you explicitly add the directory to `PYTHONPATH` (not recommended with Bazel).
- The patched `genrule` ensures the generated files use relative imports internally, so everything works as a package.

---

## Troubleshooting & Lessons Learned
- **Import errors** (e.g., `ModuleNotFoundError: No module named 'user_pb2'`) are almost always due to:
  - Incorrect import style (top-level vs. package import)
  - Missing `__init__.py` files
  - Not patching the generated code to use relative imports
- **Bazel package boundaries**: Never reference files in subpackages directly; always depend on Bazel targets.
- **Proto package**: If you use a `package` statement in your proto, it affects the output directory structure and imports. For simplicity, omit it unless you want nested packages.
- **Regeneration**: Bazel will automatically regenerate protos when the `.proto` file or `genrule` changes. No manual steps needed.

---

## Usage

### What is a Bazel `genrule`?
A `genrule` is a flexible Bazel build rule that allows you to run arbitrary shell commands as part of your build process. In this project, we use a `genrule` to invoke the gRPC Python code generator (`grpc_tools.protoc`) and patch the generated files for correct imports. This approach is necessary because Bazel does not provide a built-in rule for Python gRPC code generation.

### Build all services:
```sh
# Hello Service
bazel build //khushal_hello_grpc/src/server:hello_server

# User Service 🆕  
bazel build //khushal_hello_grpc/src/user_service:user_service

# UI Service
bazel build //khushal_hello_grpc/src/ui/server:ui_server
```

### Run all services:
```sh
# Hello Service (Terminal 1)
bazel run //khushal_hello_grpc/src/server:hello_server

# User Service (Terminal 2) 🆕
bazel run //khushal_hello_grpc/src/user_service:user_service

# UI Service (Terminal 3)
bazel run //khushal_hello_grpc/src/ui/server:ui_server
```

> **Note:** Every time you build or run the services, Bazel automatically regenerates the proto files. This is enabled by the custom `genrule` in `generated/BUILD.bazel`, which runs the gRPC Python code generator and patches imports as needed. Using a `genrule` for Python gRPC proto generation is the standard and recommended practice with Bazel, since there is no built-in Bazel rule for Python gRPC codegen.

### Add dependencies:
- Edit `requirements.in`, then run `python3 -m piptools compile requirements.in --output-file=requirements_lock.txt --allow-unsafe` to update `requirements_lock.txt`.
- Bazel will pick up changes automatically via bzlmod and `pip_parse`.

---

## Summary
This project demonstrates a robust, multi-service gRPC architecture with Bazel:
- **Three services**: Hello, User Authentication, and Web UI
- **Unified proto generation**: All services share the same generated code
- **Production-ready authentication**: JWT tokens, bcrypt hashing, secure storage
- **Clean architecture**: Proper separation of concerns and dependency injection
- **Containerized deployment**: Docker support for all services
- **Automated CI/CD**: GitHub Actions builds and deploys all services

If you add more protos or services, just follow the same pattern!

## Important Versions Used

- **rules_python:** 0.40.0
- **Python:** 3.11
- **grpcio:** 1.71.0
- **grpcio-tools:** 1.71.0
- **protobuf:** 5.29.4
- **PyJWT:** 2.10.1 🆕
- **bcrypt:** 4.3.0 🆕
- **requests:** 2.32.3
- **pytest:** 8.3.5

See `requirements_lock.txt` for the full list of pinned Python dependencies.

## Containerization & CI/CD

> **Note:** Building the Docker images is a separate, explicit step—typically done in your CI/CD pipeline (or when you want to deploy). Normal Bazel build and test commands (e.g., `bazel build ...`, `bazel test ...`) do NOT build the Docker images unless you explicitly build the image targets.

---

## GitHub Actions CI/CD 🚀

This project uses GitHub Actions for automated Continuous Integration and Continuous Deployment. Every push to the `master` or `main` branch triggers an automated build and deployment pipeline for **all three services**.

### What happens on each push:

1. **Automatic Build**: GitHub Actions automatically builds Docker images for all services:
   - `hello_grpc-grpc` (Hello Service)
   - `hello_grpc-user` (User Service) 🆕
   - `hello_grpc-ui` (UI Service)

2. **Dependency Installation**: All Python dependencies are installed from `requirements_lock.txt` including authentication libraries

3. **Code Generation**: gRPC code is generated from both proto files during the build process

4. **Multi-Service Push**: All built images are pushed to GitHub Container Registry (ghcr.io) with multiple tags:
   - `ghcr.io/khushal1198/hello_grpc-grpc:latest`
   - `ghcr.io/khushal1198/hello_grpc-user:latest` 🆕
   - `ghcr.io/khushal1198/hello_grpc-ui:latest`

5. **Kubernetes Deployment**: Automatically updates Kubernetes manifests for all services

### Workflow Configuration

The CI/CD pipeline is configured in `.github/workflows/docker-build.yml` and includes:

- **Multi-Service Build**: Builds and pushes all three services in parallel
- **Build Matrix**: Supports multiple platforms (linux/amd64, linux/arm64)
- **Caching**: Uses GitHub Actions cache to speed up builds
- **Security**: Uses GitHub secrets for registry authentication
- **Auto-deployment**: Updates Kubernetes manifests in separate repository

### Required GitHub Secrets

The following secrets must be configured in your GitHub repository settings:

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- `MANIFESTS_REPO_TOKEN`: Personal Access Token for updating Kubernetes manifests

### Pulling and Running the Built Images

Once the workflow completes successfully, you can pull and run all services:

```bash
# Pull all images
docker pull ghcr.io/khushal1198/hello_grpc-grpc:latest      # Hello Service
docker pull ghcr.io/khushal1198/hello_grpc-user:latest      # User Service 🆕
docker pull ghcr.io/khushal1198/hello_grpc-ui:latest        # UI Service

# Run all services (for Apple Silicon Macs, specify platform)
docker run --platform linux/amd64 -p 50051:50051 ghcr.io/khushal1198/hello_grpc-grpc:latest
docker run --platform linux/amd64 -p 50052:50052 ghcr.io/khushal1198/hello_grpc-user:latest
docker run --platform linux/amd64 -p 8081:8081 ghcr.io/khushal1198/hello_grpc-ui:latest

# Or use docker-compose for all services
docker-compose -f docker/docker-compose.yml up
```

### Monitoring Builds

- View build status in the "Actions" tab of your GitHub repository
- Each build shows detailed logs for all three services
- Failed builds will show specific error messages for debugging

### Benefits of This Setup

- **Multi-Service Automation**: All services built and deployed together
- **Automated Deployment**: No manual intervention required
- **Reproducible Builds**: Every build uses the same environment and dependencies
- **Version Tracking**: Each commit gets its own tagged images for all services
- **Easy Rollbacks**: Can quickly revert to any previous commit's images
- **Production Ready**: Images are built with production best practices