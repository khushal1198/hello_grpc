import hashlib
import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

from .models import ConnectionPool

logger = logging.getLogger(__name__)


class DistributedLockManager(ABC):
    """Abstract base class for distributed lock managers"""
    
    @abstractmethod
    def acquire(self, lock_name: str) -> None:
        """Acquire a lock (blocking)"""
        pass
    
    @abstractmethod
    def acquire_non_blocking(self, lock_name: str) -> bool:
        """Try to acquire a lock without blocking. Returns True if acquired."""
        pass
    
    @abstractmethod
    def release(self, lock_name: str) -> None:
        """Release a lock"""
        pass
    
    @abstractmethod
    def heartbeat(self) -> None:
        """Send heartbeat to keep connection alive"""
        pass
    
    def start_heartbeat_daemon(self) -> None:
        """Start heartbeat daemon (optional)"""
        pass
    
    def stop_heartbeat_daemon(self) -> None:
        """Stop heartbeat daemon (optional)"""
        pass


class PostgresLockManagerHeartbeatWorker:
    """Background worker to send periodic heartbeats for lock manager"""
    
    def __init__(self, lock_manager: "PostgresLockManager", heartbeat_interval: int = 30):
        self.lock_manager = lock_manager
        self.heartbeat_interval = heartbeat_interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the heartbeat worker thread"""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            logger.info("Heartbeat worker started")
    
    def stop(self):
        """Stop the heartbeat worker thread"""
        self._stop_event.set()
    
    def join(self, timeout: Optional[float] = None):
        """Wait for the heartbeat worker thread to finish"""
        if self._thread:
            self._thread.join(timeout)
    
    def _run(self):
        """Main heartbeat worker loop"""
        while not self._stop_event.is_set():
            try:
                self.lock_manager.heartbeat_no_time_check()
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
            
            # Wait for the interval or until stop is requested
            self._stop_event.wait(self.heartbeat_interval)


class PostgresLockManager(DistributedLockManager):
    """PostgreSQL-based distributed lock manager using advisory locks"""
    
    def __init__(self, connection_pool: ConnectionPool, heartbeat_daemon: bool = False):
        """
        Initialize the PostgresLockManager with a connection pool.

        :param connection_pool: A connection pool instance to manage DB connections.
        :param heartbeat_daemon: Whether to start a background heartbeat daemon.
        """
        self._connection_pool = connection_pool
        self._connection = None
        self._acquired_lock_keys = set()
        self._thread_lock = threading.Lock()
        self._last_heartbeat_ts = datetime.fromtimestamp(0, timezone.utc)

        if heartbeat_daemon:
            self._heartbeat_daemon = PostgresLockManagerHeartbeatWorker(self, heartbeat_interval=30)
        else:
            self._heartbeat_daemon = None

    def _string_to_lock_key(self, lock_name: str) -> int:
        """
        Convert a string lock name into a 64-bit signed integer for PostgreSQL advisory locks.
        """
        hash_value = hashlib.md5(lock_name.encode("utf-8")).hexdigest()
        lock_key_unsigned = int(hash_value[:16], 16)

        if lock_key_unsigned >= 2**63:
            return lock_key_unsigned - 2**64
        return lock_key_unsigned

    def _get_connection(self) -> Optional[object]:
        """Return a valid DB connection, reusing or creating as needed."""
        if self._connection is None:
            self._connection = self._connection_pool.get_connection()
        return self._connection

    def _get_connection_for_lock(self, lock_key: int):
        """Track lock and return connection."""
        with self._thread_lock:
            self._acquired_lock_keys.add(lock_key)
            return self._get_connection()

    def _release_connection_for_lock(self, lock_key: int):
        """Untrack lock; optionally close connection if none left."""
        with self._thread_lock:
            self._acquired_lock_keys.discard(lock_key)
            if not self._acquired_lock_keys and self._connection:
                self._connection.close()
                self._connection = None

    def acquire(self, lock_name: str) -> None:
        """
        Acquire an advisory lock (blocking until the lock is acquired).

        :param lock_name: The name of the lock to acquire.
        """
        lock_key = self._string_to_lock_key(lock_name)
        connection = self._get_connection_for_lock(lock_key)

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT pg_advisory_lock({lock_key}::bigint);")
            logger.info(f"Lock '{lock_name}' acquired")

    def acquire_non_blocking(self, lock_name: str) -> bool:
        """
        Try to acquire an advisory lock without blocking.
        Returns True if the lock was acquired, or False if already held.

        :param lock_name: The name of the lock to try to acquire.
        :return: True if successfully acquired, False if already held.
        """
        lock_key = self._string_to_lock_key(lock_name)
        attempt = 1

        while True:
            connection = self._get_connection_for_lock(lock_key)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT pg_try_advisory_lock({lock_key}::bigint);")
                    result = cursor.fetchone()
                    lock_acquired = result.get("pg_try_advisory_lock", False) if result else False

                    if lock_acquired:
                        logger.info(f"Lock '{lock_name}' acquired")
                    else:
                        logger.info(f"Lock '{lock_name}' is already held")
                        self._release_connection_for_lock(lock_key)

                    return lock_acquired

            except Exception as e:
                if "connection already closed" in str(e):
                    if attempt == 1:
                        logger.warning("Connection was closed; re-initializing and retrying once.")
                        attempt += 1
                        self._release_connection_for_lock(lock_key)
                        continue
                    else:
                        logger.error("Connection was closed; retry exhausted.")
                        raise e
                raise e

    def release(self, lock_name: str) -> None:
        """
        Release an advisory lock.

        :param lock_name: The name of the lock to release.
        """
        lock_key = self._string_to_lock_key(lock_name)
        connection = self._get_connection_for_lock(lock_key)

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT pg_advisory_unlock({lock_key}::bigint);")
            logger.info(f"Lock '{lock_name}' released")

        self._release_connection_for_lock(lock_key)

    def heartbeat_no_time_check(self):
        """Send heartbeat without time checking (used by daemon)"""
        with self._thread_lock:
            if not (self._acquired_lock_keys and self._connection):
                return
            logger.debug("Detected alive postgres connection with valid locks, sending heartbeat")
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT 1;")

    def heartbeat(self) -> None:
        """
        Send a dummy query ('SELECT 1') to keep the connection alive if at least one lock is held.
        Rate-limited to avoid excessive heartbeats.
        """
        if self._heartbeat_daemon:
            return

        with self._thread_lock:
            now = datetime.now(timezone.utc)
            if now - self._last_heartbeat_ts < timedelta(seconds=30):
                return
            self._last_heartbeat_ts = now

            if self._acquired_lock_keys and self._connection:
                logger.debug("Detected alive postgres connection with valid locks, sending heartbeat")
                with self._connection.cursor() as cursor:
                    cursor.execute("SELECT 1;")

    def start_heartbeat_daemon(self):
        """Start the background heartbeat daemon"""
        if self._heartbeat_daemon:
            self._heartbeat_daemon.start()

    def stop_heartbeat_daemon(self):
        """Stop the background heartbeat daemon"""
        if self._heartbeat_daemon:
            self._heartbeat_daemon.stop()
            self._heartbeat_daemon.join()


class InMemoryLockManager(DistributedLockManager):
    """
    In-memory lock manager for testing.
    Note: this is not thread-safe and is just meant to be used for local testing.
    """
    def __init__(self) -> None:
        self.locks = set()
        self._lock = threading.Lock()

    def acquire(self, lock_name: str) -> None:
        """Acquire a lock (blocking)"""
        while True:
            with self._lock:
                if lock_name not in self.locks:
                    self.locks.add(lock_name)
                    logger.info(f"In-memory lock '{lock_name}' acquired")
                    return
            time.sleep(0.01)  # Small delay instead of busy waiting

    def acquire_non_blocking(self, lock_name: str) -> bool:
        """Try to acquire a lock without blocking"""
        with self._lock:
            if lock_name in self.locks:
                logger.info(f"In-memory lock '{lock_name}' is already held")
                return False
            self.locks.add(lock_name)
            logger.info(f"In-memory lock '{lock_name}' acquired")
            return True

    def release(self, lock_name: str) -> None:
        """Release a lock"""
        with self._lock:
            self.locks.discard(lock_name)
            logger.info(f"In-memory lock '{lock_name}' released")

    def heartbeat(self) -> None:
        """No-op for in-memory implementation"""
        pass


def create_lock_manager(connection_pool: Optional[ConnectionPool], heartbeat_daemon: bool = False) -> DistributedLockManager:
    """
    Factory function to create appropriate lock manager based on connection pool availability.
    
    :param connection_pool: Database connection pool, or None for in-memory
    :param heartbeat_daemon: Whether to start background heartbeat daemon (PostgreSQL only)
    :return: Appropriate lock manager instance
    """
    if not connection_pool:
        logger.info("Creating in-memory lock manager")
        return InMemoryLockManager()
    
    logger.info("Creating PostgreSQL distributed lock manager")
    return PostgresLockManager(connection_pool, heartbeat_daemon=heartbeat_daemon) 