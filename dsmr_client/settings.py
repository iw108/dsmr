from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TCP_HOST: str
    TCP_PORT: int

    INFLUXDB_BUCKET: str
    INFLUXDB_ORG: str
    INFLUXDB_TOKEN: str
    INFLUXDB_URL: AnyHttpUrl

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
