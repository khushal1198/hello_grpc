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
- **Web UI for testing gRPC calls** (see below)
- **Containerization with Docker** (see below)
- **Automated CI/CD with GitHub Actions** (see below)

---

## Quickstart Commands

### Build the server
```sh
bazel build //khushal_hello_grpc/src/server:hello_server
```

### Run the server
```sh
bazel run //khushal_hello_grpc/src/server:hello_server
```

### Run the UI client
```sh
bazel run //khushal_hello_grpc/src/ui:ui_server
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

## Web UI for Testing gRPC Calls

This project includes a web-based UI that allows you to interact with your gRPC server through a browser. The UI provides:

- **Real-time gRPC calls**: Send `HelloRequest` messages and receive `HelloReply` responses
- **Server health monitoring**: Check if the gRPC server is running and healthy
- **Beautiful interface**: Modern, responsive design with real-time status updates
- **Connection status**: Visual indicator showing connection to the gRPC server

### How to use the UI:

1. **Start the gRPC server** (in one terminal):
   ```sh
   bazel run //khushal_hello_grpc/src/server:hello_server
   ```

2. **Start the UI server** (in another terminal):
   ```sh
   bazel run //khushal_hello_grpc/src/ui:ui_server
   ```

3. **Open your browser** and go to:
   ```
   http://localhost:8080/static/index.html
   ```

4. **Test the gRPC service**:
   - Enter a name in the input field
   - Click "Send Hello Request" to make a gRPC call
   - Click "Check Server Health" to verify server status
   - Watch the real-time response display

### How the UI works:

- **UI Server**: Runs on port 8080, serves static files and acts as a proxy
- **gRPC Client**: Makes actual gRPC calls to your server on port 50051
- **Web Interface**: Modern HTML/CSS/JS frontend with real-time updates
- **Fallback Mode**: If gRPC server is unavailable, shows simulated responses

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

This project includes a `Dockerfile` that:
- Installs all Python dependencies from `requirements_lock.txt` for reproducibility
- Copies your full Python package and proto definitions into the image
- Generates Python gRPC code from your proto at build time (using `grpcio-tools`)
- Patches the generated code for correct relative imports (required for Bazel-style package structure)
- Sets `PYTHONPATH` so your code can use absolute imports
- Runs your gRPC server as the container entrypoint

### Build the Docker image
```sh
docker build -t hello_server:latest .
```

### Run the Docker container
```sh
docker run -p 50051:50051 hello_server:latest
```

You should see:
```
gRPC server running on port 50051...
```

You can now connect a gRPC client to `localhost:50051`.

#### How the Dockerfile works (step-by-step):
1. **Installs dependencies** from `requirements_lock.txt` (including `grpcio-tools` for codegen)
2. **Copies your full Python package** (`khushal_hello_grpc/`) and proto file(s) into the image
3. **Generates Python gRPC code** using `python -m grpc_tools.protoc ...` at build time
4. **Patches the generated `hello_pb2_grpc.py`** to use relative imports (avoids import errors)
5. **Sets `PYTHONPATH`** so your code can use absolute imports
6. **Entrypoint** runs your gRPC server

#### Troubleshooting Docker builds
- If you see `ModuleNotFoundError: No module named 'grpc'`, make sure `requirements_lock.txt` is present and up to date, and that the Dockerfile is not skipping the `pip install` step.
- If you see `ModuleNotFoundError: No module named 'khushal_hello_grpc'`, make sure the full package is copied and `PYTHONPATH` is set.
- If you see `ModuleNotFoundError: No module named 'hello_pb2'`, make sure the proto code is generated and the patch step is present in the Dockerfile.

---

## Project Structure
```
hello_grpc/
├── khushal_hello_grpc/
│   ├── src/
│   │   ├── server/
│   │   │   ├── server.py
│   │   │   └── impl/
│   │   │       └── service_impl.py
│   │   ├── ui/
│   │   │   ├── server.py
│   │   │   └── static/
│   │   │       ├── index.html
│   │   │       ├── style.css
│   │   │       └── client.js
│   │   └── generated/
│   │       └── (generated .py)
│   └── tests/
│       ├── test_server.py
│       └── BUILD.bazel
├── protos/
│   ├── BUILD.bazel
│   └── hello.proto
├── .github/
│   └── workflows/
│       └── build.yml
├── .jenkins/
│   ├── setup-credentials.sh
│   ├── setup-webhook.sh
│   └── README.md
├── MODULE.bazel
├── requirements.in
├── requirements_lock.txt
├── Dockerfile
├── Jenkinsfile
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

## Proto Generation and the `genrule`
### What We Tried First
- We tried using Bazel's `proto_library` and `py_proto_library` rules, but these do not support gRPC Python code generation out-of-the-box.
- We also tried generating protos directly into the `generated/` directory, but ran into import issues due to how the generated code references each other.

### Why We Use a `genrule`
- The `genrule` in `generated/BUILD.bazel` runs `grpc_tools.protoc` to generate both `hello_pb2.py` and `hello_pb2_grpc.py`.
- We patch the generated `hello_pb2_grpc.py` to use a relative import (`from . import hello_pb2 as hello__pb2`) so it works as a package import under Bazel.
- This ensures all generated code can be imported as `from generated import hello_pb2, hello_pb2_grpc` in your code, and avoids import errors.

