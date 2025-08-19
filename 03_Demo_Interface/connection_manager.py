# 05_Database_Layer/connection_manager.py

import asyncio
import asyncpg
import os
import logging
from typing import Optional, Dict, Any

# Enterprise logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PostgreSQLConnectionManager:
    """
    Manages asynchronous PostgreSQL database connections using asyncpg.
    Implements a connection pool for efficient and robust database access
    in a production-grade Adaptive Mind Framework.
    """

    _instance = None
    _pool: Optional[asyncpg.Pool] = None
    _lock = asyncio.Lock()  # Ensure thread-safe singleton initialization

    def __new__(cls):
        """Implements the Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """
        Initializes the connection pool. This method should be called once at application startup.
        Ensures the pool is created only if it doesn't already exist.
        """
        async with self._lock:
            if self._pool is None:
                try:
                    # Retrieve database credentials from environment variables
                    self.db_user = os.getenv('POSTGRES_USER', 'postgres')
                    self.db_password = os.getenv('POSTGRES_PASSWORD', 'password')
                    self.db_name = os.getenv('POSTGRES_DB', 'adaptive_mind_demo')
                    self.db_host = os.getenv('POSTGRES_HOST', 'localhost')
                    self.db_port = os.getenv('POSTGRES_PORT', '5432')

                    # Set up connection parameters
                    conn_params = {
                        'user': self.db_user,
                        'password': self.db_password,
                        'database': self.db_name,
                        'host': self.db_host,
                        'port': self.db_port,
                        # Enable SSL/TLS if running against a secure endpoint (e.g., Azure PostgreSQL)
                        # 'ssl': 'require' # Uncomment if SSL is needed, or load a client certificate
                    }

                    # Add connection pool parameters
                    pool_params = {
                        'min_size': int(os.getenv('POSTGRES_POOL_MIN_SIZE', 5)),
                        'max_size': int(os.getenv('POSTGRES_POOL_MAX_SIZE', 20)),
                        'timeout': int(os.getenv('POSTGRES_POOL_TIMEOUT', 60)),  # seconds
                        'max_queries': int(os.getenv('POSTGRES_POOL_MAX_QUERIES', 10000)),
                        'max_inactive_connection_lifetime': int(os.getenv('POSTGRES_POOL_MAX_INACTIVE_LIFETIME', 300)),
                        # seconds
                        'command_timeout': int(os.getenv('POSTGRES_COMMAND_TIMEOUT', 30))
                        # seconds for a single command
                    }

                    logger.info(
                        f"Attempting to initialize PostgreSQL connection pool for '{self.db_name}' on {self.db_host}:{self.db_port}...")
                    self._pool = await asyncpg.create_pool(**conn_params, **pool_params)

                    # Test connection by acquiring and releasing one connection
                    async with self._pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")

                    logger.info("✅ PostgreSQL connection pool initialized successfully and connection tested.")

                except Exception as e:
                    logger.critical(f"❌ Failed to initialize PostgreSQL connection pool: {e}", exc_info=True)
                    # It's critical to re-raise or handle this as the application cannot proceed without DB
                    raise ConnectionError(f"Database connection failed: {e}")

    async def get_connection(self) -> asyncpg.Connection:
        """
        Acquires a connection from the pool.
        If the pool is not initialized, it will attempt to initialize it.
        """
        if self._pool is None:
            await self.initialize()  # Attempt to initialize if not already

        try:
            conn = await self._pool.acquire()
            logger.debug("Acquired connection from pool.")
            return conn
        except Exception as e:
            logger.error(f"Failed to acquire connection from pool: {e}", exc_info=True)
            raise

    async def release_connection(self, conn: asyncpg.Connection) -> None:
        """
        Releases a connection back to the pool.
        """
        if self._pool:
            await self._pool.release(conn)
            logger.debug("Released connection to pool.")
        else:
            logger.warning("Attempted to release connection, but connection pool is not initialized.")

    async def close_all_connections(self) -> None:
        """
        Closes all connections in the pool. This should be called gracefully
        during application shutdown.
        """
        async with self._lock:
            if self._pool:
                logger.info("Closing PostgreSQL connection pool...")
                await self._pool.close()
                self._pool = None
                logger.info("✅ PostgreSQL connection pool closed.")
            else:
                logger.info("No PostgreSQL connection pool to close.")

    async def execute_query(self, query: str, *args: Any) -> Optional[str]:
        """
        Executes a DDL/DML query that doesn't return rows (e.g., INSERT, UPDATE, DELETE, CREATE TABLE).
        Returns the command status string.
        """
        conn = None
        try:
            conn = await self.get_connection()
            status = await conn.execute(query, *args)
            logger.debug(f"Executed query: {query.splitlines()[0].strip()}... Status: {status}")
            return status
        except Exception as e:
            logger.error(f"Error executing query: {query.splitlines()[0].strip()}... Error: {e}", exc_info=True)
            raise
        finally:
            if conn:
                await self.release_connection(conn)

    async def fetch_rows(self, query: str, *args: Any) -> List[Dict[str, Any]]:
        """
        Executes a query that returns multiple rows (e.g., SELECT).
        Returns a list of dictionaries.
        """
        conn = None
        try:
            conn = await self.get_connection()
            rows = await conn.fetch(query, *args)
            logger.debug(f"Fetched {len(rows)} rows for query: {query.splitlines()[0].strip()}...")
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching rows: {query.splitlines()[0].strip()}... Error: {e}", exc_info=True)
            raise
        finally:
            if conn:
                await self.release_connection(conn)

    async def fetch_one(self, query: str, *args: Any) -> Optional[Dict[str, Any]]:
        """
        Executes a query that returns at most one row.
        Returns a dictionary or None.
        """
        conn = None
        try:
            conn = await self.get_connection()
            row = await conn.fetchrow(query, *args)
            logger.debug(f"Fetched one row for query: {query.splitlines()[0].strip()}...")
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching one row: {query.splitlines()[0].strip()}... Error: {e}", exc_info=True)
            raise
        finally:
            if conn:
                await self.release_connection(conn)

    async def fetch_val(self, query: str, *args: Any) -> Any:
        """
        Executes a query that returns a single value.
        Returns the value.
        """
        conn = None
        try:
            conn = await self.get_connection()
            val = await conn.fetchval(query, *args)
            logger.debug(f"Fetched value for query: {query.splitlines()[0].strip()}...")
            return val
        except Exception as e:
            logger.error(f"Error fetching value: {query.splitlines()[0].strip()}... Error: {e}", exc_info=True)
            raise
        finally:
            if conn:
                await self.release_connection(conn)


# Example usage (for testing this module in isolation)
async def main():
    # Set dummy environment variables for local testing
    os.environ['POSTGRES_USER'] = os.getenv('POSTGRES_USER', 'postgres')
    os.environ['POSTGRES_PASSWORD'] = os.getenv('POSTGRES_PASSWORD', 'password')
    os.environ['POSTGRES_DB'] = os.getenv('POSTGRES_DB', 'adaptive_mind_demo')
    os.environ['POSTGRES_HOST'] = os.getenv('POSTGRES_HOST', 'localhost')
    os.environ['POSTGRES_PORT'] = os.getenv('POSTGRES_PORT', '5432')

    manager = PostgreSQLConnectionManager()

    try:
        await manager.initialize()

        # Test query
        print("\n--- Testing SELECT query ---")
        current_time = await manager.fetch_val("SELECT NOW();")
        print(f"Current database time: {current_time}")

        # Test DDL (create a dummy table if it doesn't exist)
        print("\n--- Testing DDL query ---")
        await manager.execute_query("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50)
            );
        """)
        print("test_table ensured to exist.")

        # Test DML (insert data)
        print("\n--- Testing INSERT query ---")
        await manager.execute_query("INSERT INTO test_table (name) VALUES ($1);", "Test Name 1")
        await manager.execute_query("INSERT INTO test_table (name) VALUES ($1);", "Test Name 2")
        print("Inserted data into test_table.")

        # Test fetch_rows
        print("\n--- Testing FETCH_ROWS query ---")
        rows = await manager.fetch_rows("SELECT * FROM test_table ORDER BY id DESC LIMIT 2;")
        for row in rows:
            print(f"Fetched Row: {row}")

        # Test fetch_one
        print("\n--- Testing FETCH_ONE query ---")
        one_row = await manager.fetch_one("SELECT * FROM test_table WHERE id = $1;", rows[0]['id'])
        print(f"Fetched One Row: {one_row}")

        # Test closing and re-opening pool
        print("\n--- Testing pool re-initialization ---")
        await manager.close_all_connections()
        await manager.initialize()
        re_test = await manager.fetch_val("SELECT 'Pool re-initialized' FROM DUAL;")
        print(f"Re-initialized pool test: {re_test}")

    except ConnectionError as ce:
        print(f"Connection Error: {ce}. Please check your PostgreSQL server and environment variables.")
    except Exception as e:
        print(f"An unexpected error occurred during tests: {e}")
    finally:
        await manager.close_all_connections()
        print("\nAll database operations tested and connections closed.")


if __name__ == "__main__":
    asyncio.run(main())