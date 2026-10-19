import uuid
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps_auth import get_current_user
from db.session import get_db
from models.user import User
from schemas.service import UserLoginIn, UserOut, UserRegisterIn
from services.password import hash_password, verify_password
from services.redis_client import get_redis

router = APIRouter(tags=["Пользователи"])

SESSION_TTL_SECONDS = 86400


@router.post(
    "/users/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Создаёт нового пользователя. Пароль хешируется алгоритмом bcrypt.",
)
async def register(
    payload: UserRegisterIn,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(
        select(User).where(User.username == payload.username)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Пользователь уже существует")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Пользователь уже существует")
    await db.refresh(user)
    return UserOut(id=user.id, username=user.username)


@router.post(
    "/users/login",
    summary="Вход в систему",
    description=(
        "Проверяет логин и пароль, создаёт сессию в Redis "
        "и устанавливает HttpOnly-куку `session_id`."
    ),
)
async def login(
    payload: UserLoginIn,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(
        select(User).where(User.username == payload.username)
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    session_id = str(uuid.uuid4())
    redis = get_redis()
    await redis.setex(f"session:{session_id}", SESSION_TTL_SECONDS, str(user.id))

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=SESSION_TTL_SECONDS,
        samesite="lax",
        secure=False,
    )
    return {"message": "Вход выполнен"}


@router.post(
    "/users/logout",
    summary="Выход из системы",
    description="Удаляет сессию из Redis и очищает куку.",
)
async def logout(
    response: Response,
    session_id: str | None = Cookie(default=None),
):
    if session_id:
        redis = get_redis()
        await redis.delete(f"session:{session_id}")
    response.delete_cookie("session_id")
    return {"message": "Выход выполнен"}


@router.get(
    "/users/me",
    response_model=UserOut,
    summary="Текущий пользователь",
    description="Возвращает данные авторизованного пользователя.",
)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut(id=current_user.id, username=current_user.username)
