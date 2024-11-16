import asyncpg
from typing import List, Any, Optional

class DatabaseConnection:
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                user='match-score_owner',
                password='3qem5dgbONsA',
                host='ep-broad-morning-a2defk2e.eu-central-1.aws.neon.tech',
                port=5432,
                database='match-score'
            )
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    async def read_query(cls, sql: str, *params) -> List[Any]:
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            results = await conn.fetch(sql, *params)
            return [tuple(row) for row in results]

    @classmethod
    async def insert_query(cls, sql: str, *params) -> int:
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            # Add RETURNING id if not present
            if "RETURNING id" not in sql.upper():
                sql += " RETURNING id"
            result = await conn.fetchval(sql, *params)
            return result

    @classmethod
    async def update_query(cls, sql: str, *params) -> bool:
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(sql, *params)
            return True