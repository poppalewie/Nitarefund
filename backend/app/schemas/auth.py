from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    security_answer: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"