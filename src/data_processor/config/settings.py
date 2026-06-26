"""Application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    processor_env: str = Field(default="development", validation_alias="PROCESSOR_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+psycopg://user:password@localhost:5432/kilo_hoku",
        validation_alias="DATABASE_URL",
    )
    database_schema: str = Field(default="astronomy", validation_alias="DATABASE_SCHEMA")
    poll_interval_seconds: int = Field(default=30, validation_alias="POLL_INTERVAL_SECONDS")
    worker_id: str = Field(default="local-worker", validation_alias="WORKER_ID")
    job_batch_size: int = Field(default=10, validation_alias="JOB_BATCH_SIZE")
    processing_chunk_size: int = Field(default=50_000, validation_alias="PROCESSING_CHUNK_SIZE")
    temp_dir: str = Field(default="./tmp", validation_alias="TEMP_DIR")
    local_light_curves_path: str = Field(
        default=r"C:\UPC\TFG\TFG_Victor\light_curves",
        validation_alias="LOCAL_LIGHT_CURVES_PATH",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
