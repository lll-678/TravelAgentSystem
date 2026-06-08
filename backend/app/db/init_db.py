from sqlalchemy import Engine
from sqlalchemy import inspect, text

from app.db.base import Base
from app.models import *  # noqa: F401,F403


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    ensure_compatible_schema(engine)


def drop_all(engine: Engine) -> None:
    Base.metadata.drop_all(bind=engine)


def ensure_compatible_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    with engine.begin() as connection:
        if "users" in table_names:
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            if "role" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'"))
        if "restaurants" in table_names:
            restaurant_columns = {column["name"] for column in inspector.get_columns("restaurants")}
            if "destination_id" not in restaurant_columns:
                connection.execute(text("ALTER TABLE restaurants ADD COLUMN destination_id INTEGER"))
