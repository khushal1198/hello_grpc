"""
gRPC request storage: Abstract interface and PostgreSQL implementation.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from khushal_hello_grpc.src.common.storage import DatabaseStore, ConnectionPool
from khushal_hello_grpc.src.server.models import GrpcRequest


class GrpcStore(ABC):
    """Abstract interface for storing and retrieving gRPC requests"""
    
    @abstractmethod
    def store_request(
        self,
        request_name: str,
        response_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store a gRPC request with metadata.
        
        :param request_name: Name from the gRPC request
        :param response_message: Response message that was sent
        :param metadata: Additional metadata to store
        :return: ID of the stored request, or None if storage failed
        """
        pass
    
    @abstractmethod
    def get_recent_requests(self, limit: int = 10) -> List[GrpcRequest]:
        """
        Get the most recent gRPC requests.
        
        :param limit: Maximum number of requests to return
        :return: List of recent requests, ordered by creation time (newest first)
        """
        pass
    
    @abstractmethod
    def get_requests_by_name(self, name: str) -> List[GrpcRequest]:
        """
        Get all requests for a specific name.
        
        :param name: Request name to filter by
        :return: List of requests with the given name
        """
        pass
    
    @abstractmethod
    def get_requests_by_metadata(self, metadata_filter: Dict[str, Any]) -> List[GrpcRequest]:
        """
        Get requests by metadata filtering using JSON path queries.
        
        :param metadata_filter: Dictionary of metadata key-value pairs to filter by
        :return: List of requests matching the metadata filter
        """
        pass
    
    @abstractmethod
    def get_request_count(self) -> int:
        """
        Get total count of stored requests.
        
        :return: Total number of requests in storage
        """
        pass
    
    @abstractmethod
    def get_request_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about stored requests.
        
        :return: Dictionary containing statistics like total count, common names, etc.
        """
        pass
    
    @abstractmethod
    def cleanup_old_requests(self, keep_count: int = 1000) -> int:
        """
        Keep only the most recent N requests, delete older ones.
        
        :param keep_count: Number of recent requests to keep
        :return: Number of requests deleted
        """
        pass


class PostgresGrpcStorage(GrpcStore):
    """PostgreSQL implementation of gRPC request storage using DatabaseStore"""
    
    def __init__(self, connection_pool: ConnectionPool, table_name: str = "grpc_requests"):
        """
        Initialize PostgreSQL gRPC storage.
        
        :param connection_pool: Database connection pool
        :param table_name: Name of the table to store requests in
        """
        self._store = DatabaseStore(GrpcRequest, table_name, connection_pool)
        self._table_name = table_name
    
    def store_request(
        self,
        request_name: str,
        response_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Store a gRPC request with metadata"""
        now = datetime.now(timezone.utc)
        request = GrpcRequest(
            id=str(uuid.uuid4()),
            created_ts=now,
            last_updated_ts=now,
            request_name=request_name,
            response_message=response_message,
            metadata=metadata or {}
        )
        return self._store.insert(request)
    
    def get_recent_requests(self, limit: int = 10) -> List[GrpcRequest]:
        """Get the most recent gRPC requests"""
        return self._store.get_all(
            order_by="created_ts",
            order_by_asc=False,
            limit=limit
        )
    
    def get_requests_by_name(self, name: str) -> List[GrpcRequest]:
        """Get all requests for a specific name"""
        return self._store.get_all(filters={"request_name": name})
    
    def get_requests_by_metadata(self, metadata_filter: Dict[str, Any]) -> List[GrpcRequest]:
        """Get requests by metadata filtering using JSON path queries"""
        filters = {}
        for key, value in metadata_filter.items():
            # Use JSON path filtering: metadata:key -> value
            filters[f"metadata:{key}"] = value
        
        return self._store.get_all(filters=filters)
    
    def get_request_count(self) -> int:
        """Get total count of stored requests"""
        return self._store.count()
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get summary statistics about stored requests"""
        # Get recent stats
        recent_raw = self._store.get_all_raw(
            selected_columns=["request_name", "created_ts", "metadata"],
            order_by="created_ts",
            order_by_asc=False,
            limit=100
        )
        
        # Count by name and extract metadata stats
        name_counts = {}
        service_counts = {}
        
        for row in recent_raw:
            name = row.get("request_name", "")
            name_counts[name] = name_counts.get(name, 0) + 1
            
            # Parse metadata for service stats
            if row.get("metadata"):
                try:
                    import json
                    metadata = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]
                    service = metadata.get("service", "unknown")
                    service_counts[service] = service_counts.get(service, 0) + 1
                except Exception:
                    pass
        
        total_count = self._store.count()
        
        return {
            "total_requests": total_count,
            "recent_name_counts": name_counts,
            "service_counts": service_counts,
            "most_common_name": max(name_counts.items(), key=lambda x: x[1])[0] if name_counts else None,
            "most_common_service": max(service_counts.items(), key=lambda x: x[1])[0] if service_counts else None
        }
    
    def cleanup_old_requests(self, keep_count: int = 1000) -> int:
        """Keep only the most recent N requests, delete older ones"""
        # Get IDs of old requests to delete
        old_requests = self._store.get_all_raw(
            selected_columns=["id"],
            order_by="created_ts",
            order_by_asc=False,
            limit=None  # Get all
        )
        
        if len(old_requests) <= keep_count:
            return 0  # Nothing to delete
        
        # Get IDs of requests to delete (everything beyond keep_count)
        ids_to_delete = [req["id"] for req in old_requests[keep_count:]]
        
        # Delete in batches to avoid huge WHERE IN clauses
        deleted_count = 0
        batch_size = 100
        
        for i in range(0, len(ids_to_delete), batch_size):
            batch_ids = ids_to_delete[i:i + batch_size]
            # Use raw query for efficient batch deletion
            query = f"DELETE FROM {self._store._connection_pool.schema}.{self._table_name} WHERE id = ANY(%s)"
            self._store.raw_query(query, [batch_ids])
            deleted_count += len(batch_ids)
        
        return deleted_count


# Factory function for creating gRPC request store
def create_grpc_request_store(connection_pool: ConnectionPool) -> GrpcStore:
    """
    Create a gRPC request store from a connection pool.
    
    :param connection_pool: Database connection pool to use
    :return: GrpcStore implementation
    """
    return PostgresGrpcStorage(connection_pool, table_name="grpc_requests") 