import asyncio
import json

import aio_pika
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import engine
from app.models import Inbox, Order, Outbox

RABBIT_URL = "amqp://guest:guest@rabbitmq:5672/"
EXCHANGE_NAME = "events"
QUEUE_NAME = "orders.payment_result"
ROUTING_KEY = "payment.result"

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process(requeue=True):
        payload = json.loads(message.body.decode("utf-8"))

        message_id = payload["message_id"]
        order_id = int(payload["order_id"])
        payment_status = payload["status"]

        new_status = "PAID" if payment_status == "SUCCESS" else "CANCELLED"

        async with SessionLocal() as session:
            async with session.begin():
                res = await session.execute(select(Inbox).where(Inbox.message_id == message_id))
                if res.scalar_one_or_none() is not None:
                    return

                session.add(Inbox(message_id=message_id, payload=payload))

                await session.execute(
                    update(Order)
                    .where(Order.id == order_id)
                    .values(status=new_status)
                )

                session.add(
                    Outbox(
                        event_type="OrderStatusChanged",
                        aggregate_id=order_id,
                        payload={
                            "order_id": order_id,
                            "status": new_status,
                        },
                    )
                )

        print(f"Order {order_id} -> {new_status}")

async def connect_rabbit():
    delay = 1
    while True:
        try:
            return await aio_pika.connect_robust(RABBIT_URL)
        except Exception as e:
            print(f"RabbitMQ not ready yet: {e}. Retry in {delay}s")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 10)

async def main():
    connection = await connect_rabbit()
    async with connection:
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.bind(exchange, routing_key=ROUTING_KEY)

        print("orders-consumer started, waiting for payment results...")
        await queue.consume(handle_message)
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
