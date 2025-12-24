from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.models import Order, Outbox

class OrdersRepository:
    async def create_order(
        self,
        session: AsyncSession,
        user_id: int,
        amount: int,
        description: str | None,
    ) -> Order:
        order = Order(
            user_id=user_id,
            amount=amount,
            description=description,
            status="NEW",
        )
        session.add(order)
        await session.flush()
        message_id = str(uuid.uuid4())
        event = Outbox(
            event_type="PaymentRequested",
            aggregate_id=order.id,
            payload={
                "message_id": message_id,
                "order_id": order.id,
                "user_id": user_id,
                "amount": amount,
            },
        )
        session.add(event)

        return order

    async def get_order(self, session: AsyncSession, order_id: int) -> Order | None:
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def list_orders(self, session: AsyncSession) -> list[Order]:
        result = await session.execute(select(Order))
        return list(result.scalars())
