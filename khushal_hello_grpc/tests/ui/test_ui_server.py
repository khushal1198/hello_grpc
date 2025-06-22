#!/usr/bin/env python3
"""
Tests for the UI server functionality
"""

import asyncio
import json
import pytest
from aiohttp import web, ClientSession
from aiohttp.test_utils import TestClient, TestServer
import grpc
import threading
import time

# Import the UI server components
from khushal_hello_grpc.src.ui.server.server import UIServer, GrpcClient
from khushal_hello_grpc.src.generated import hello_pb2, hello_pb2_grpc


class TestGrpcClient:
    """Test the gRPC client functionality"""
    
    @pytest.mark.asyncio
    async def test_grpc_client_connection_failure(self):
        """Test gRPC client handles connection failure gracefully"""
        client = GrpcClient()
        # Try to connect to non-existent server
        connected = await client.connect()
        assert not connected
    
    @pytest.mark.asyncio
    async def test_grpc_client_disconnect(self):
        """Test gRPC client disconnect"""
        client = GrpcClient()
        # Should not raise exception even if not connected
        await client.disconnect()


class TestUIServer:
    """Test the UI server functionality"""
    
    @pytest.mark.asyncio
    async def test_ui_server_startup(self):
        """Test UI server can start up"""
        server = UIServer()
        app = await server.start()
        assert app is not None
        await server.grpc_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_hello_request_simulation(self):
        """Test hello request when gRPC server is unavailable"""
        server = UIServer()
        app = await server.start()
        
        # Create test client
        client = TestClient(app)
        
        # Test hello endpoint
        data = {"name": "Test User"}
        async with client.post('/api/hello', json=data) as response:
            assert response.status == 200
            result = await response.json()
            assert "message" in result
            assert "Test User" in result["message"]
            assert "Simulated response" in result["message"]
        
        await server.grpc_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test health check endpoint"""
        server = UIServer()
        app = await server.start()
        
        # Create test client
        client = TestClient(app)
        
        # Test health endpoint
        async with client.get('/api/health') as response:
            assert response.status == 200
            result = await response.json()
            assert "status" in result
            assert result["status"] in ["SERVING", "NOT_SERVING"]
        
        await server.grpc_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_static_file_serving(self):
        """Test static file serving"""
        server = UIServer()
        app = await server.start()
        
        # Create test client
        client = TestClient(app)
        
        # Test static file endpoint (should return 404 if file doesn't exist)
        async with client.get('/static/nonexistent.html') as response:
            # Should return 404 for non-existent files
            assert response.status == 404
        
        await server.grpc_client.disconnect()


class TestIntegration:
    """Integration tests with both gRPC and UI servers"""
    
    def test_full_integration(self):
        """Full integration test with both servers"""
        # This would require starting both servers
        # For now, we'll test the components separately
        pass


# Mock tests for when gRPC server is available
class TestWithGrpcServer:
    """Tests that require a running gRPC server"""
    
    @pytest.mark.skip(reason="Requires running gRPC server")
    @pytest.mark.asyncio
    async def test_hello_request_with_grpc(self):
        """Test hello request when gRPC server is available"""
        # This test would require a running gRPC server
        # It's marked as skip for now but can be enabled in CI/CD
        pass 