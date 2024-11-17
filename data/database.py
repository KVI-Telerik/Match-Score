import asyncpg
from typing import List, Any, Optional, Union
from contextlib import asynccontextmanager

class DatabaseConnection:
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    user='match-score_owner',
                    password='3qem5dgbONsA',
                    host='ep-broad-morning-a2defk2e.eu-central-1.aws.neon.tech',
                    port=5432,
                    database='match-score',
                    min_size=1,
                    max_size=10  # Adjust based on your needs
                )
            except Exception as e:
                print(f"Failed to create connection pool: {str(e)}")
                raise
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            yield connection

    @classmethod
    async def read_query(cls, sql: str, *params) -> List[Any]:
        try:
            async with cls.get_connection() as conn:
                results = await conn.fetch(sql, *params)
                return [tuple(row) for row in results]
        except Exception as e:
            print(f"Error executing read query: {str(e)}")
            print(f"Query: {sql}")
            print(f"Parameters: {params}")
            raise

    @classmethod
    async def insert_query(cls, sql: str, *params) -> Optional[int]:
        try:
            async with cls.get_connection() as conn:
                if "RETURNING" not in sql.upper():
                    sql += " RETURNING id"
                result = await conn.fetchval(sql, *params)
                return result
        except Exception as e:
            print(f"Error executing insert query: {str(e)}")
            print(f"Query: {sql}")
            print(f"Parameters: {params}")
            raise

    @classmethod
    async def update_query(cls, sql: str, *params) -> bool:
        try:
            async with cls.get_connection() as conn:
                await conn.execute(sql, *params)
                return True
        except Exception as e:
            print(f"Error executing update query: {str(e)}")
            print(f"Query: {sql}")
            print(f"Parameters: {params}")
            return False

    @classmethod
    async def test_connection(cls) -> bool:
        try:
            async with cls.get_connection() as conn:
                await conn.fetch("SELECT 1")
                return True
        except Exception as e:
            print(f"Database connection test failed: {str(e)}")
            return False