from fastapi import FastAPI
import uvicorn
import pandas as pd
import warnings


app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/portfolio")
def portfolio():
    
    url = "https://docs.google.com/spreadsheets/d/1JOmzegYf0kGxDcjej0Fx_RCuFVoaOxobEnDsptjTJA8/export?format=csv&gid=595987006"

    df = pd.read_csv(url)

    # looks for columns E:H 
    df = df.iloc[:,[4,5,6,7]]

    # drops the Weird ADBE and CRM Numbers at 
    df.dropna(inplace = True)

    for i in range(df.shape[1]):
        warnings.filterwarnings('ignore')
        df.rename(columns={df.columns[i]:df.iloc[0][i]}, inplace=True)

    df.drop([0], inplace=True)

    print(df.head())

    return df

portfolio()