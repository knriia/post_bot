import datetime

from asyncpg.pgproto.pgproto import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from auth import (
    verify_password,
    create_access_token,
    get_current_user,
    get_password_hash,
    get_user_from_db,
    security_scheme,
    add_to_blacklist,
)
from config import settings
from models import QueryUsers
from schemas import UserResponse, Token, UserCreate, UpdatePassword
from database import get_postgres_session, get_redis_session


router = APIRouter(
    prefix='/users',
    tags = ['users']
)


@router.post("/register", response_model=UserResponse)
async def register_user(
    input_user_data: UserCreate,
    postgres: AsyncSession = Depends(get_postgres_session)
):
    """
    Регистрирует нового пользователя

    :param input_user_data: Данные пользователя логин и пороль
    :param postgres: Сессия для postgres
    :return: Возвращает id и имя пользователя
    """
    username = input_user_data.username
    result = await get_user_from_db(username, postgres)
    if result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь таким именем уже зарегитрирован'
        )

    new_user = QueryUsers(
        username=username,
        hashed_password=get_password_hash(input_user_data.password)
    )

    postgres.add(new_user)
    await postgres.commit()
    await postgres.refresh(new_user)
    return new_user


@router.post("/change-password")
async def change_password(
    passwords: UpdatePassword,
    postgres: AsyncSession = Depends(get_postgres_session),
    current_user: QueryUsers = Depends(get_current_user)
):
    """
    Заменяет старый пароль пользователя на новый

    :param passwords: Модель с паролями
    :param postgres: Сессия для postgres
    :param current_user: Текущий активный пользователь
    :return: Сообщение об успешной или не успешной смене пароля
    """
    if passwords.old_password == passwords.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Новый пароль не должен совпадать со старым',
        )

    if verify_password(passwords.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Неверный текущий пароль'
        )

    new_hashed_password = get_password_hash(passwords.new_password)
    await postgres.execute(
        (
            update(QueryUsers)
            .where(QueryUsers.username == current_user.username)
            .values(hashed_password=new_hashed_password)
        )
    )

    await postgres.commit()
    await postgres.refresh(current_user)


@router.post('/login', response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        postgres: AsyncSession = Depends(get_postgres_session)
):
    """
    Получает токен для пользователя

    :param form_data: Данные пользователя логин и пороль
    :param postgres: Сессия для postgres
    :return: Возвращет токен
    """
    user = await get_user_from_db(form_data.username, postgres)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise  HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Некоректные имя пользователя или пароль',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    access_token_expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(username=user.username, expires_delta=access_token_expire)
    return Token(access_token=access_token, token_type='bearer')


@router.post('/logout')
async def user_logout(
        token: HTTPAuthorizationCredentials = Depends(security_scheme),
        redis_session: AsyncSession = Depends(get_redis_session),
        current_user: QueryUsers = Depends(get_current_user),
):
    """
    Разлогиневает пользователя

    :param token: Токен пользователя
    :param redis_session: Сессия для redis
    :param current_user: Текущий активный пользователь
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        expires_at = datetime.datetime.fromtimestamp(payload['exp'], datetime.UTC)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Невалидный токе'
        )

    await add_to_blacklist(token, expires_at, redis_session)

    return {'message': 'Пользователь успешно разлогинился'}