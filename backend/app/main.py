from fastapi import FastAPI
from app.api.routes import auth, transactions, trust, group

app = FastAPI()

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(trust.router)
app.include_router(group.router)

@app.get("/")
def root():
    return {"message": "System online"}