import datetime
from datetime import timedelta
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_postgres_session, get_redis_session
from config import settings
from models import QueryUsers


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
security_scheme = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Сверяет введеный пароль с хэшем пороля из бд

    :param plain_password: Введеный пользователем пароль при аутентификации
    :param hashed_password: Хэш пароля из базы данных
    :return: True если пароли совпадают, False если не совпадают
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Из строки с паролем вычисляет ее хэш

    :param password: Пароль
    :rerurn: Хэш пороля
    """
    return pwd_context.hash(password)


async def get_user_from_db(username: str, postgres: AsyncSession) -> QueryUsers | None:
    """
    Возвращет пользователя из базы данных со всеми его полями

    :param username: Имя пользователя
    :param postgres: Сессия базы данных
    :return: Пользователь
    """
    result = await postgres.execute(select(QueryUsers).where(QueryUsers.username == username))
    return result.scalars().first()


def create_access_token(username: str, expires_delta: timedelta | None = None) -> str:
    """
    Создает токен, по усолчанию время жизни токена 15 минут

    :param username: Имя пользователя
    :param expires_delta: Время жизни токена
    :return: Токен
    """
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta

    else:
        expire = datetime.datetime.now(datetime.UTC) + timedelta(minutes=15)

    to_encode = (
        {
            'sub': username,
            'exp': expire
        }
    )
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


async def add_to_blacklist(token: HTTPAuthorizationCredentials, expires_at: datetime, redis_session: AsyncSession):
    expires_in = expires_at - datetime.datetime.now(datetime.UTC)
    await redis_session.setex(token, int(expires_in.total_seconds()), 'revoked')


async def is_token_blacklisted(token: str, redis_session: AsyncSession) -> bool:
    return await redis_session.exists(token)


async def get_current_user(
        token: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
        postgres_session = Depends(get_postgres_session),
        redis_session = Depends(get_redis_session)
) -> QueryUsers:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Не верные имя пользователя или пароль',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    token = token.credentials
    if await is_token_blacklisted(token, redis_session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Токен был отозван'
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username = payload.get('sub')
        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await get_user_from_db(username, postgres_session)
    if user is None:
        raise credentials_exception

    return user
