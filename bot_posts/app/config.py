from pydantic_settings import BaseSettings


class SettingsConfig(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ''
    API_URL: str = ''


settings = SettingsConfig()
