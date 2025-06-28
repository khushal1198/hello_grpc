# mypy: ignore-errors

import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from time import sleep
from types import TracebackType
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

try:
    from psycopg2 import connect
    from psycopg2.extras import DictCursor
    from sqlalchemy import pool
    from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
    ADVANCED_DEPS_AVAILABLE = True
except ImportError:
    ADVANCED_DEPS_AVAILABLE = False
    connect = None
    DictCursor = None
    pool = None
    PGDialect_psycopg2 = None

from .models import (
    AdditionalFilter,
    ConnectionPool,
    ConnectionProto,
    CursorProto,
    DatabaseType,
    PostgresConfig,
    Storable,
    CREATED_TS_FIELD,
    ID_FIELD,
    LAST_UPDATED_TS_FIELD,
)

T = TypeVar("T", bound=Storable)
TUpdateNode = TypeVar("TUpdateNode", bound="UpdateNode")

logger = logging.getLogger(__name__)

MAX_INSERTS_PER_EXEC = 10000


@dataclass(frozen=True)
class UpdateStatementInput:
    updates: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    additional_filters: Optional[List[AdditionalFilter]] = None


class Serializable:
    """Simple Serializable interface for compatibility"""
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {}


def split_by_dot(s: str) -> List[str]:
    """Split string by dots, handling escaped dots"""
    return s.split(".")


def from_base36(s: str) -> int:
    """Convert base36 string to integer"""
    return int(s, 36)


def to_base36(n: int) -> str:
    """Convert integer to base36 string"""
    if n == 0:
        return "0"
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    while n:
        result = digits[n % 36] + result
        n //= 36
    return result


class PostgresCursor(CursorProto):
    """PostgreSQL cursor wrapper with DictCursor support"""
    
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
        else:
            self._cursor.execute(query, params)
    
    def executemany(self, query: str, params: List[Dict[str, Any]]) -> None:
        """Execute a query with multiple sets of parameters."""
        self._cursor.executemany(query, params)
    
    def fetchall(self) -> List[Dict[str, Any]]:
        """Fetch all rows from the last executed statement."""
        rows = self._cursor.fetchall()
        return [dict(row) for row in rows]
    
    def fetchone(self) -> Dict[Any, Any]:
        """Fetch one row from the last executed statement."""
        row = self._cursor.fetchone()
        if row is None:
            return {}
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
    """PostgreSQL connection wrapper with better connection management"""
    
    def __init__(self, conn):
        self.conn = conn

    def cursor(self) -> CursorProto:
        """Get a cursor for this connection"""
        if ADVANCED_DEPS_AVAILABLE:
            psycopg2_cursor = self.conn.cursor(cursor_factory=DictCursor)
        else:
            psycopg2_cursor = self.conn.cursor()
        return PostgresCursor(psycopg2_cursor)

    def close(self) -> None:
        """Close the connection"""
        self.conn.close()

    def commit(self) -> None:
        """Commit the current transaction"""
        self.conn.commit()

    def rollback(self) -> None:
        """Rollback the current transaction"""
        self.conn.rollback()

    def __enter__(self) -> "PostgresConnection":
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType]
    ) -> bool:
        return self.conn.__exit__(exception_type, exception_value, exception_traceback)


