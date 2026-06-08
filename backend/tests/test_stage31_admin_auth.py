import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.admin import router as admin_router
from app.api.v1.users import UserLoginRequest, get_current_user_model, login_user, require_admin
from app.db.init_db import create_all
from app.seed.seed_all import seed_demo_data


def test_seeded_user_and_admin_roles_are_distinct() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        user_login = login_user(UserLoginRequest(username_or_email="user01", password="demo123456"), session)
        admin_login = login_user(UserLoginRequest(username_or_email="admin01", password="admin123456"), session)

    assert user_login["role"] == "user"
    assert user_login["user"]["role"] == "user"
    assert admin_login["role"] == "admin"
    assert admin_login["user"]["role"] == "admin"


def test_admin_dependency_rejects_missing_and_normal_user_tokens() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)

    with Session(engine) as session:
        seed_demo_data(session)
        user_token = login_user(UserLoginRequest(username_or_email="user01", password="demo123456"), session)[
            "access_token"
        ]
        admin_token = login_user(UserLoginRequest(username_or_email="admin01", password="admin123456"), session)[
            "access_token"
        ]

        with pytest.raises(HTTPException) as missing:
            get_current_user_model(None, session)

        user = get_current_user_model(f"Bearer {user_token}", session)
        admin = get_current_user_model(f"Bearer {admin_token}", session)

        with pytest.raises(HTTPException) as forbidden:
            require_admin(user)

        allowed = require_admin(admin)

    assert missing.value.status_code == 401
    assert forbidden.value.status_code == 403
    assert user.role == "user"
    assert allowed.role == "admin"


def test_admin_router_is_guarded_by_require_admin_dependency() -> None:
    assert any(dependency.dependency is require_admin for dependency in admin_router.dependencies)
