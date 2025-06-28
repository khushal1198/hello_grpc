import logging
import random
import time
import uuid
from datetime import datetime
from types import TracebackType
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
import psycopg2
import psycopg2.extras
from .models import (
    ConnectionPool, ConnectionProto, CursorProto, 
    DatabaseType, Storable, AdditionalFilter
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Storable)

DEFAULT_LIMIT = 1000


def retry(max_attempts: int = 3, sleep_times: List[float] = None):
    """Decorator for retrying database operations"""
    if sleep_times is None:
        sleep_times = [1.0, 2.0, 3.0]
    
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    attempts += 1
                    return func(self, *args, **kwargs)
                except Exception as e:
                    if attempts >= max_attempts:
                        logger.exception(f"Failed after {max_attempts} attempts")
                        raise
                    sleep_time = random.choice(sleep_times)
                    logger.warning(f"Attempt {attempts} failed, retrying in {sleep_time}s: {e}")
                    time.sleep(sleep_time)
        return wrapper
    return decorator


class PostgresCursor(CursorProto):
    """PostgreSQL cursor wrapper implementing CursorProto"""
    
    def __init__(self, psycopg2_cursor):
        self._cursor = psycopg2_cursor
    
    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """Execute a query with optional parameters."""
        if params is None:
            self._cursor.execute(query)
        elif isinstance(params, (list, tuple)):
            self._cursor.execute(query, params)
        else:
            # Convert dict params to list format for psycopg2
            self._cursor.execute(query, params)
    
    def executemany(self, query: str, params: List[Dict[str, Any]]) -> None:
        """Execute a query with multiple sets of parameters."""
        self._cursor.executemany(query, params)
    
    def fetchall(self) -> List[Dict[str, Any]]:
        """Fetch all rows from the last executed statement."""
        rows = self._cursor.fetchall()
        if isinstance(rows[0] if rows else None, dict):
            return rows
        # Convert psycopg2.extras.RealDictRow to dict if needed
        return [dict(row) for row in rows]
    
    def fetchone(self) -> Dict[Any, Any]:
        """Fetch one row from the last executed statement."""
        row = self._cursor.fetchone()
        if row is None:
            return {}
        if isinstance(row, dict):
            return row
        # Convert psycopg2.extras.RealDictRow to dict if needed
        return dict(row)
    
    def close(self) -> None:
        """Closes the cursor."""
        self._cursor.close()
    
    def __enter__(self) -> "PostgresCursor":
        return self
    
    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> bool:
        self.close()
        return False


class PostgresConnection(ConnectionProto):
    """PostgreSQL connection wrapper implementing ConnectionProto"""
    
    def __init__(self, psycopg2_connection):
        self._connection = psycopg2_connection
    
    def cursor(self) -> CursorProto:
        """Get a cursor for this connection"""
        psycopg2_cursor = self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return PostgresCursor(psycopg2_cursor)
    
    def close(self) -> None:
        """Close the connection"""
        self._connection.close()
    
    def commit(self) -> None:
        """Commit the current transaction"""
        self._connection.commit()
    
    def rollback(self) -> None:
        """Rollback the current transaction"""
        self._connection.rollback()
    
    def __enter__(self) -> "PostgresConnection":
        return self
    
    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> bool:
        self.close()
        return False


class PostgresConnectionPool(ConnectionPool):
    """PostgreSQL connection pool implementation"""
    
    def __init__(self, database_url: str, schema: str = "test", default_timeout: int = 30):
        self.db_type = DatabaseType.POSTGRES
        self.default_timeout = default_timeout
        self.schema = schema
        self._database_url = database_url
    
    def get_connection(self) -> ConnectionProto:
        """Get a database connection"""
        psycopg2_conn = psycopg2.connect(
            self._database_url,
            options=f"-c search_path={self.schema},public"
        )
        return PostgresConnection(psycopg2_conn)
    
    def close(self) -> None:
        """Close the connection pool (no-op for simple implementation)"""
        pass


