from pydantic_settings import BaseSettings
from pydantic import Field


class SettingsConfig(BaseSettings):
    POSTGRES_HOST: str = ''
    POSTGRES_PORT: str = '5432'
    POSTGRES_USER: str = ''
    POSTGRES_DB: str = 'posts'
    POSTGRES_PASSWORD: str = ''

    REDIS_HOST: str = ''
    REDIS_PORT: str = '6379'
    REDIS_DB: int = 0
    REDIS_CACHE_TTL: int = 3600

    SECRET_KEY: str = Field(default='admin', min_length=5)
    ALGORITHM: str = Field(default='HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)


    @property
    def postgres_url(self):
        return (f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:'
                f'{self.POSTGRES_PORT}/{self.POSTGRES_DB}')


    @property
    def redis_url(self):
        return f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'


settings = SettingsConfig()
