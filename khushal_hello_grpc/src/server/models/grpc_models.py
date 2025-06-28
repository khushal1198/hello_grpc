"""
gRPC service-specific data models.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Type

from khushal_hello_grpc.src.common.storage.models import Storable


@dataclass(frozen=True)
class GrpcRequest(Storable["GrpcRequest"]):
    """Model for storing gRPC request/response pairs with full metadata"""
    
    # Application-specific fields
    request_name: str = ""
    response_message: str = ""
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            # Required Storable fields
            "id": self.id,
            "created_ts": self.created_ts,
            "last_updated_ts": self.last_updated_ts,
            # Application fields
            "request_name": self.request_name,
            "response_message": self.response_message,
            "metadata": json.dumps(self.metadata) if self.metadata else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GrpcRequest":
        """Create from database row dictionary"""
        return cls(
            # Required Storable fields
            id=data.get("id", ""),
            created_ts=data.get("created_ts", datetime.now()),
            last_updated_ts=data.get("last_updated_ts", datetime.now()),
            # Application fields
            request_name=data.get("request_name", ""),
            response_message=data.get("response_message", ""),
            metadata=json.loads(data.get("metadata", "{}")) if data.get("metadata") else {}
        )
    
    def __str__(self) -> str:
        return f"GrpcRequest(id={self.id}, name='{self.request_name}', created_ts={self.created_ts})" 