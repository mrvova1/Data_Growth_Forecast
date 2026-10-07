from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.handlers import router as page_router
from api.rest import router as rest_router

from db.session import async_session_maker
from models.user import User

from services.minio_storage import ensure_bucket

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


async def ensure_lab3_user():
    async with async_session_maker() as db:
        existing = await db.get(User, 1)

        if existing is None:
            db.add(
                User(
                    id=1,
                    username="lab3_creator",
                )
            )

            try:
                await db.commit()

            except IntegrityError:
                await db.rollback()
                raise

        await db.execute(
            text(
                "SELECT setval("
                "pg_get_serial_sequence('users','id'), "
                "COALESCE("
                "(SELECT MAX(id) FROM users), 1"
                "), true)"
            )
        )

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_lab3_user()
    ensure_bucket()

    yield


app = FastAPI(
    title="Прогноз роста объёма данных — ЛР3",
    version="1.0",
    lifespan=lifespan,
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


# Новый REST API
app.include_router(
    rest_router,
    prefix="/api",
)


# Старый HTML-интерфейс
app.include_router(
    page_router,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )