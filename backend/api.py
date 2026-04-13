# Access Google Sheets API / BNY Mellon API and return information
from pathlib import Path
import duckdb


Parent_Path = Path(__file__).resolve().parents[1] / "algory.duckdb"
Parent_Path.parent.mkdir(parents=True, exist_ok=True)
from main import portfolio


def fetchData(Timestamp):
    df = portfolio()

    con = duckdb.connect(str(Parent_Path))

    for i in range(df.count()):
        con.execute(f"""
        INSERT INTO positions (timestamp, ticker, num_shares, price)
        VALUES ({Timestamp}, {df.iloc[i][0]}, {df.iloc[i][3]}, {df.iloc[i][6]/df.iloc[i][3]});
        );
        """)

    return