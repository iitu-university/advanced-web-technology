"""Login and authentication dependencies for REST and GraphQL."""

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import get_db
from models import User
from schemas import Token
from security import DUMMY_HASH, create_access_token, password_hash, read_access_token

SessionDep = Annotated[Session, Depends(get_db)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
router = APIRouter(prefix="/auth", tags=["auth"])


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    hashed = user.password_hash if user else DUMMY_HASH
    valid = password_hash.verify(password, hashed)
    return user if valid else None


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessionDep, response: Response):
    user = authenticate(db, form.username, form.password)
    if user is None:
        raise unauthorized("Incorrect email or password")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return Token(access_token=create_access_token(user.id))


def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)], db: SessionDep
) -> User | None:
    if token is None:
        return None
    try:
        user_id = read_access_token(token)
    except jwt.InvalidTokenError:
        raise unauthorized("Invalid or expired token") from None

    user = db.get(User, user_id)
    if user is None:
        raise unauthorized("Invalid or expired token")
    return user


def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise unauthorized("Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
