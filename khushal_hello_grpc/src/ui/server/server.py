#!/usr/bin/env python3
"""
gRPC UI Server
This server provides a web interface for interacting with the gRPC Hello service.
It serves static files and acts as a proxy between the web client and gRPC server.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from aiohttp import web, ClientSession
import aiohttp_cors
import grpc
from concurrent import futures

# Add the generated directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'generated'))

from khushal_hello_grpc.src.generated import hello_pb2
from khushal_hello_grpc.src.generated import hello_pb2_grpc
from khushal_hello_grpc.src.common.logging_config import setup_root_logging, log_request

# Import UI service configuration
from khushal_hello_grpc.src.ui.config import get_config

# Configure root logging so logging.info(), logging.debug(), etc. can be used directly
setup_root_logging(level=logging.DEBUG)

# Get configuration
config = get_config()

# Configuration - can be enhanced with config system later
GRPC_SERVER_HOST = os.getenv("GRPC_SERVER_HOST", "localhost")
GRPC_SERVER_PORT = int(os.getenv("GRPC_SERVER_PORT", "50051"))
UI_SERVER_PORT = int(os.getenv("UI_SERVER_PORT", "8081"))

# Database is available via: config.database.url
logging.info(f"UI Server config loaded - Database available at: {config.database.host}:{config.database.port}")

class GrpcClient:
    """gRPC client for communicating with the Hello service"""
    
    def __init__(self):
        self.channel = None
        self.stub = None
        self.connected = False
    
    async def connect(self):
        """Connect to the gRPC server - non-blocking"""
        try:
            # Create gRPC channel with timeout
            self.channel = grpc.aio.insecure_channel(f"{GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}")
            self.stub = hello_pb2_grpc.HelloServiceStub(self.channel)
            
            # Test connection with timeout
            try:
                await asyncio.wait_for(self.health_check(), timeout=5.0)
                self.connected = True
                logging.info(f"Connected to gRPC server at {GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}")
                return True
            except asyncio.TimeoutError:
                logging.warning(f"gRPC server connection timeout at {GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}")
                self.connected = False
                return False
            except Exception as e:
                logging.warning(f"gRPC server not available at {GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}: {e}")
                self.connected = False
                return False
            
        except Exception as e:
            logging.warning(f"Failed to initialize gRPC client: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the gRPC server"""
        if self.channel:
            await self.channel.close()
        self.connected = False
    
    async def say_hello(self, name: str) -> str:
        """Send a hello request to the gRPC server"""
        if not self.connected:
            raise Exception("gRPC client not connected")
        
        try:
            request = hello_pb2.HelloRequest(name=name)
            response = await self.stub.SayHello(request)
            return response.message
        except Exception as e:
            logging.error(f"gRPC call failed: {e}")
            self.connected = False  # Mark as disconnected on failure
            raise e
    
    async def health_check(self) -> bool:
        """Check if the gRPC server is healthy"""
        if not self.connected:
            return False
            
        try:
            # Simple ping to check if server is reachable
            request = hello_pb2.HelloRequest(name="health_check")
            await self.stub.SayHello(request)
            return True
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            self.connected = False
            return False

