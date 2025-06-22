# gRPC UI Client

This directory contains the web-based UI for interacting with the gRPC Hello service. The UI is structured to support both static HTML and modern React frontends.

## Structure

```
ui/
├── server/                 # Backend server (Python/aiohttp)
│   ├── server.py          # Main server implementation
│   └── __init__.py
├── frontend/              # Frontend assets
│   ├── static/            # Static HTML frontend
│   │   └── index.html     # Main HTML file
│   ├── assets/            # Static assets
│   │   ├── css/           # Stylesheets
│   │   │   └── style.css  # Main CSS file
│   │   ├── js/            # JavaScript files
│   │   │   └── client.js  # Main client logic
│   │   └── images/        # Image assets
│   └── react/             # React frontend (optional)
│       ├── package.json   # React dependencies
│       └── README.md      # React setup instructions
└── BUILD.bazel           # Bazel build configuration
```

## Features

### Static Frontend
- **Simple HTML/CSS/JS**: Lightweight, no build step required
- **Real-time gRPC calls**: Send requests and receive responses
- **Health monitoring**: Check server status
- **Connection status**: Visual indicator of gRPC server connection
- **Responsive design**: Works on desktop and mobile

### React Frontend (Optional)
- **Modern React components**: TypeScript support available
- **Hot reloading**: Fast development experience
- **Production builds**: Optimized for deployment
- **Proxy configuration**: Seamless integration with backend

## Usage

### Quick Start (Static Frontend)

1. **Start the gRPC server:**
   ```bash
   bazel run //khushal_hello_grpc/src/server:hello_server
   ```

2. **Start the UI server:**
   ```bash
   bazel run //khushal_hello_grpc/src/ui:ui_server
   ```

3. **Access the UI:**
   ```
   http://localhost:8080/static/index.html
   ```

### React Frontend (Optional)

1. **Setup React:**
   ```bash
   cd khushal_hello_grpc/src/ui/frontend/react
   npm install
   ```

2. **Start React dev server:**
   ```bash
   npm start
   ```

3. **Access React app:**
   ```
   http://localhost:3000
   ```

## Architecture

### Backend (server/)
- **aiohttp web server**: Serves static files and API endpoints
- **gRPC client**: Communicates with the Hello service
- **CORS support**: Enables cross-origin requests
- **Health checking**: Monitors gRPC server status
- **Error handling**: Graceful fallbacks and error reporting

### Frontend (frontend/)
- **Static assets**: HTML, CSS, JS served directly
- **API integration**: RESTful endpoints for gRPC communication
- **Real-time updates**: Connection status and response display
- **Responsive design**: Modern UI with animations

## API Endpoints

- `GET /api/health` - Check gRPC server health
- `POST /api/hello` - Send HelloRequest to gRPC server
- `GET /static/*` - Serve static frontend files

## Development

### Adding New Features

1. **Backend changes**: Modify `server/server.py`
2. **Frontend changes**: Edit files in `frontend/`
3. **React changes**: Work in `frontend/react/`

### Building

The UI is built and served through Bazel:
```bash
bazel build //khushal_hello_grpc/src/ui:ui_server
bazel run //khushal_hello_grpc/src/ui:ui_server
```

### Testing

Test the UI by:
1. Starting both servers
2. Opening the web interface
3. Sending test requests
4. Checking health status

## Configuration

- **UI Server Port**: 8080 (configurable in `server.py`)
- **gRPC Server**: localhost:50051 (configurable in `server.py`)
- **CORS**: Enabled for all origins (configurable in `server.py`)

## Troubleshooting

### Common Issues

1. **"Cannot run the event loop"**: Bazel environment issue - fixed with proper event loop handling
2. **"gRPC server not responding"**: Make sure the gRPC server is running on port 50051
3. **"CORS errors"**: CORS is configured for all origins, should work in most cases

### Debug Mode

Enable debug logging by modifying the logging level in `server.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **TypeScript support**: Add TypeScript to React frontend
- **WebSocket support**: Real-time bidirectional communication
- **Authentication**: Add user authentication and authorization
- **Multiple services**: Support for additional gRPC services
- **Docker integration**: Containerized UI deployment 