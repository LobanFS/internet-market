import asyncio
import json
import aio_pika
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
import httpx
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
app = FastAPI(title="API Gateway", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ORDERS_BASE = "http://orders-api:8000"
PAYMENTS_BASE = "http://payments-api:8000"
RABBIT_URL = "amqp://guest:guest@rabbitmq:5672/"
EXCHANGE_NAME = "events"
QUEUE_NAME = "gateway.order_status_changed"
ROUTING_KEY = "order.status_changed"

client = httpx.AsyncClient()

subscribers: dict[int, set[WebSocket]] = defaultdict(set)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}

async def _proxy(request: Request, base_url: str, path: str) -> Response:
    url = f"{base_url}/{path}"
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()
    proxied = await client.request(
        method=request.method,
        url=url,
        params=request.query_params,
        content=body,
        headers=headers,
        timeout=30.0,
    )

    return Response(
        content=proxied.content,
        status_code=proxied.status_code,
        headers={"content-type": proxied.headers.get("content-type", "application/json")},
    )

async def rabbit_consumer():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
    )
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(exchange, routing_key=ROUTING_KEY)

    print("gateway rabbit consumer started")

    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process(requeue=True):
            payload = json.loads(message.body.decode("utf-8"))
            order_id = int(payload["order_id"])
            status = payload["status"]

            conns = list(subscribers.get(order_id, []))
            if not conns:
                return

            dead: list[WebSocket] = []
            for ws in conns:
                try:
                    await ws.send_json({"order_id": order_id, "status": status})
                except Exception:
                    dead.append(ws)

            for ws in dead:
                subscribers[order_id].discard(ws)

    await queue.consume(on_message)

@app.on_event("startup")
async def startup():
    asyncio.create_task(rabbit_consumer())


@app.api_route("/orders/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_orders(request: Request, path: str):
    return await _proxy(request, ORDERS_BASE, path)

@app.api_route("/payments/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_payments(request: Request, path: str):
    return await _proxy(request, PAYMENTS_BASE, path)

@app.websocket("/ws/orders/{order_id}")
async def ws_orders(ws: WebSocket, order_id: int):
    await ws.accept()
    subscribers[order_id].add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        subscribers[order_id].discard(ws)
        if not subscribers[order_id]:
            subscribers.pop(order_id, None)