#### Example `genrule`:
```python
genrule(
    name = "generate_hello_grpc",
    srcs = ["//protos:hello.proto"],
    outs = [
        "hello_pb2.py",
        "hello_pb2_grpc.py",
        "__init__.py",
    ],
    cmd = "touch $(@D)/__init__.py && cp $(location //protos:hello.proto) $(@D)/hello.proto && cd $(@D) && python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. hello.proto && sed -i '' 's/import hello_pb2 as hello__pb2/from . import hello_pb2 as hello__pb2/' hello_pb2_grpc.py",
    tools = [requirement("grpcio-tools")],
)
```

---

## Python Imports: Best Practices
- Always use **absolute imports** in your code, e.g.:
  ```python
  from generated import hello_pb2, hello_pb2_grpc
  from server.impl.service_impl import HelloService
  ```
- Never import generated files as top-level modules (e.g., `import hello_pb2`) unless you explicitly add the directory to `PYTHONPATH` (not recommended with Bazel).
- The patched `genrule` ensures the generated files use relative imports internally, so everything works as a package.

---

## Troubleshooting & Lessons Learned
- **Import errors** (e.g., `ModuleNotFoundError: No module named 'hello_pb2'`) are almost always due to:
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

### Build the server:
```sh
bazel build //server:hello_server
```

### Run the server:
```sh
bazel run //server:hello_server
```

> **Note:** Every time you build or run the server, Bazel automatically regenerates the proto files. This is enabled by the custom `genrule` in `generated/BUILD.bazel`, which runs the gRPC Python code generator and patches imports as needed. Using a `genrule` for Python gRPC proto generation is the standard and recommended practice with Bazel, since there is no built-in Bazel rule for Python gRPC codegen. This ensures that the latest proto definitions are always used at runtime, and you never need to check in or manually update generated code.

### Add dependencies:
- Edit `requirements.in`, then run `python3 -m piptools compile requirements.in --output-file=requirements_lock.txt --allow-unsafe` to update `requirements_lock.txt`.
- Bazel will pick up changes automatically via bzlmod and `pip_parse`.

---

## Summary
This project demonstrates a robust, idiomatic Bazel Python gRPC setup:
- All proto code is generated at build time
- Imports are always correct and robust
- Bazel package boundaries are respected
- The build is reproducible and easy to extend

If you add more protos or services, just follow the same pattern!

> **Note:** Bazel can run pytest-style tests out of the box. You do **not** need to add `requirement("pytest")` to your `py_test` deps—just write your tests using pytest conventions and Bazel's test runner will handle them. If you add `requirement("pytest")` to `deps`, Bazel will try to resolve it as a target, which may fail depending on your pip integration.

## Important Versions Used

- **rules_python:** 0.40.0
- **Python:** 3.11
- **grpcio:** 1.71.0
- **grpcio-tools:** 1.71.0
- **protobuf:** 5.29.4
- **requests:** 2.32.3
- **pytest:** 8.3.5

See `requirements_lock.txt` for the full list of pinned Python dependencies.

## Containerization & CI/CD

> **Note:** Building the Docker image is a separate, explicit step—typically done in your CI/CD pipeline (or when you want to deploy). Normal Bazel build and test commands (e.g., `bazel build ...`, `bazel test ...`) do NOT build the Docker image unless you explicitly build the image target (e.g., `bazel build //khushal_hello_grpc/src/server:hello_server_image`).

---

## GitHub Actions CI/CD

This project uses GitHub Actions for automated Continuous Integration and Continuous Deployment. Every push to the `master` or `main` branch triggers an automated build and deployment pipeline.

### What happens on each push:

1. **Automatic Build**: GitHub Actions automatically builds the Docker image using the `Dockerfile`
2. **Dependency Installation**: All Python dependencies are installed from `requirements_lock.txt`
3. **Code Generation**: gRPC code is generated from proto files during the build process
4. **Image Push**: The built image is pushed to GitHub Container Registry (ghcr.io) with multiple tags:
   - `ghcr.io/khushal1198/hello_grpc:latest`
   - `ghcr.io/khushal1198/hello_grpc:master` (or `main`)
   - `ghcr.io/khushal1198/hello_grpc:master-<commit-hash>`

### Workflow Configuration

The CI/CD pipeline is configured in `.github/workflows/build.yml` and includes:

- **Build Matrix**: Supports multiple platforms (linux/amd64, linux/arm64)
- **Caching**: Uses GitHub Actions cache to speed up builds
- **Security**: Uses GitHub secrets for registry authentication
- **Multi-tagging**: Automatically tags images with latest, branch name, and commit hash

### Required GitHub Secrets

The following secrets must be configured in your GitHub repository settings:

- `CR_PAT`: GitHub Personal Access Token with `write:packages` scope
- `CR_USERNAME`: Your GitHub username

### Pulling and Running the Built Image

Once the workflow completes successfully, you can pull and run the image:

```bash
# Pull the latest image
docker pull ghcr.io/khushal1198/hello_grpc:latest

# Run the container (for Apple Silicon Macs, specify platform)
docker run --platform linux/amd64 -p 50051:50051 ghcr.io/khushal1198/hello_grpc:latest

# For x86_64 systems
docker run -p 50051:50051 ghcr.io/khushal1198/hello_grpc:latest
```

### Monitoring Builds

- View build status in the "Actions" tab of your GitHub repository
- Each build shows detailed logs of the Docker build process
- Failed builds will show specific error messages for debugging

### Benefits of This Setup

- **Automated Deployment**: No manual intervention required for deployments
- **Reproducible Builds**: Every build uses the same environment and dependencies
- **Version Tracking**: Each commit gets its own tagged image
- **Easy Rollbacks**: Can quickly revert to any previous commit's image
- **Production Ready**: Images are built with production best practices