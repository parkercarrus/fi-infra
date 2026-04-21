# Access Google Sheets API / BNY Mellon API and return information
from pathlib import Path
import duckdb
import yfinance as yf

Parent_Path = Path(__file__).resolve().parents[1] / "algory.duckdb"
Parent_Path.parent.mkdir(parents=True, exist_ok=True)
#from main import portfolio
Theoretical_db_path = Parent_Path.parent / "Theoretical.duckdb"

def fetchData(Timestamp):
    df = portfolio()

    con = duckdb.connect(str(Parent_Path))

    for i in range(df.shape[0]):
        con.execute(f"""
        INSERT INTO positions (timestamp, ticker, num_shares, price)
        VALUES ({Timestamp}, {df.iloc[i][0]}, {df.iloc[i][3]}, {df.iloc[i][6]/df.iloc[i][3]});
        );
        """)

    return

def ResetTheoreticalDB():
    con = duckdb.connect(str(Parent_Path))
    df = con.sql("SELECT * FROM positions").df()
    con.close()
    
    Theoretical_db_path.unlink(missing_ok=True)
    
    new_con = duckdb.connect(str(Theoretical_db_path))
    new_con.execute("CREATE TABLE positions AS SELECT * FROM df")
    new_con.close()
    print("Theoretical database created from dataframe.")

def addTheoreticalPosition(TICKER, ENTRANCE, EXIT, numShares = 1):
    # dates formatted as YYYY-MM-DD
    data = yf.download(TICKER, start=ENTRANCE, end=EXIT)

    con = duckdb.connect(str(Theoretical_db_path))

    print("XXXX")
    print(con.execute("SELECT * FROM positions").fetchdf())
    
    print("XXXX")

    for i in range(data.shape[0]):
        con.execute(f"""
        INSERT INTO positions (timestamp, "$Ticker ", "num_shares", price)
        VALUES ({data.index[i].timestamp()}, '{TICKER}', {numShares}, {data.iloc[i][3]});
        """)

ResetTheoreticalDB()
addTheoreticalPosition("AMZN","2023-1-1","2024-1-1")
con = duckdb.connect(str(Theoretical_db_path))
df = con.sql("SELECT * FROM positions").df()
df.head()