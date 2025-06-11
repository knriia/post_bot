from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, update, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from models import QueryPosts, QueryUsers
from schemas import PostCreate, PostResponse, UserBase
from database import get_postgres_session


router = APIRouter(
    prefix='/posts',
    tags = ['posts']
)


@router.post('/create', response_model=PostResponse)
async def create_post(
        post: PostCreate,
        postgres: AsyncSession = Depends(get_postgres_session),
        current_user: QueryUsers = Depends(get_current_user)
):
    """
    Создает пост

    :param post: Данные для поста
    :param postgres: Сессия для postgres
    :param current_user: Объект с авторизированным пользователем, для внесения изменнений в бд
    :return: Возвращет пост
    """
    new_post = QueryPosts(
        **post.model_dump(),
        username=current_user.username
    )
    postgres.add(new_post)
    await postgres.commit()
    await postgres.refresh(new_post)

    return new_post


@router.post('/editing/{post_id}', response_model=PostResponse)
async def editing_post(
        post_id: int,
        post: PostCreate,
        postgres: AsyncSession = Depends(get_postgres_session),
        current_user: QueryUsers = Depends(get_current_user)
):
    """
    Редактирует пост

    :param post_id: id поста
    :param post: Данные для поста
    :param postgres: Сессия для postgres
    :param current_user: Объект с авторизированным пользователем, для внесения изменнений в бд
    :return: Возвращет отредактированный пост
    """
    update_data = {}
    if post.title is not None and post.title.strip() != "":
        update_data["title"] = post.title
    if post.content is not None and post.content.strip() != "":
        update_data["content"] = post.content

    if not update_data:
        raise HTTPException(status_code=400, detail='Нет данных для обновления')

    new_post = await postgres.execute(
        update(QueryPosts)
        .where(QueryPosts.id == post_id)
        .where(QueryPosts.username == current_user.username)
        .values(**update_data)
    )

    if new_post.rowcount == 0:
        raise HTTPException(status_code=404, detail="Пост не найден или у вас не хватает прав на редоктирование")

    await postgres.commit()
    updated_post = await postgres.get(QueryPosts, post_id)
    if not updated_post:
        raise HTTPException(status_code=404, detail='Пост не найден после обновления')

    return updated_post


@router.get("/read_all", response_model=list[PostResponse])
async def read_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    postgres: AsyncSession = Depends(get_postgres_session),
    current_user: QueryUsers = Depends(get_current_user)
):
    """
    Получает посты из базы данных

    :param skip: Количество постов которые нужно пропустить
    :param limit: Количество постов которые нужно получить
    :param postgres: Сессия для postgres
    :param current_user: Авторизованный текущий пользователь
    :return: Список постов
    """
    result = await postgres.execute(
        select(QueryPosts)
        .where(QueryPosts.username == current_user.username)
        .offset(skip)
        .limit(limit)
    )

    posts = result.scalars().all()

    return posts


@router.get("/count")
async def get_posts_count(
        postgres: AsyncSession = Depends(get_postgres_session),
        current_user: QueryUsers = Depends(get_current_user)
):
    """
    Получает количество постов опубликованных пользователем

    :param postgres: Сессия для postgres
    :param current_user: Авторизованный текущий пользователь
    :return: Количество постов для конкретного пользователя
    """
    result = await postgres.execute(
        select(func.count(QueryPosts.id))
        .where(QueryPosts.username == current_user.username)
    )
    return {"total": result.scalar()}


@router.get("/{post_id}", response_model=PostResponse)
async def read_post(
        post_id: int,
        postgres: AsyncSession = Depends(get_postgres_session),
        current_user: QueryUsers = Depends(get_current_user)
):
    """
    Получает пост из базы данных по id

    :param post_id: Количество постов которые нужно пропустить
    :param postgres: Сессия для postgres
    :param current_user: Авторизованный текущий пользователь
    :return: Пост и информация о нем, id, заголовок, содержимое, дата создания и пользователь
    """
    result = await postgres.execute(
        select(QueryPosts)
        .where(QueryPosts.id == post_id)
        .where(QueryPosts.username == current_user.username)
    )
    post = result.scalar()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/delete/{post_id}")
async def delete_post(
        post_id: int,
        postgres: AsyncSession = Depends(get_postgres_session),
        current_user: UserBase = Depends(get_current_user)
):
    """
    Удаляет пост из базы данных

    :param post_id: Количество постов которые нужно пропустить
    :param postgres: Сессия для postgres
    :param current_user: Объект с авторизированным пользователем, для внесения изменнений в бд
    :return: Сообщение об успешном удалении поста
    """
    result = await postgres.execute(
        select(QueryPosts)
        .where(QueryPosts.id == post_id)
        .where(QueryPosts.username == current_user.username)
    )
    post = result.scalar()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    await postgres.delete(post)
    await postgres.commit()

    return {"status": "success"}
