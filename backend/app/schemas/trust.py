from pydantic import BaseModel


class TrustOut(BaseModel):
    user_a_id: int
    user_b_id: int
    score: float

    class Config:
        from_attributes = True


class TrustWithUser(BaseModel):
    user_id: int
    username: str
    score: float