class DatabaseStore(Generic[T]):
    """Generic database storage layer for any Storable type"""
    
    def __init__(self, cls: Type[T], table_name: str, connection_pool: ConnectionPool):
        self._cls = cls
        self._table_name = table_name
        self._schema = connection_pool.schema
        self._fq_table_name = f"{self._schema}.{self._table_name}"
        self._connection_pool = connection_pool
    
    def _generate_id(self) -> str:
        """Generate a unique ID for new records"""
        return str(uuid.uuid4())
    
    @retry()
    def insert(self, obj: T) -> Optional[str]:
        """Insert a single object and return its ID"""
        conn = self._connection_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                data = obj.to_dict()
                
                # Generate ID and timestamps if not provided
                if not data.get('id'):
                    data['id'] = self._generate_id()
                
                now = datetime.now()
                if not data.get('created_ts'):
                    data['created_ts'] = now
                if not data.get('last_updated_ts'):
                    data['last_updated_ts'] = now
                
                columns = list(data.keys())
                values = list(data.values())
                placeholders = ["%s"] * len(values)
                
                query = f"""
                    INSERT INTO {self._fq_table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    RETURNING id;
                """
                
                cursor.execute(query, values)
                result = cursor.fetchone()
                conn.commit()
                
                record_id = result.get("id") if result else None
                logger.info(f"Inserted {self._cls.__name__} with ID {record_id}")
                return record_id
        except Exception:
            conn.rollback()
            logger.exception(f"Failed to insert {self._cls.__name__}: {obj}")
            raise
        finally:
            conn.close()
    
    @retry()
    def bulk_insert(self, objs: List[T]) -> None:
        """Insert multiple objects in a single transaction"""
        if not objs:
            return
            
        conn = self._connection_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                # Prepare all objects with IDs and timestamps
                all_data = []
                columns = None
                now = datetime.now()
                
                for obj in objs:
                    obj_data = obj.to_dict()
                    
                    # Generate ID and timestamps if not provided
                    if not obj_data.get('id'):
                        obj_data['id'] = self._generate_id()
                    if not obj_data.get('created_ts'):
                        obj_data['created_ts'] = now
                    if not obj_data.get('last_updated_ts'):
                        obj_data['last_updated_ts'] = now
                    
                    if columns is None:
                        columns = list(obj_data.keys())
                    
                    all_data.append([obj_data[col] for col in columns])
                
                placeholders = ["%s"] * len(columns)
                query = f"""
                    INSERT INTO {self._fq_table_name} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)});
                """
                
                cursor.executemany(query, all_data)
                conn.commit()
                
                logger.info(f"Bulk inserted {len(objs)} {self._cls.__name__} objects")
        except Exception:
            conn.rollback()
            logger.exception(f"Failed to bulk insert {len(objs)} {self._cls.__name__} objects")
            raise
        finally:
            conn.close()
    
    @retry()
    def get(self, filters: Optional[Dict[str, Any]] = None) -> Optional[T]:
        """Get a single object matching the filters"""
        results = self.get_all(filters=filters, limit=2)
        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            raise ValueError(f"Multiple records found for filters {filters}")
    
    @retry()
    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        additional_filters: Optional[List[AdditionalFilter]] = None,
        order_by: str = "id",
        order_by_asc: bool = True,
        limit: Optional[int] = None
    ) -> List[T]:
        """Get all objects matching the filters"""
        conn = self._connection_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                query = f"SELECT * FROM {self._fq_table_name}"
                params = []
                
                # Add WHERE clauses
                where_clauses = []
                
                # Basic filters
                if filters:
                    for key, value in filters.items():
                        if value is not None:
                            where_clauses.append(f"{key} = %s")
                            params.append(value)
                
                # Additional filters
                if additional_filters:
                    for additional_filter in additional_filters:
                        where_clauses.append(additional_filter.statement)
                        params.extend(additional_filter.params.values())
                
                if where_clauses:
                    query += f" WHERE {' AND '.join(where_clauses)}"
                
                # Add ORDER BY
                order_direction = "ASC" if order_by_asc else "DESC"
                query += f" ORDER BY {order_by} {order_direction}"
                
                # Add LIMIT
                if limit:
                    query += f" LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert rows to objects
                results = [self._cls.from_dict(row) for row in rows]
                logger.debug(f"Retrieved {len(results)} {self._cls.__name__} objects")
                return results
        except Exception:
            logger.exception(f"Failed to get_all {self._cls.__name__} with filters {filters}")
            raise
        finally:
            conn.close()
    
    @retry()
    def get_all_raw(
        self,
        filters: Optional[Dict[str, Any]] = None,
        additional_filters: Optional[List[AdditionalFilter]] = None,
        selected_columns: Optional[List[str]] = None,
        order_by: str = "id",
        order_by_asc: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get raw dictionary results without converting to objects"""
        conn = self._connection_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                # Build SELECT clause
                columns = ", ".join(selected_columns) if selected_columns else "*"
                query = f"SELECT {columns} FROM {self._fq_table_name}"
                params = []
                
                # Add WHERE clauses
                where_clauses = []
                
                # Basic filters
                if filters:
                    for key, value in filters.items():
                        if value is not None:
                            where_clauses.append(f"{key} = %s")
                            params.append(value)
                
                # Additional filters
                if additional_filters:
                    for additional_filter in additional_filters:
                        where_clauses.append(additional_filter.statement)
                        params.extend(additional_filter.params.values())
                
                if where_clauses:
                    query += f" WHERE {' AND '.join(where_clauses)}"
                
                # Add ORDER BY
                order_direction = "ASC" if order_by_asc else "DESC"
                query += f" ORDER BY {order_by} {order_direction}"
                
                # Add LIMIT
                if limit:
                    query += f" LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                logger.debug(f"Retrieved {len(rows)} raw rows from {self._fq_table_name}")
                return rows
        except Exception:
            logger.exception(f"Failed to get_all_raw from {self._fq_table_name} with filters {filters}")
            raise
        finally:
            conn.close()
    
    @retry()
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count objects matching the filters"""
        conn = self._connection_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                query = f"SELECT COUNT(*) FROM {self._fq_table_name}"
                params = []
                
                # Add WHERE clause if filters provided
                if filters:
                    where_clauses = []
                    for key, value in filters.items():
                        if value is not None:
                            where_clauses.append(f"{key} = %s")
                            params.append(value)
                    
                    if where_clauses:
                        query += f" WHERE {' AND '.join(where_clauses)}"
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                count = result.get("count", 0) if result else 0
                
                logger.debug(f"Counted {count} {self._cls.__name__} objects")
                return count
        except Exception:
            logger.exception(f"Failed to count {self._cls.__name__} with filters {filters}")
            raise
        finally:
            conn.close()
    
    @retry()
    def delete(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Delete objects matching the filters. Returns number of deleted rows."""
        if not filters:
            raise ValueError("Delete requires filters to prevent accidental full table deletion")
            
        conn = self._connection_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                where_clauses = []
                params = []
                
                for key, value in filters.items():
                    if value is not None:
                        where_clauses.append(f"{key} = %s")
                        params.append(value)
                
                if not where_clauses:
                    raise ValueError("No valid filters provided for delete")
                
                query = f"DELETE FROM {self._fq_table_name} WHERE {' AND '.join(where_clauses)}"
                cursor.execute(query, params)
                deleted_count = cursor._cursor.rowcount  # Access underlying psycopg2 cursor
                conn.commit()
                
                logger.info(f"Deleted {deleted_count} {self._cls.__name__} objects")
                return deleted_count
        except Exception:
            conn.rollback()
            logger.exception(f"Failed to delete {self._cls.__name__} with filters {filters}")
            raise
        finally:
            conn.close()
    
    @retry()
    def raw_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results"""
        conn = self._connection_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or [])
                
                # Check if query returns results
                try:
                    rows = cursor.fetchall()
                    logger.debug(f"Executed raw query, got {len(rows)} rows")
                    return rows
                except Exception:
                    # Query didn't return results (like INSERT/UPDATE/DELETE)
                    logger.debug("Executed raw query (no results returned)")
                    return []
        except Exception:
            logger.exception(f"Failed to execute raw query: {query}")
            raise
        finally:
            conn.close() 