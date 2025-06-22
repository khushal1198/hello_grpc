# React Frontend for gRPC Hello Service

This directory contains a React frontend that can be used as an alternative to the static HTML frontend.

## Setup

1. **Install dependencies:**
   ```bash
   cd khushal_hello_grpc/src/ui/frontend/react
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

## Features

- Modern React components
- TypeScript support (optional)
- Hot reloading during development
- Production build optimization
- Proxy configuration to connect to the gRPC UI server

## Integration with Bazel

To integrate this React app with Bazel, you can:

1. Build the React app: `npm run build`
2. Copy the build output to the static directory
3. Serve it through the existing UI server

## Development Workflow

1. Start the gRPC server: `bazel run //khushal_hello_grpc/src/server:hello_server`
2. Start the UI server: `bazel run //khushal_hello_grpc/src/ui:ui_server`
3. Start React dev server: `npm start`
4. Access React app at: http://localhost:3000
5. Access static app at: http://localhost:8080/static/index.html 