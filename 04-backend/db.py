from collections.abc import Iterator
from datetime import datetime

from sqlalchemy import DateTime, MetaData, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings


NAMING_CONVENTION = {
    "ix": "%(table_name)s_%(column_0_N_name)s_idx",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {str: Text, datetime: DateTime(timezone=True)}


engine = create_engine(settings.database_url, echo=settings.sql_echo)
SessionLocal = sessionmaker(engine)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
