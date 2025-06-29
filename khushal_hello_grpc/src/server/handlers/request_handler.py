"""
Request handler for processing gRPC requests with logging and business logic.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from khushal_hello_grpc.src.server.storage import GrpcStore
from khushal_hello_grpc.src.common.metrics import track_metrics, track_database_operation

logger = logging.getLogger(__name__)


class RequestHandler:
    """Handler for processing gRPC requests with comprehensive logging and storage"""
    
    def __init__(self, grpc_store: GrpcStore):
        """
        Initialize the request handler.
        
        :param grpc_store: Storage instance for persisting requests
        """
        self.grpc_store = grpc_store
        logger.info("RequestHandler initialized with storage backend and Prometheus metrics")
    
    @track_metrics("SayHello")
    def handle_say_hello(self, request, context) -> str:
        """
        Handle SayHello gRPC requests with full logging and storage.
        Clean and simple - metrics are handled by the decorator.
        
        :param request: gRPC HelloRequest
        :param context: gRPC context with metadata
        :return: Response message string
        """
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        
        # Extract request details
        name = request.name
        peer_info = self._extract_peer_info(context)
        metadata_info = self._extract_metadata(context)
        
        # Log incoming request
        logger.info(f"Processing gRPC request [{request_id}] for name='{name}' from peer={peer_info}")
        logger.debug(f"Request [{request_id}] metadata: {metadata_info}")
        
        # Validate request
        validation_result = self._validate_request(name)
        if not validation_result["valid"]:
            logger.warning(f"Request [{request_id}] validation failed: {validation_result['error']}")
            return f"Error: {validation_result['error']}"
        
        # Process business logic
        response_message = self._generate_response(name)
        logger.debug(f"Request [{request_id}] generated response: '{response_message}'")
        
        # Store the request asynchronously (don't block response)
        self._store_request_async(request_id, name, response_message, peer_info, metadata_info)
        
        logger.info(f"Request [{request_id}] completed successfully")
        return response_message
    
    @track_database_operation("insert", "grpc_requests")
    def _store_request_async(self, request_id: str, name: str, response_message: str, 
                           peer_info: str, metadata_info: Dict[str, Any]):
        """Store request data - metrics tracked by decorator"""
        try:
            storage_metadata = self._build_storage_metadata(
                request_id, name, response_message, peer_info, metadata_info
            )
            
            record_id = self.grpc_store.store_request(
                request_name=name,
                response_message=response_message,
                metadata=storage_metadata
            )
            
            if record_id:
                logger.info(f"Request [{request_id}] stored in database with ID: {record_id}")
                return record_id
            else:
                logger.warning(f"Request [{request_id}] failed to store in database")
                return None
                
        except Exception as e:
            logger.error(f"Request [{request_id}] database error: {e}")
            # Continue processing - don't fail the request due to storage issues
            raise
    
    def _extract_peer_info(self, context) -> str:
        """Extract peer information from gRPC context"""
        try:
            if hasattr(context, 'peer'):
                return context.peer()
            return "unknown"
        except Exception:
            return "unknown"
    
    def _extract_metadata(self, context) -> Dict[str, Any]:
        """Extract metadata from gRPC context"""
        metadata_dict = {}
        try:
            if hasattr(context, 'invocation_metadata'):
                metadata_dict = dict(context.invocation_metadata())
        except Exception as e:
            logger.debug(f"Could not parse invocation metadata: {e}")
        
        return {
            "user_agent": metadata_dict.get("user-agent", "unknown"),
            "content_type": metadata_dict.get("content-type", "unknown"),
            "full_metadata": metadata_dict
        }
    
    def _validate_request(self, name: str) -> Dict[str, Any]:
        """Validate the incoming request"""
        if not name:
            return {"valid": False, "error": "Name cannot be empty"}
        
        if len(name) > 100:
            return {"valid": False, "error": "Name too long (max 100 characters)"}
        
        if name.strip() != name:
            return {"valid": False, "error": "Name cannot have leading/trailing whitespace"}
        
        # Check for potentially harmful content
        forbidden_chars = ['<', '>', '&', '"', "'"]
        if any(char in name for char in forbidden_chars):
            return {"valid": False, "error": "Name contains forbidden characters"}
        
        return {"valid": True}
    
    def _generate_response(self, name: str) -> str:
        """Generate the response message (business logic)"""
        # This is where business logic would go
        # For now, simple greeting, but could be more complex
        return f"Hello, {name}!"
    
    def _build_storage_metadata(
        self, 
        request_id: str,
        name: str, 
        response: str, 
        peer_info: str, 
        metadata_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comprehensive metadata for storage"""
        return {
            "request_id": request_id,
            "service": "HelloService",
            "method": "SayHello",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_info": {
                "peer": peer_info,
                "user_agent": metadata_info.get("user_agent", "unknown"),
                "metadata": metadata_info.get("full_metadata", {})
            },
            "request_details": {
                "name_length": len(name),
                "response_length": len(response),
                "processing_time_ms": None  # Could add timing later
            },
            "system_info": {
                "handler_version": "1.0",
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}"
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        try:
            stats = self.grpc_store.get_request_stats()
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)} 