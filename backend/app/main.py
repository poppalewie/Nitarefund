from fastapi import FastAPI
from app.api.routes import auth, transactions, wallet, users, trust, group

app = FastAPI()

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(trust.router)
app.include_router(group.router)
app.include_router(wallet.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {"message": "System online"}