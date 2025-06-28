from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import TracebackType
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

T = TypeVar("T", bound="Storable")

# Standard field names for storable objects
ID_FIELD = "id"
CREATED_TS_FIELD = "created_ts"
LAST_UPDATED_TS_FIELD = "last_updated_ts"


class DatabaseType(Enum):
    SNOWHOUSE = "snowhouse"
    IN_MEMORY = "in_memory"
    POSTGRES = "postgres"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PostgresConfig:
    database: str
    schema: str
    auth_string: str  # Simplified - removed SecretKey dependency


@dataclass(frozen=True)
class _SnowhouseAuthConfig:
    user: str
    password: Optional[str]  # Simplified - removed SecretKey dependency


@dataclass(frozen=True)
class SnowhouseConfig:
    schema: str
    auth: Optional[_SnowhouseAuthConfig] = None  # If None, will use local user to auth


@dataclass(frozen=True)
class _LegacySnowhouseAuthConfig:
    user: str
    password: str  # Simplified - removed SecretKey dependency


@dataclass(frozen=True)
class LegacySnowhouseConfig:
    schema: str
    auth: _LegacySnowhouseAuthConfig


@dataclass(frozen=True)
class DatabaseConfig:
    type: DatabaseType
    snowhouse: Optional[SnowhouseConfig] = None  # Only used if provider is "snowhouse"
    legacy_snowhouse: Optional[LegacySnowhouseConfig] = None  # For the legacy database
    postgres: Optional[PostgresConfig] = None  # Only used if provider is "postgres"


# Signals that a class can be stored into a database
# Includes methods for serializing and deserializing the class instance for storage
@dataclass(frozen=True)
class Storable(Generic[T], ABC):
    id: str  # Storable should always have a primary key called id
    created_ts: datetime
    last_updated_ts: datetime

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        pass


class StorageFilter:
    pass


@dataclass(frozen=True)
class AdditionalFilter:
    statement: str
    params: Dict[str, Any]


class CursorProto(ABC):
    @abstractmethod
    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Execute a query with optional parameters.
        """
        pass

    @abstractmethod
    def executemany(self, query: str, params: List[Dict[str, Any]]) -> None:
        """
        Execute a query with multiple sets of parameters.
        """
        pass

    @abstractmethod
    def fetchall(self) -> List[Dict[str, Any]]:
        """
        Fetch all rows from the last executed statement.
        """
        pass

    @abstractmethod
    def fetchone(self) -> Dict[Any, Any]:
        """
        Fetch one row from the last executed statement.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Closes the cursor.
        """
        pass

    @abstractmethod
    def __enter__(self) -> "CursorProto":
        pass

    @abstractmethod
    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> bool:
        pass


class ConnectionProto(ABC):
    @abstractmethod
    def cursor(self) -> CursorProto:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def __enter__(self) -> "ConnectionProto":
        pass

    @abstractmethod
    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        exception_traceback: Optional[TracebackType],
    ) -> bool:
        pass


class ConnectionPool(ABC):
    db_type: DatabaseType
    default_timeout: Optional[int]
    schema: str

    @abstractmethod
    def get_connection(self) -> ConnectionProto:
        pass

    @abstractmethod
    def close(self) -> None:
        pass 