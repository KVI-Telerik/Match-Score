import psycopg2
from psycopg2.extensions import connection as Connection


def _get_connection() -> Connection:
    return psycopg2.connect(
        user='match-score_owner',
        password='3qem5dgbONsA',
        host='ep-broad-morning-a2defk2e.eu-central-1.aws.neon.tech',
        port=5432,
        database='match-score'
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