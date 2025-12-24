from sqlalchemy import BigInteger, Text, JSON, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .db import Base

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )


class Inbox(Base):
    __tablename__ = "inbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    message_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    aggregate_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP, nullable=True
    )
