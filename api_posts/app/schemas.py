from pydantic import BaseModel, field_validator
from datetime import datetime


class PostCreate(BaseModel):
    title: str
    content: str


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str

    @field_validator('password')
    def validate_password(cls, passw):
        return validate_password_strength(passw)


class UpdatePassword(BaseModel):
    old_password: str
    mew_password: str


    @field_validator('mew_password')
    def validate_password(cls, passw):
        return validate_password_strength(passw)

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


def validate_password_strength(password: str) -> str:
    """
    Валидация пароля: минимум 8 символов и хотя бы одна цифра

    :param password: Пароль для валидации
    :return: Провалидированный пароль
    """
    if len(password) < 8:
        raise ValueError("Пароль должен содержать минимум 8 символов")
    if not any(c.isdigit() for c in password):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")
    return password
