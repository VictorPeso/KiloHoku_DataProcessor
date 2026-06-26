"""SQLAlchemy engine factory."""

from sqlalchemy import Engine, create_engine

from data_processor.config.settings import Settings, get_settings


def create_database_engine(settings: Settings | None = None) -> Engine:
    resolved_settings = settings or get_settings()
    return create_engine(resolved_settings.database_url, pool_pre_ping=True)
