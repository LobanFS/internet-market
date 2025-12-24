# SE_4 — Orders & Payments Microservices

Использовались:

- **FastAPI**
- **PostgreSQL**
- **RabbitMQ**
- **Outbox / Inbox pattern**
- **API Gateway**
- **WebSocket (push-уведомления)**
- **Frontend (React + Vite)**
- **Docker Compose**

Проект реализует сценарий оформления заказа с асинхронной оплатой и доставкой статуса заказа в реальном времени.

---

## Архитектура

Система состоит из следующих сервисов:

### Backend
- **gateway-api**  
  API Gateway:
  - проксирует REST-запросы к orders и payments
  - поднимает WebSocket сервер
  - подписывается на события из RabbitMQ и пушит обновления клиентам

- **orders-api**  
  Сервис заказов:
  - создание заказов
  - хранение заказов
  - Outbox-событие `PaymentRequested`

- **orders-worker**  
  Публикует события `PaymentRequested` из Outbox в RabbitMQ

- **orders-consumer**  
  Обрабатывает `PaymentResult`, обновляет статус заказа  
  Использует Inbox для дедупликации

- **payments-api**  
  Сервис платежей:
  - создание аккаунтов
  - пополнение баланса
  - получение списка аккаунтов
  - получение баланса пользователя

- **payments-worker**  
  Обрабатывает `PaymentRequested`:
  - атомарное списание средств
  - идемпотентность
  - запись `PaymentResult` в Outbox

- **payments-publisher**  
  Публикует `PaymentResult` в RabbitMQ

### Infrastructure
- **RabbitMQ** (+ management UI)
- **PostgreSQL (orders-db, payments-db)**

### Frontend
- **React + Vite**
- Подключается только к **API Gateway**
- Использует WebSocket для отслеживания статуса заказа

---

## Основной сценарий работы

1. Создать аккаунт пользователя
2. Пополнить баланс
3. Создать заказ
4. Orders публикует `PaymentRequested`
5. Payments обрабатывает платёж
6. Orders получает `PaymentResult`
7. Gateway отправляет статус заказа по WebSocket
8. Фронтенд получает push-уведомление

---

## Запуск проекта

### 1. Запуск всех сервисов

```bash
docker compose up --build
```

### 2. Проверка доступности сервисов

* Gateway health:

```
GET http://localhost:8080/health
```

---

## Доступные сервисы и порты

| Сервис      | URL                                              |
| ----------- | ------------------------------------------------ |
| Frontend    | [http://localhost:5173](http://localhost:5173)   |
| API Gateway | [http://localhost:8080](http://localhost:8080)   |
| RabbitMQ UI | [http://localhost:15672](http://localhost:15672) |
RabbitMQ credentials:

```
login: guest
password: guest
```

---

## Swagger / OpenAPI

Swagger доступен через API Gateway.

### Orders

```
http://localhost:8080/orders/docs
```

### Payments

```
http://localhost:8080/payments/docs
```

Через Swagger можно:

* создавать заказы
* получать список заказов
* создавать аккаунты
* пополнять баланс
* получать список аккаунтов и балансы

---

## REST API (основное)

### Orders

* `POST /orders/orders` — создать заказ
* `GET /orders/orders` — список заказов
* `GET /orders/orders/{order_id}` — получить заказ

### Payments

* `POST /payments/accounts` — создать аккаунт
* `POST /payments/accounts/topup` — пополнить баланс
* `GET /payments/accounts/{user_id}/balance` — баланс пользователя
* `GET /payments/accounts` — список всех аккаунтов

---

## WebSocket

WebSocket поднимается **в API Gateway**.

### Endpoint

```
ws://localhost:8080/ws/orders/{order_id}
```

### Назначение

* Получение push-уведомлений при изменении статуса заказа

### Тестирование WebSocket

Необходимо использовать `wscat`:

```bash
npx wscat -c ws://localhost:8080/ws/orders/1
```

При изменении статуса заказа сервер отправляет сообщение вида:

```json
{
  "order_id": 1,
  "status": "PAID"
}
```

---

## Frontend

Frontend реализован как отдельный сервис и взаимодействует с backend **только через API Gateway**.

### Возможности UI

* создание аккаунта
* пополнение баланса
* создание заказа
* отслеживание статуса заказа по WebSocket
* история заказов
* список пользователей и их балансы

### Доступ

```
http://localhost:5173
```

---

## Надёжность и паттерны

### Outbox / Inbox

* Все события записываются в БД в рамках транзакции
* Отдельные воркеры публикуют события в RabbitMQ
* Inbox используется для дедупликации сообщений
* Идемпотентность обеспечена на уровне `order_id`

### Гарантии

* Заказ не будет обработан дважды
* Платёж не будет списан повторно
* Статус заказа всегда консистентен

---

## Соответствие требованиям ТЗ

* Микросервисная архитектура — ✅
* Асинхронное взаимодействие (RabbitMQ) — ✅
* Outbox / Inbox — ✅
* API Gateway — ✅
* WebSocket push-уведомления — ✅
* Frontend как отдельный сервис — ✅
* Docker Compose — ✅
* Swagger / OpenAPI — ✅


