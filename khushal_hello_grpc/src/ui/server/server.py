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

# Configure root logging so logging.info(), logging.debug(), etc. can be used directly
setup_root_logging(level=logging.DEBUG)

# Configuration
GRPC_SERVER_HOST = "localhost"
GRPC_SERVER_PORT = 50051
UI_SERVER_PORT = 8081

class GrpcClient:
    """gRPC client for communicating with the Hello service"""
    
    def __init__(self):
        self.channel = None
        self.stub = None
    
    async def connect(self):
        """Connect to the gRPC server"""
        try:
            # Create gRPC channel
            self.channel = grpc.aio.insecure_channel(f"{GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}")
            self.stub = hello_pb2_grpc.HelloServiceStub(self.channel)
            
            # Test connection
            await self.health_check()
            logging.info(f"Connected to gRPC server at {GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to gRPC server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the gRPC server"""
        if self.channel:
            await self.channel.close()
    
    async def say_hello(self, name: str) -> str:
        """Send a hello request to the gRPC server"""
        try:
            request = hello_pb2.HelloRequest(name=name)
            response = await self.stub.SayHello(request)
            return response.message
        except Exception as e:
            logging.error(f"gRPC call failed: {e}")
            raise e
    
    async def health_check(self) -> bool:
        """Check if the gRPC server is healthy"""
        try:
            # Simple ping to check if server is reachable
            request = hello_pb2.HelloRequest(name="health_check")
            await self.stub.SayHello(request)
            return True
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return False

class UIServer:
    """Web server for the gRPC UI client"""
    
    def __init__(self):
        self.grpc_client = GrpcClient()
        self.app = None
    
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
        
        # Connect to gRPC server
        connected = await self.grpc_client.connect()
        if not connected:
            logging.warning("Failed to connect to gRPC server. UI will work in simulation mode.")
        
        # Add routes
        self.app.router.add_post('/api/hello', self.handle_hello_request)
        self.app.router.add_get('/api/health', self.handle_health_check)
        
        # Use Bazel runfiles to resolve the static directory
        try:
            # Try to import runfiles from bazel_tools
            from bazel_tools.tools.python.runfiles import runfiles
            r = runfiles.Create()
            # Use the correct runfiles path
            static_runfile_path = r.Rlocation("_main/khushal_hello_grpc/src/ui/frontend/static")
            if static_runfile_path and os.path.exists(static_runfile_path):
                frontend_path = static_runfile_path
                print(f"[DEBUG] (runfiles) Serving static files from: {frontend_path}")
            else:
                raise FileNotFoundError("Runfiles path not found")
        except (ImportError, FileNotFoundError) as e:
            # Fallback for non-Bazel environments or if runfiles fails
            frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static')
            print(f"[DEBUG] (fallback) Serving static files from: {os.path.abspath(frontend_path)}")
            print(f"[DEBUG] Fallback reason: {e}")
        
        # Verify the path exists
        if not os.path.exists(frontend_path):
            print(f"[ERROR] Static path does not exist: {frontend_path}")
            # Try to list the parent directory to debug
            parent_dir = os.path.dirname(frontend_path)
            if os.path.exists(parent_dir):
                print(f"[DEBUG] Parent directory contents: {os.listdir(parent_dir)}")
        else:
            print(f"[DEBUG] Static path exists and contains: {os.listdir(frontend_path)}")
        
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
                message = await self.grpc_client.say_hello(name)
                response_data = {"message": message}
                logging.info(f"Handled hello request for name: {name} via gRPC")
            except Exception as e:
                # Fallback to simulation if gRPC fails
                response_data = {
                    "message": f"Hello, {name}! (Simulated response - gRPC server unavailable)"
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
            is_healthy = await self.grpc_client.health_check()
            
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