from pydantic import BaseModel, Field
from typing import List


class GroupCreate(BaseModel):
    user_ids: List[int] = Field(..., min_items=1)
    total_amount: float = Field(gt=0)
    description: str | None = None