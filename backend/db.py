import duckdb
from pathlib import Path

def initialize_duckdb() -> int:
    DB_PATH = Path(__file__).resolve().parents[1] / "algory.duckdb"
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH))

    con.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        timestamp TIMESTAMP,
        ticker TEXT,
        num_shares INT,
        price INT,
    );
    """)

    con.close()
    print(f"DuckDB initialized successfully at '{DB_PATH}'")
    return 100

if __name__ == "__main__":
    initialize_duckdb()