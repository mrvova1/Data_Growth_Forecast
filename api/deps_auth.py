from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.user import User
from services.redis_client import get_redis

async def get_current_user_optional(
    session_id: str | None = Cookie(default=None, alias="session_id"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not session_id:
        return None
    redis = get_redis()
    user_id = await redis.get(f"session:{session_id}")
    if not user_id:
        return None
    user = await db.get(User, int(user_id))
    return user

async def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
        )
    return user
