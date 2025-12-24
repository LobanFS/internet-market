import asyncio
import json
from datetime import datetime

import aio_pika
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import engine
from app.models import Outbox

RABBIT_URL = "amqp://guest:guest@rabbitmq:5672/"
EXCHANGE_NAME = "events"
ROUTING_KEY = "payment.result"

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def publish_once() -> int:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Outbox)
            .where(Outbox.published_at.is_(None))
            .order_by(Outbox.id)
            .limit(20)
        )
        events = list(result.scalars())
        if not events:
            return 0

    connection = await aio_pika.connect_robust(RABBIT_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )

        published_ids: list[int] = []
        for ev in events:
            body = json.dumps(ev.payload).encode("utf-8")
            msg = aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await exchange.publish(msg, routing_key=ROUTING_KEY)
            published_ids.append(ev.id)

    async with SessionLocal() as session:
        async with session.begin():
            await session.execute(
                update(Outbox)
                .where(Outbox.id.in_(published_ids))
                .values(published_at=datetime.utcnow())
            )

    return len(published_ids)


async def main():
    print("payments-publisher started")
    while True:
        try:
            n = await publish_once()
            if n:
                print(f"published {n} events")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"publisher error: {e}")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
