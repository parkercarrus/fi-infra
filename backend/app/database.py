from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import duckdb

from backend.app.config import get_settings


@contextmanager
def duckdb_connection(read_only: bool = True) -> Iterator[duckdb.DuckDBPyConnection]:
    settings = get_settings()
    connection = duckdb.connect(str(settings.database_path), read_only=read_only)
    try:
        yield connection
    finally:
        connection.close()
