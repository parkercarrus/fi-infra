from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/portfolio")
def portfolio():
    # implement portfolio getting and send to frontend
    return {}
