from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: int = Field(..., gt=0)
    description: str | None = None


class OrderResponse(BaseModel):
    order_id: int
    user_id: int
    amount: int
    status: str
