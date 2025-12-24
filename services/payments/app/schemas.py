from pydantic import BaseModel, Field


class CreateAccountRequest(BaseModel):
    user_id: int = Field(..., gt=0)


class TopUpRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: int = Field(..., gt=0)


class AccountResponse(BaseModel):
    user_id: int
    balance: int
