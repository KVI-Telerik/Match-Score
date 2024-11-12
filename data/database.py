import psycopg2
from psycopg2.extensions import connection as Connection

# Change password to make requests
def _get_connection() -> Connection:
    return psycopg2.connect(
        user='root',
        password='postgres123', 
        host='localhost',
        port=5432,  # Default PostgreSQL port
        database='forumdb'
    )

def read_query(sql: str, sql_params=()):
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, sql_params)
        return list(cursor)

def insert_query(sql: str, sql_params=()) -> int:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql + " RETURNING id", sql_params)
        last_inserted_id = cursor.fetchone()[0]
        conn.commit()
        return last_inserted_id

def update_query(sql: str, sql_params=()) -> bool:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, sql_params)
        conn.commit()
    return True