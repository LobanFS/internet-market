from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.models import Account


class AccountsRepository:
    async def create_account(self, session: AsyncSession, user_id: int) -> Account:
        result = await session.execute(select(Account).where(Account.user_id == user_id))
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise ValueError("ACCOUNT_EXISTS")

        acc = Account(user_id=user_id, balance=0)
        session.add(acc)

        await session.flush()
        return acc

    async def get_account(self, session: AsyncSession, user_id: int) -> Account | None:
        result = await session.execute(select(Account).where(Account.user_id == user_id))
        return result.scalar_one_or_none()

    async def topup(self, session: AsyncSession, user_id: int, amount: int) -> int:
        stmt = (
            update(Account)
            .where(Account.user_id == user_id)
            .values(balance=Account.balance + amount)
            .returning(Account.balance)
        )
        result = await session.execute(stmt)
        new_balance = result.scalar_one_or_none()
        if new_balance is None:
            raise ValueError("ACCOUNT_NOT_FOUND")
        return int(new_balance)

    async def list_accounts(self, session: AsyncSession) -> list[Account]:
        result = await session.execute(select(Account).order_by(Account.user_id))
        return list(result.scalars())

