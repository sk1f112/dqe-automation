"""PostgreSQL connection and query support for the DQ test framework."""

from typing import Optional

import pandas as pd
import psycopg2


class PostgresConnectorContextManager:
    """Manage a PostgreSQL connection and return query results as DataFrames."""

    def __init__(
        self,
        db_user: str,
        db_password: str,
        db_host: str,
        db_name: str,
        db_port: int,
    ) -> None:
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_name = db_name
        self.db_port = db_port
        self.connection: Optional[psycopg2.extensions.connection] = None

    def __enter__(self) -> "PostgresConnectorContextManager":
        self.connection = psycopg2.connect(
            host=self.db_host,
            dbname=self.db_name,
            port=self.db_port,
            user=self.db_user,
            password=self.db_password,
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def get_data_sql(self, sql: str) -> pd.DataFrame:
        """Execute a read query using the active connection."""
        if self.connection is None or self.connection.closed:
            raise RuntimeError("PostgreSQL connection is not open")
        return pd.read_sql_query(sql, self.connection)
