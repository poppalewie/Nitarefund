from fastapi import FastAPI
from app.api.routes import auth, transactions

app = FastAPI()

app.include_router(auth.router)
app.include_router(transactions.router)

@app.get("/")
def root():
    return {"message": "System online"}