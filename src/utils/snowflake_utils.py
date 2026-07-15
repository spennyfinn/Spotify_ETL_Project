from contextlib import contextmanager
import dotenv
import os
from snowflake.connector import connect
from snowflake.connector.cursor import SnowflakeCursor


dotenv.load_dotenv()

DATABASE =  os.getenv('SNOWFLAKE_DATABASE', 'MUSICDB')




def get_snowflake_connection():
    account = os.environ["SNOWFLAKE_ACCOUNT"]
    user = os.environ["SNOWFLAKE_USER"]
    key_path = os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]
    key_passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")

    connect_kwargs = {
        "account": account,
        "user": user,
        "authenticator": "SNOWFLAKE_JWT",
        "private_key_file": key_path,
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "MUSICDB"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
    }
    if key_passphrase:
        connect_kwargs["private_key_file_pwd"] = key_passphrase
    if host := os.getenv("SNOWFLAKE_HOST"):
        connect_kwargs["host"] = host

    return connect(**connect_kwargs)


@contextmanager
def snowflake_cursor():
    conn = get_snowflake_connection()
    cur = conn.cursor()

    try:
        yield cur
    finally:
        cur.close()
        conn.close()


@contextmanager
def snowflake_connection():
    conn = get_snowflake_connection()
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(
    query: str,
    cur: SnowflakeCursor | None = None,
    params: dict | None = None,
) -> list[tuple]:
    """Run a query and return all rows.

    Pass an existing cursor to reuse a session connection; omit ``cur`` to
    open and close a short-lived connection automatically.
    """
    if cur is None:
        with snowflake_cursor() as cursor:
            cursor.execute(query, params or {})
            return cursor.fetchall()

    cur.execute(query, params or {})
    return cur.fetchall()


    