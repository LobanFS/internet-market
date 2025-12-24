import asyncio
import json
import aio_pika
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, update
from app.db import engine
from app.models import Inbox, PaymentTransaction, Outbox, Account


RABBIT_URL = "amqp://guest:guest@rabbitmq:5672/"
EXCHANGE_NAME = "events"
QUEUE_NAME = "payments.payment_requested"
ROUTING_KEY = "payment.requested"

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def connect_rabbit():
    delay = 1
    while True:
        try:
            return await aio_pika.connect_robust(RABBIT_URL)
        except Exception as e:
            print(f"RabbitMQ not ready yet: {e}. Retry in {delay}s")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 10)

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process(requeue=True):
        payload = json.loads(message.body.decode("utf-8"))

        print("PaymentRequested:", payload)

        async with SessionLocal() as session:
            async with session.begin():
                message_id = payload["message_id"]
                order_id = int(payload["order_id"])
                user_id = int(payload["user_id"])
                amount = int(payload["amount"])

                res = await session.execute(select(Inbox).where(Inbox.message_id == message_id))
                if res.scalar_one_or_none() is not None:
                    return

                session.add(Inbox(message_id=message_id, payload=payload))

                res = await session.execute(
                    select(PaymentTransaction).where(PaymentTransaction.order_id == order_id)
                )
                if res.scalar_one_or_none() is not None:
                    return

                res = await session.execute(select(Account).where(Account.user_id == user_id))
                acc = res.scalar_one_or_none()
                if acc is None:
                    status = "FAILED"
                    reason = "ACCOUNT_NOT_FOUND"
                else:
                    stmt = (
                        update(Account)
                        .where(Account.user_id == user_id, Account.balance >= amount)
                        .values(balance=Account.balance - amount)
                        .returning(Account.balance)
                    )
                    res = await session.execute(stmt)
                    new_balance = res.scalar_one_or_none()

                    if new_balance is None:
                        status = "FAILED"
                        reason = "INSUFFICIENT_FUNDS"
                    else:
                        status = "SUCCESS"
                        reason = None

                session.add(
                    PaymentTransaction(
                        order_id=order_id,
                        user_id=user_id,
                        amount=amount,
                        status=status,
                        reason=reason,
                    )
                )

                session.add(
                    Outbox(
                        event_type="PaymentResult",
                        aggregate_id=order_id,
                        payload={
                            "message_id": message_id,
                            "order_id": order_id,
                            "status": status,
                            "reason": reason,
                        },
                    )
                )

async def main():
    connection = await connect_rabbit()
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True)

        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.bind(exchange, routing_key=ROUTING_KEY)

        print("payments-worker started, waiting for messages...")
        await queue.consume(handle_message)

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
