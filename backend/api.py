# Access Google Sheets API / BNY Mellon API and return information
from pathlib import Path
import duckdb
import yfinance as yf
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import portfolio

Parent_Path = Path(__file__).resolve().parents[1] / "algory.duckdb"
Parent_Path.parent.mkdir(parents=True, exist_ok=True)
#from main import portfolio
Theoretical_db_path = Parent_Path.parent / "Theoretical.duckdb"

def fetchData(Timestamp):
    df = portfolio()
    con = duckdb.connect(str(Parent_Path))

    rows = [
        (Timestamp, df.iloc[i][0], df.iloc[i][3], df.iloc[i][6] / df.iloc[i][3])
        for i in range(df.shape[0])
    ]

    con.executemany("""
        INSERT INTO positions (timestamp, ticker, num_shares, price)
        VALUES (?, ?, ?, ?)
    """, rows)

    con.close()

def ResetTheoreticalDB():
    con = duckdb.connect(str(Parent_Path))
    df = con.sql("SELECT * FROM positions").df()
    con.close()
    
    Theoretical_db_path.unlink(missing_ok=True)
    
    new_con = duckdb.connect(str(Theoretical_db_path))
    new_con.execute("""
        CREATE TABLE positions (
            timestamp TIMESTAMP,
            ticker VARCHAR,
            num_shares INTEGER,
            price FLOAT
        )
    """)

    if not df.empty:
        rows = [
            (row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
             row[1], row[2], row[3])
            for row in df.itertuples(index=False)
        ]
        new_con.executemany("""
            INSERT INTO positions (timestamp, ticker, num_shares, price)
            VALUES (?, ?, ?, ?)
        """, rows)

    new_con.close()
    print("Theoretical database created from dataframe.")

def addTheoreticalPosition(TICKER, ENTRANCE, EXIT, numShares=1):
    data = yf.download(TICKER, start=ENTRANCE, end=EXIT)
    con = duckdb.connect(str(Theoretical_db_path))

    for i in range(len(data)):
        price = float(data.iloc[i]["Close"])
        con.execute("""
            INSERT INTO positions (timestamp, ticker, num_shares, price)
            VALUES (?, ?, ?, ?)
        """, [data.index[i].isoformat(), TICKER, numShares, price])  # isoformat() here too

    con.close() 

ResetTheoreticalDB()
addTheoreticalPosition("AMZN","2023-1-1","2024-1-1")
con = duckdb.connect(str(Theoretical_db_path))
df = con.sql("SELECT * FROM positions").df()
df.head()