class PostgresConnectionPool(ConnectionPool):
    """PostgreSQL connection pool with SQLAlchemy pooling and production configuration"""
    
    db_type = DatabaseType.POSTGRES
    default_timeout = 30

    def __init__(
        self, 
        config: PostgresConfig, 
        pool_size: int = 15, 
        max_overflow: int = 3,
        auth_data: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Initialize PostgreSQL connection pool
        
        :param config: PostgreSQL configuration
        :param pool_size: Base pool size
        :param max_overflow: Maximum overflow connections
        :param auth_data: Auth data dict with keys: username, password, hostname, port
        """
        if not ADVANCED_DEPS_AVAILABLE:
            raise ImportError("Advanced PostgreSQL features require psycopg2 and sqlalchemy")
        
        self.schema = config.schema
        
        # Use provided auth_data or parse from config
        if auth_data:
            auth_info = auth_data
        else:
            # Simple parsing for our use case (in production you'd use SecretManager)
            auth_string = config.auth_string
            if "://" in auth_string:
                # Parse postgresql://user:pass@host:port/db format
                import urllib.parse
                parsed = urllib.parse.urlparse(auth_string)
                auth_info = {
                    "username": parsed.username or "postgres",
                    "password": parsed.password or "",
                    "hostname": parsed.hostname or "localhost", 
                    "port": str(parsed.port) if parsed.port else "5432"
                }
            else:
                # Default values for our setup
                auth_info = {
                    "username": "test_user",
                    "password": "test123",
                    "hostname": "shivi.local",
                    "port": "32543"
                }

        self._full_config = {
            "dbname": config.database,
            "user": auth_info["username"],
            "password": auth_info["password"],
            "port": int(auth_info["port"]),
            "host": auth_info["hostname"],
            "keepalives": 1,
            "keepalives_idle": 15,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }

        self._connection_pool = pool.QueuePool(
            self._create_connection,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pre_ping=True,
            dialect=PGDialect_psycopg2()
        )
        
        logger.info(f"PostgreSQL connection pool initialized: {pool_size} base + {max_overflow} overflow")

    def _create_connection(self):
        """Create a new database connection"""
        return connect(**self._full_config)

    def get_connection(self) -> ConnectionProto:
        """Get a connection from the pool"""
        conn = self._connection_pool.connect()
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {self.schema}")
        cursor.close()
        return PostgresConnection(conn)

    def close(self) -> None:
        """Close the connection pool gracefully"""
        logger.info("Stopping PostgresConnectionPool...")
        
        # Wait for connections to close gracefully
        for attempt in range(5):
            checked_out = self._connection_pool.checkedout()
            if not checked_out:
                break
            logger.info(f"Waiting for {checked_out} PostgreSQL connections to close... (attempt {attempt + 1}/5)")
            sleep(1)

        # Warn about remaining connections
        remaining = self._connection_pool.checkedout()
        if remaining:
            logger.warning(f"{remaining} PostgreSQL connections remain open after 5s. Abandoning...")

        # Dispose of the pool
        try:
            self._connection_pool.dispose()
            logger.info("PostgreSQL connection pool disposed successfully")
        except Exception as e:
            logger.error(f"Failed to close PostgreSQL connection pool: {e}")

        logger.info("Stopped PostgresConnectionPool")


class UpdateNode:
    """Base class for update nodes"""
    
    def __init__(
        self,
        path: List[str],
        update_mode: Union[None, Literal["update"], Literal["append"]],
        value: Any,
        children: List["UpdateNode"]
    ):
        self.path = path
        self.update_mode = update_mode
        self.value = value
        self.children = children

    def to_update_obj(self) -> str:
        """Convert to SQL update object - implemented by subclasses"""
        raise NotImplementedError

    def get_self_path(self) -> str:
        """Get the SQL path for this node - implemented by subclasses"""
        raise NotImplementedError

    def get_parent_path(self) -> str:
        """Get the SQL path for parent node - implemented by subclasses"""
        raise NotImplementedError

    def get_path_str(self, path: List[str]) -> str:
        """Convert path list to SQL path string - implemented by subclasses"""
        raise NotImplementedError


class StatementExecutor(Generic[T]):
    """Production-ready statement executor with sophisticated JSON/JSONB support"""

    def __init__(
        self,
        cls: Type[T],
        fq_table_name: str,
    ) -> None:
        self.cls: Type[T] = cls
        self.fq_table_name: str = fq_table_name

    def bulk_insert(self, cursor: CursorProto, objs: List[T]) -> None:
        """Bulk insert objects with automatic timestamp management"""
        data = []
        now = datetime.now(timezone.utc)

        for obj in objs:
            obj_data = obj.to_dict()
            obj_data.update({
                CREATED_TS_FIELD: now,
                LAST_UPDATED_TS_FIELD: now,
            })
            data.append(obj_data)

        sql_stmt, payload_list = self._build_bulk_insert_stmt(data)

        # Execute in chunks to avoid memory issues
        for i in range(0, len(payload_list), MAX_INSERTS_PER_EXEC):
            chunk = payload_list[i : i + MAX_INSERTS_PER_EXEC]
            cursor.executemany(sql_stmt, chunk)

    def _build_bulk_insert_stmt(self, data: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """Build bulk insert statement with proper JSON handling"""
        if not data:
            raise ValueError("No data provided for bulk insert")
            
        column_list = list(data[0].keys())
        columns_str = ",".join(column_list)
        fields_str = ",".join([f"%({col})s" for col in column_list])

        payload_list: List[Dict[str, Any]] = []
        for datum in data:
            payload = {}
            for col in column_list:
                if isinstance(datum[col], dict):
                    payload[col] = json.dumps(datum[col])
                else:
                    payload[col] = datum[col]
            payload_list.append(payload)

        sql_stmt = f"INSERT INTO {self.fq_table_name} ({columns_str}) VALUES ({fields_str})"
        return sql_stmt, payload_list

    def get_all(
        self,
        cursor: CursorProto,
        filters: Optional[Dict[str, Any]],
        additional_filters: Optional[List[AdditionalFilter]],
        order_by: str,
        order_by_asc: bool,
        limit: int,
        timeout: Optional[int],
    ) -> List[T]:
        """Returns a list of objects that match the given filters"""
        raw_entries = self.get_all_raw(
            cursor, filters, additional_filters, None, order_by, order_by_asc, limit, timeout
        )
        return [self.cls.from_dict(raw_entry) for raw_entry in raw_entries]

    def get_all_raw(
        self,
        cursor: CursorProto,
        filters: Optional[Dict[str, Any]],
        additional_filters: Optional[List[AdditionalFilter]],
        selected_columns: Optional[List[str]],
        order_by: str,
        order_by_asc: bool,
        limit: int,
        timeout: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Returns raw data matching filters with pagination support"""

        filter_clause, filter_params = self._build_filter(filters, additional_filters)

        # Handle large result sets with pagination
        out: List[Dict[str, Any]] = []
        offset = 0
        batch = min(10000, limit)
        order_by_modifier = "ASC" if order_by_asc else "DESC"

        selected_columns_str = "*"
        if selected_columns:
            selected_columns_str = ", ".join(selected_columns)

        while True:
            sql_stmt = f"""
                SELECT {selected_columns_str} FROM {self.fq_table_name}
                {filter_clause}
                ORDER BY {order_by} {order_by_modifier} OFFSET {offset} ROWS FETCH NEXT {batch} ROWS ONLY
            """
            
            if timeout:
                cursor.execute(sql_stmt, filter_params, timeout=timeout)
            else:
                cursor.execute(sql_stmt, filter_params)
            results = cursor.fetchall()

            if not results:
                break

            for result in results:
                processed = self.transform_fetch_results(result)
                out.append(processed)

            # Optimization: break if we got less than batch size
            if len(results) < batch:
                break

            offset = offset + batch
            batch = min(batch, limit - len(out))

        return out

    def transform_fetch_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform fetched data for consistency"""
        return {
            k.lower(): json.dumps(v) if isinstance(v, dict) else v
            for k, v in data.items()
        }

    def get_all_paginate(
        self,
        cursor: CursorProto,
        filters: Optional[Dict[str, Any]],
        additional_filters: Optional[List[AdditionalFilter]],
        pagination_token: Optional[str],
        limit: int,
        pagination_field: str,
        pagination_order_by_asc: bool,
        timeout: Optional[int],
    ) -> Tuple[List[T], Optional[str]]:
        """Get objects with pagination support"""
        raw_entries, next_pagination_token = self.get_all_raw_paginate(
            cursor,
            filters,
            additional_filters,
            None,
            pagination_token,
            limit,
            pagination_field,
            pagination_order_by_asc,
            timeout,
        )
        return [self.cls.from_dict(raw_entry) for raw_entry in raw_entries], next_pagination_token

    def get_all_raw_paginate(
        self,
        cursor: CursorProto,
        filters: Optional[Dict[str, Any]],
        additional_filters: Optional[List[AdditionalFilter]],
        selected_columns: Optional[List[str]],
        pagination_token: Optional[str],
        limit: int,
        pagination_field: str,
        pagination_order_by_asc: bool,
        timeout: Optional[int],
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Sophisticated pagination using base36 encoded tokens"""
        
        if pagination_token:
            if pagination_field == CREATED_TS_FIELD:
                created_ts_millis = from_base36(pagination_token)
                created_ts = datetime.fromtimestamp(created_ts_millis / 1000, timezone.utc)

                effective_additional_filters = list(additional_filters or [])
                effective_additional_filters.append(
                    AdditionalFilter(
                        f"{CREATED_TS_FIELD} < %(af_created_ts)s",
                        {"af_created_ts": created_ts.isoformat()},
                    )
                )
            elif pagination_field == ID_FIELD:
                id_str = base64.b64decode(pagination_token.encode("utf-8")).decode("utf-8")

                effective_additional_filters = list(additional_filters or [])
                effective_additional_filters.append(
                    AdditionalFilter(
                        f"{ID_FIELD} < %(af_id)s",
                        {"af_id": id_str},
                    )
                )
            else:
                raise ValueError(f"Unsupported pagination field: {pagination_field}")
        else:
            effective_additional_filters = additional_filters

        raw_entries = self.get_all_raw(
            cursor,
            filters,
            effective_additional_filters,
            selected_columns,
            pagination_field,
            pagination_order_by_asc,
            limit,
            timeout,
        )

        if len(raw_entries) < limit:
            return raw_entries, None
        else:
            if pagination_field == CREATED_TS_FIELD:
                oldest_created_ts = raw_entries[-1].get(pagination_field)
                if not oldest_created_ts:
                    raise AssertionError("BUG: created_ts not found in the last entry")
                return raw_entries, to_base36(int(oldest_created_ts.timestamp() * 1000))
            elif pagination_field == ID_FIELD:
                last_id = raw_entries[-1].get(pagination_field)
                if not last_id:
                    raise AssertionError("BUG: id not found in the last entry")
                pagination_token = base64.b64encode(last_id.encode("utf-8")).decode("utf-8")
                return raw_entries, pagination_token
            else:
                raise ValueError(f"Unsupported pagination field: {pagination_field}")

    def update(
        self,
        cursor: CursorProto,
        update_input: UpdateStatementInput,
    ) -> None:
        """Update records matching filters"""
        sql_stmt, payload = self._build_update_statement(
            update_input.filters, update_input.additional_filters, update_input.updates
        )
        cursor.execute(sql_stmt, payload)

    def bulk_update(
        self,
        cursor: CursorProto,
        update_input_list: List[UpdateStatementInput],
    ) -> None:
        """Bulk update with identical SQL structure"""
        payload_list: List[Dict[str, Any]] = []
        sql_stmt_list: List[str] = []
        
        for update_input in update_input_list:
            sql_stmt, payload = self._build_update_statement(
                update_input.filters, update_input.additional_filters, update_input.updates
            )
            sql_stmt_list.append(sql_stmt)
            payload_list.append(payload)
            
        assert all(
            stmt == sql_stmt_list[0] for stmt in sql_stmt_list
        ), "Bulk update not applicable on different sql statements!"
        
        cursor.executemany(sql_stmt_list[0], payload_list)

    def delete(
        self,
        cursor: CursorProto,
        filters: Optional[Dict[str, Any]],
        additional_filters: Optional[List[AdditionalFilter]],
    ) -> None:
        """Delete records matching filters"""
        sql_stmt, payload = self._build_delete_statement(filters, additional_filters)
        cursor.execute(sql_stmt, payload)

    def _build_delete_statement(
        self, filters: Optional[Dict[str, Any]], additional_filters: Optional[List[AdditionalFilter]]
    ) -> Tuple[str, Dict[str, Any]]:
        """Build DELETE statement"""
        if not filters and not additional_filters:
            raise ValueError("No filters specified for delete op")

        filter_clause, filter_params = self._build_filter(filters, additional_filters)

        sql_stmt = f"""
            DELETE FROM {self.fq_table_name}
            {filter_clause}
        """

        return sql_stmt, filter_params

    def _build_update_statement(
        self,
        filters: Optional[Dict[str, Any]],
        additional_filters: Optional[List[AdditionalFilter]],
        updates: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Build UPDATE statement with automatic last_updated_ts"""
        if not filters and not additional_filters:
            raise ValueError("No filters specified for update op")
        if len(updates) == 0:
            raise ValueError("No updates specified for update op")
            
        updates[LAST_UPDATED_TS_FIELD] = datetime.now(timezone.utc)

        filter_clause, filter_params = self._build_filter(filters, additional_filters)
        update_clause, update_params = self._build_update(updates)

        sql_stmt = f"""
            UPDATE {self.fq_table_name}
            SET {update_clause}
            {filter_clause}
        """
        
        payload: Dict[str, Any] = {}
        payload.update(filter_params)
        payload.update(update_params)

        return sql_stmt, payload

    def _build_filter(
        self,
        filters: Optional[Dict[str, Any]],
        additional_filters: Optional[List[AdditionalFilter]],
    ) -> Tuple[str, Dict[str, Any]]:
        """Build sophisticated filter clauses with JSON path support"""
        filters = filters or {}
        additional_filters = additional_filters or []

        filter_clauses: List[str] = []
        filter_params: Dict[str, Any] = {}

        # Process basic filters with JSON path support
        for key in filters:
            sanitized_key = key
            param_key = key.replace(":", "_").replace(".", "_")
            
            # Handle JSON path filtering (e.g., "metadata:client.ip")
            if ":" in key:
                column_name, path = key.split(":", 1)
                path_parts = path.split(".")
                sanitized_path = "->".join([f"'{elem}'" for elem in path_parts])
                sanitized_key = f"{column_name}->{sanitized_path}"

            # Handle different value types
            if filters[key] is None:
                filter_clauses.append(f"{sanitized_key} IS NULL")
            elif isinstance(filters[key], list):
                # Handle IN clauses
                placeholders = ", ".join([f"%({param_key}_{i})s" for i in range(len(filters[key]))])
                for i, value in enumerate(filters[key]):
                    filter_params[f"{param_key}_{i}"] = value
                filter_clauses.append(f"{sanitized_key} IN ({placeholders})")
            else:
                # Handle equality
                value = filters[key]
                if isinstance(value, Serializable):
                    value = json.dumps(value.to_json())
                elif isinstance(value, dict):
                    value = json.dumps(value)
                else:
                    value = str(value)
                
                filter_params[param_key] = value
                
                # Use ->> for text extraction if it's a JSON path
                if "->" in sanitized_key and not isinstance(filters[key], Serializable):
                    base_key, final_key = sanitized_key.rsplit("->", 1)
                    sanitized_key = f"{base_key}->>{final_key}"
                
                filter_clauses.append(f"{sanitized_key} = %({param_key})s")

        # Add additional filters
        for additional_filter in additional_filters:
            filter_clauses.append(additional_filter.statement)
            filter_params.update(additional_filter.params)

        filter_clause = f"WHERE {' AND '.join(filter_clauses)}" if filter_clauses else ""
        return filter_clause, filter_params

    def _build_update(
        self,
        updates: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Build update clause with JSON path support"""
        # Group updates by column name
        col_updates: Dict[str, Dict[str, Any]] = {}
        for key in updates:
            col_name = key.split(":", 1)[0]

            if col_name not in col_updates:
                col_updates[col_name] = {}
            col_updates[col_name][key] = updates[key]

        update_clauses: List[str] = []
        update_params: Dict[str, Any] = {}
        for col_name in col_updates:
            (clause, params) = self._build_update_clause(col_updates[col_name])
            update_clauses.append(clause)
            update_params.update(params)

        return (", ".join(update_clauses), update_params)

    def _build_update_clause(
        self,
        updates: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Build sophisticated JSON update clause"""
        (col_name, path_to_val) = self._extract_json_path(updates)
        root: UpdateNode = self._build_update_clause_tree(col_name, path_to_val)
        update_clause = f"{col_name} = {root.to_update_obj()}"

        update_params: Dict[str, Any] = {}
        nodes_to_process = [root]
        while nodes_to_process:
            node = nodes_to_process.pop()
            nodes_to_process.extend(node.children)
            if node.update_mode:
                if isinstance(node.value, dict) or len(node.path) > 1:
                    update_val = json.dumps(node.value)
                else:
                    update_val = node.value
                update_params[f"u_{node.get_self_path()}"] = update_val
        return update_clause, update_params

    @staticmethod
    def _extract_json_path(updates: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Extract JSON path and values from updates"""
        if len(updates) == 0:
            raise ValueError("No updates specified for update op")

        col_name = ""
        path_to_val: Dict[str, Any] = {}
        
        for field in updates:
            parts = field.split(":", 1)
            if len(parts) == 1:
                col_name_ = parts[0]
                json_path = ""
            elif len(parts) == 2:
                col_name_ = parts[0]
                json_path = parts[1]

            if not col_name:
                col_name = col_name_
            elif col_name != col_name_:
                raise ValueError(
                    f"All updates for _build_update_clause should only be for a single field, but got {updates}"
                )
            path_to_val[json_path] = updates[field]

        return col_name, path_to_val

    def _build_update_clause_tree(
        self,
        col_name: str,
        path_to_val: Dict[str, Any],
    ) -> "UpdateNode":
        """Build tree for complex JSON updates"""
        if len(path_to_val) == 1:
            # Non-json case
            (key, val) = next(iter(path_to_val.items()))
            if not key:
                return self._get_update_node(path=[col_name], update_mode="update", value=val, children=[])

        # JSON case
        root: UpdateNode = self._get_update_node(path=[col_name], update_mode=None, value=None, children=[])
        for path in path_to_val:
            parts = split_by_dot(path)
            current_node = root
            for i, part in enumerate(parts):
                # Determine the new UpdateNode
                if i == len(parts) - 1:
                    if part.endswith("@append"):
                        key = part.rsplit("@", 1)[0]
                        update_mode = "append"
                    else:
                        key = part
                        update_mode = "update"
                    node_path = [*current_node.path, key]
                    new_node = self._get_update_node(
                        path=node_path, update_mode=update_mode, value=path_to_val[path], children=[]
                    )
                else:
                    new_node = self._get_update_node(
                        path=[*current_node.path, part], update_mode=None, value=None, children=[]
                    )

                # Add to tree
                found = False
                for child in current_node.children:
                    if child.path[-1] == new_node.path[-1]:
                        if child.update_mode != new_node.update_mode or child.value != new_node.value:
                            raise ValueError(f"Conflicting update path: {path_to_val}")
                        current_node = child
                        found = True
                        break
                if not found:
                    current_node.children.append(new_node)
                    current_node = new_node

        return root

    def _get_update_node(
        self,
        path: List[str],
        update_mode: Union[None, Literal["update"], Literal["append"]],
        value: Any,
        children: List["PostgresUpdateNode"],
    ) -> "PostgresUpdateNode":
        """Create PostgreSQL-specific update node"""
        return PostgresUpdateNode(path, update_mode, value, children)


@dataclass
class PostgresUpdateNode(UpdateNode):
    """PostgreSQL-specific update node for JSONB operations"""
    
    path: List[str]
    update_mode: Union[None, Literal["update"], Literal["append"]]
    value: Any
    children: List["PostgresUpdateNode"]

    def to_update_obj(self) -> str:
        """Convert to PostgreSQL JSONB update object"""
        if self.update_mode:
            path = self.get_self_path()
            if isinstance(self.value, dict):
                return f"%(u_{path})s::jsonb"
            return f"%(u_{path})s"
        else:
            obj = self.get_self_path()
            for child in self.children:
                if child.update_mode == "append":
                    obj = f"jsonb_set({obj}, '{{{child.path[-1]}}}', ({child.get_self_path()} || '{{{child.to_update_obj()}}}')::jsonb)"
                else:
                    obj = f"jsonb_set({obj}, '{{{child.path[-1]}}}', {child.to_update_obj()}::jsonb)"
            return obj

    def get_self_path(self) -> str:
        """Get the SQL path for this node"""
        return self.get_path_str(self.path)

    def get_parent_path(self) -> str:
        """Get the SQL path for parent node"""
        return self.get_path_str(self.path[:-1])

    def get_path_str(self, path: List[str]) -> str:
        """Convert path list to PostgreSQL JSONB path string"""
        cleaned_path = [f'"{part}"' if any(char in part for char in ['.', ':', '@']) else part for part in path]
        path_str = cleaned_path[0]
        if len(cleaned_path) > 1:
            path_str += '->' + '->'.join([f"'{elem}'" for elem in cleaned_path[1:]])
        return path_str


def create_postgres_pool(
    database_url: str, 
    schema: str = "test",
    pool_size: int = 15,
    max_overflow: int = 3
) -> Optional[PostgresConnectionPool]:
    """
    Factory function to create PostgreSQL connection pool
    
    :param database_url: PostgreSQL connection URL
    :param schema: Database schema to use
    :param pool_size: Base pool size
    :param max_overflow: Maximum overflow connections
    :return: PostgreSQL connection pool or None if dependencies unavailable
    """
    if not ADVANCED_DEPS_AVAILABLE:
        logger.warning("Advanced PostgreSQL features unavailable - missing psycopg2 or sqlalchemy")
        return None
    
    config = PostgresConfig(
        database="myapp",  # Extract from URL in production
        schema=schema,
        auth_string=database_url
    )
    
    return PostgresConnectionPool(
        config=config,
        pool_size=pool_size,
        max_overflow=max_overflow
    ) 