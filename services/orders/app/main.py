from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import engine, Base, get_session
from app import models  # noqa: F401
from app.schemas import CreateOrderRequest, OrderResponse
from app.repository import OrdersRepository

app = FastAPI(title="Orders Service", version="0.0.1")
repo = OrdersRepository()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
def health():
    return {"status": "ok", "service": "orders"}


@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    req: CreateOrderRequest,
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        order = await repo.create_order(
            session,
            user_id=req.user_id,
            amount=req.amount,
            description=req.description,
        )
    return OrderResponse(
        order_id=order.id,
        user_id=order.user_id,
        amount=order.amount,
        status=order.status,
    )

@app.get("/orders", response_model=list[OrderResponse])
async def list_orders(session: AsyncSession = Depends(get_session)):
    orders = await repo.list_orders(session)
    return [
        OrderResponse(
            order_id=o.id,
            user_id=o.user_id,
            amount=o.amount,
            status=o.status,
        )
        for o in orders
    ]


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, session: AsyncSession = Depends(get_session)):
    order = await repo.get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(
        order_id=order.id,
        user_id=order.user_id,
        amount=order.amount,
        status=order.status,
    )