class UIServer:
    """Web server for the gRPC UI client"""
    
    def __init__(self):
        self.grpc_client = GrpcClient()
        self.app = None
    
    def find_static_files(self):
        """Find static files directory with multiple fallback strategies"""
        possible_paths = [
            # Bazel runfiles path
            ("bazel_runfiles", lambda: self._get_bazel_runfiles_path()),
            # Container path (when running in Docker/K8s)
            ("container", lambda: "/app/static"),
            # Development path
            ("dev", lambda: os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static')),
            # Alternative development path
            ("dev_alt", lambda: os.path.join(os.path.dirname(__file__), '..', '..', 'ui', 'frontend', 'static')),
        ]
        
        for name, path_func in possible_paths:
            try:
                path = path_func()
                if path and os.path.exists(path):
                    logging.info(f"Found static files at {name} path: {path}")
                    return path
            except Exception as e:
                logging.debug(f"Failed to find static files at {name} path: {e}")
        
        # If no path found, create a minimal fallback
        logging.warning("No static files found, creating minimal fallback")
        return self._create_fallback_static_files()
    
    def _get_bazel_runfiles_path(self):
        """Get Bazel runfiles path"""
        try:
            from bazel_tools.tools.python.runfiles import runfiles
            r = runfiles.Create()
            static_runfile_path = r.Rlocation("_main/khushal_hello_grpc/src/ui/frontend/static")
            if static_runfile_path and os.path.exists(static_runfile_path):
                return static_runfile_path
        except (ImportError, FileNotFoundError):
            pass
        return None
    
    def _create_fallback_static_files(self):
        """Create minimal fallback static files if none exist"""
        fallback_dir = "/tmp/fallback_static"
        os.makedirs(fallback_dir, exist_ok=True)
        
        # Create minimal index.html
        index_html = """<!DOCTYPE html>
<html>
<head>
    <title>gRPC Hello Service - Fallback</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .error { background-color: #ffebee; color: #c62828; }
        .success { background-color: #e8f5e8; color: #2e7d32; }
    </style>
</head>
<body>
    <div class="container">
        <h1>gRPC Hello Service</h1>
        <div class="status error">
            <strong>Static files not found</strong><br>
            This is a fallback page. The UI server is running but static files are missing.
        </div>
        <h2>API Endpoints</h2>
        <ul>
            <li><strong>Health Check:</strong> <a href="/api/health">/api/health</a></li>
            <li><strong>Hello API:</strong> POST /api/hello (with JSON body: {"name": "Your Name"})</li>
        </ul>
    </div>
</body>
</html>"""
        
        with open(os.path.join(fallback_dir, "index.html"), "w") as f:
            f.write(index_html)
        
        logging.info(f"Created fallback static files at {fallback_dir}")
        return fallback_dir
    
    async def start(self):
        """Start the UI server"""
        self.app = web.Application()
        
        # Setup CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Try to connect to gRPC server (non-blocking)
        asyncio.create_task(self.grpc_client.connect())
        
        # Add routes
        self.app.router.add_post('/api/hello', self.handle_hello_request)
        self.app.router.add_get('/api/health', self.handle_health_check)
        
        # Find static files directory
        frontend_path = self.find_static_files()
        
        # Add custom static file handler with logging
        async def static_handler(request):
            path = request.match_info['path']
            full_path = os.path.join(frontend_path, path)
            
            # Log the request using common logging
            log_request(logging, request.method, f"/static/{path}", 
                       user_agent=request.headers.get('User-Agent', 'Unknown'))
            
            logging.debug(f"Static file lookup: {path} -> {full_path}")
            
            if os.path.exists(full_path) and os.path.isfile(full_path):
                logging.info(f"Serving static file: {full_path}")
                return web.FileResponse(full_path)
            else:
                logging.error(f"Static file not found: {full_path}")
                # Log directory contents for debugging
                parent_dir = os.path.dirname(full_path)
                if os.path.exists(parent_dir):
                    logging.debug(f"Directory contents of {parent_dir}: {os.listdir(parent_dir)}")
                return web.Response(text="File not found", status=404)
        
        # Add static route with custom handler
        self.app.router.add_get('/static/{path:.*}', static_handler)
        
        # Also add the standard static route as backup
        self.app.router.add_static('/static', path=frontend_path, name='static')
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
        
        # Cleanup on shutdown
        async def cleanup(app):
            await self.grpc_client.disconnect()
        
        self.app.on_cleanup.append(cleanup)
        
        return self.app
    
    async def handle_hello_request(self, request):
        """Handle HelloService.SayHello requests"""
        try:
            # Log the request
            log_request(logging, request.method, "/api/hello", 
                       content_type=request.headers.get('Content-Type', 'Unknown'))
            
            # Get the request body
            data = await request.json()
            name = data.get('name', 'World')
            
            logging.debug(f"Processing hello request for name: {name}")
            
            # Try to make actual gRPC call
            try:
                if self.grpc_client.connected:
                    message = await self.grpc_client.say_hello(name)
                    response_data = {"message": message}
                    logging.info(f"Handled hello request for name: {name} via gRPC")
                else:
                    # Try to reconnect
                    await self.grpc_client.connect()
                    if self.grpc_client.connected:
                        message = await self.grpc_client.say_hello(name)
                        response_data = {"message": message}
                        logging.info(f"Handled hello request for name: {name} via gRPC (reconnected)")
                    else:
                        raise Exception("gRPC server not available")
            except Exception as e:
                # Fallback to simulation if gRPC fails
                response_data = {
                    "message": f"Hello, {name}! (Simulated response - gRPC server unavailable: {str(e)})"
                }
                logging.warning(f"gRPC call failed, using simulation: {e}")
            
            return web.json_response(response_data)
            
        except Exception as e:
            logging.error(f"Error handling hello request: {e}")
            return web.json_response(
                {"error": f"Failed to process request: {str(e)}"}, 
                status=500
            )
    
    async def handle_health_check(self, request):
        """Handle health check requests"""
        try:
            # Log the request
            log_request(logging, request.method, "/api/health")
            
            # Check gRPC server health
            is_healthy = self.grpc_client.connected and await self.grpc_client.health_check()
            
            if is_healthy:
                response_data = {
                    "status": "SERVING",
                    "message": "gRPC server is healthy and responding"
                }
            else:
                response_data = {
                    "status": "NOT_SERVING",
                    "message": "gRPC server is not responding"
                }
            
            logging.info(f"Health check result: {response_data['status']}")
            
            return web.json_response(response_data)
            
        except Exception as e:
            logging.error(f"Error handling health check: {e}")
            return web.json_response(
                {"error": f"Health check failed: {str(e)}"}, 
                status=500
            )

async def main():
    """Main function to start the UI server"""
    # Create and start UI server
    ui_server = UIServer()
    app = await ui_server.start()
    
    print(f"🚀 Starting gRPC UI Server on port {UI_SERVER_PORT}")
    print(f"📡 Connecting to gRPC server at {GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}")
    print(f"🌐 Web UI will be available at http://localhost:{UI_SERVER_PORT}/static/index.html")
    print("Press Ctrl+C to stop the server")
    
    return app

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Simple approach that works with Bazel
    try:
        app = asyncio.run(main())
        web.run_app(app, port=UI_SERVER_PORT, host='0.0.0.0')
    except RuntimeError as e:
        if "event loop" in str(e):
            # Create a new event loop if one is already running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                app = loop.run_until_complete(main())
                web.run_app(app, port=UI_SERVER_PORT, host='0.0.0.0')
            finally:
                loop.close()
        else:
            raise 