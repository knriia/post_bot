from contextlib import asynccontextmanager
from fastapi import FastAPI

from database import async_engine, create_tables


@asynccontextmanager
async def startup(app: FastAPI):
    await create_tables()
    yield
    await async_engine.dispose()


app = FastAPI(lifespan=startup)


from routes import users, posts


app.include_router(users.router)
app.include_router(posts.router)
