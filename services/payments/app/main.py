from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine, Base, get_session
from app import models  # noqa: F401
from app.schemas import CreateAccountRequest, TopUpRequest, AccountResponse

from app.repository import AccountsRepository

app = FastAPI(title="Payments Service", version="0.0.1")
repo = AccountsRepository()


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
def health():
    return {"status": "ok", "service": "payments"}


@app.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_account(
    req: CreateAccountRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        async with session.begin():
            acc = await repo.create_account(session, req.user_id)
        return AccountResponse(user_id=acc.user_id, balance=acc.balance)
    except ValueError as e:
        if str(e) == "ACCOUNT_EXISTS":
            raise HTTPException(status_code=409, detail="Account already exists")
        raise

@app.post("/accounts/topup", response_model=AccountResponse)
async def topup(
    req: TopUpRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        async with session.begin():
            new_balance = await repo.topup(session, req.user_id, req.amount)
        return AccountResponse(user_id=req.user_id, balance=new_balance)
    except ValueError as e:
        if str(e) == "ACCOUNT_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Account not found")
        raise



@app.get("/accounts/{user_id}/balance", response_model=AccountResponse)
async def get_balance(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    acc = await repo.get_account(session, user_id)
    if acc is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse(user_id=acc.user_id, balance=acc.balance)

@app.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(session: AsyncSession = Depends(get_session)):
    accounts = await repo.list_accounts(session)
    return [AccountResponse(user_id=a.user_id, balance=a.balance) for a in accounts]