# Docker Setup

This directory contains Docker configurations for the gRPC Hello World project.

## Services

### 1. gRPC Server (`Dockerfile.grpc`)
- **Port**: 50051
- **Purpose**: gRPC backend service
- **Image**: `ghcr.io/khushal1198/hello_grpc-grpc`

### 2. UI Server (`Dockerfile.ui`)
- **Port**: 8081
- **Purpose**: Web UI frontend with gRPC proxy
- **Image**: `ghcr.io/khushal1198/hello_grpc-ui`

## Local Development

### Using Docker Compose
```bash
# Start both services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Services
```bash
# Build gRPC server
docker build -f docker/Dockerfile.grpc -t hello-grpc-server .

# Build UI server
docker build -f docker/Dockerfile.ui -t hello-grpc-ui .

# Run gRPC server
docker run -p 50051:50051 hello-grpc-server

# Run UI server
docker run -p 8081:8081 -e GRPC_SERVER_HOST=host.docker.internal hello-grpc-ui
```

## CI/CD

The GitHub Actions workflow automatically:
1. Builds both Docker images
2. Pushes to GitHub Container Registry
3. Updates Kubernetes manifests with new image tags

## Access Points

- **gRPC Server**: `localhost:50051`
- **Web UI**: `http://localhost:8081/static/index.html`
- **Health Check**: `http://localhost:8081/api/health` 