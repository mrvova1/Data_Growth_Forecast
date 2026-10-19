from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps_auth import get_current_user, get_current_user_optional
from db.session import get_db
from models.growth_factor import GrowthFactor
from models.like import Like
from models.user import User
from schemas.service import (
    DraftOut,
    LikeIn,
    PublishIn,
    ServiceOut,
)
from services.minio_storage import delete_object, public_url, put_upload

router = APIRouter(tags=["REST API"])

UTC_NOW = lambda: datetime.now(timezone.utc).replace(tzinfo=None)


def _validate_image(upload: UploadFile) -> None:
    if not upload.filename:
        raise HTTPException(status_code=400)
    if not upload.content_type or not upload.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


def _validate_video(upload: UploadFile) -> None:
    if not upload.filename:
        raise HTTPException(status_code=400)
    if not upload.content_type or not upload.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


async def _service_out(
    gf: GrowthFactor,
    db: AsyncSession,
    user: User | None,
) -> ServiceOut:
    likes_count = (
        await db.scalar(
            select(func.count(Like.id)).where(Like.growth_factor_id == gf.id)
        )
    ) or 0

    liked = None
    if user is not None:
        liked = await db.scalar(
            select(Like.id)
            .where(
                Like.growth_factor_id == gf.id,
                Like.user_id == user.id,
            )
            .limit(1)
        )

    is_creator = 0
    if user is not None and gf.creator_user_id == user.id:
        is_creator = 1

    return ServiceOut(
        id=gf.id,
        growth_factor_name=gf.growth_factor_name,
        growth_factor_description=gf.growth_factor_description,
        growth_factor_status=gf.growth_factor_status,
        image_url=public_url(gf.image_key),
        video_url=public_url(gf.video_key),
        growth_coefficient=gf.growth_coefficient,
        storage_impact_coefficient=gf.storage_impact_coefficient,
        created_at=gf.created_at,
        formed_at=gf.formed_at,
        likes_count=int(likes_count),
        is_creator=is_creator,
        is_liked=int(liked is not None),
    )


def _draft_out(draft: GrowthFactor) -> DraftOut:
    return DraftOut(
        id=draft.id,
        growth_factor_name=draft.growth_factor_name,
        growth_factor_description=draft.growth_factor_description,
        growth_factor_status=draft.growth_factor_status,
        image_url=public_url(draft.image_key),
        video_url=public_url(draft.video_key),
        growth_coefficient=draft.growth_coefficient,
        storage_impact_coefficient=draft.storage_impact_coefficient,
        created_at=draft.created_at,
    )


@router.get("/services", response_model=list[ServiceOut])
async def list_services(
    growth_coefficient_min: float | None = Query(default=None),
    growth_coefficient_max: float | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    if (
        growth_coefficient_min is not None
        and growth_coefficient_max is not None
        and growth_coefficient_min > growth_coefficient_max
    ):
        raise HTTPException(status_code=400)

    stmt = (
        select(GrowthFactor)
        .where(GrowthFactor.growth_factor_status == "опубликован")
        .order_by(GrowthFactor.id.asc())
    )

    if growth_coefficient_min is not None:
        stmt = stmt.where(GrowthFactor.growth_coefficient >= growth_coefficient_min)
    if growth_coefficient_max is not None:
        stmt = stmt.where(GrowthFactor.growth_coefficient <= growth_coefficient_max)

    rows = (await db.execute(stmt)).scalars().all()
    return [await _service_out(gf, db, user) for gf in rows]


@router.post(
    "/services",
    response_model=DraftOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_service(
    growth_factor_name: str = Form(...),
    image_file: UploadFile = File(...),
    video_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    growth_factor_name = growth_factor_name.strip()
    if not growth_factor_name:
        raise HTTPException(status_code=400)

    _validate_image(image_file)
    _validate_video(video_file)

    existing_draft_id = await db.scalar(
        select(GrowthFactor.id)
        .where(
            GrowthFactor.growth_factor_status == "черновик",
            GrowthFactor.creator_user_id == current_user.id,
        )
        .limit(1)
    )
    if existing_draft_id is not None:
        raise HTTPException(status_code=409)

    image_key = None
    video_key = None
    try:
        image_key = put_upload(image_file, "images")
        video_key = put_upload(video_file, "videos")

        draft = GrowthFactor(
            growth_factor_name=growth_factor_name,
            growth_factor_description=None,
            growth_factor_status="черновик",
            image_key=image_key,
            video_key=video_key,
            growth_coefficient=None,
            storage_impact_coefficient=None,
            created_at=UTC_NOW(),
            creator_user_id=current_user.id,
            formed_at=None,
        )
        db.add(draft)
        await db.commit()
        await db.refresh(draft)
        return _draft_out(draft)
    except Exception as exc:
        await db.rollback()
        delete_object(video_key)
        delete_object(image_key)
        raise HTTPException(status_code=502) from exc
    finally:
        await image_file.close()
        await video_file.close()


@router.get("/services/draft", response_model=DraftOut)
async def get_draft(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    draft = (
        await db.execute(
            select(GrowthFactor)
            .where(
                GrowthFactor.growth_factor_status == "черновик",
                GrowthFactor.creator_user_id == current_user.id,
            )
            .order_by(GrowthFactor.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if draft is None:
        raise HTTPException(status_code=404)

    return _draft_out(draft)


@router.put("/services/draft", response_model=ServiceOut)
async def publish_draft(
    payload: PublishIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    draft = (
        await db.execute(
            select(GrowthFactor)
            .where(
                GrowthFactor.growth_factor_status == "черновик",
                GrowthFactor.creator_user_id == current_user.id,
            )
            .order_by(GrowthFactor.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if draft is None:
        raise HTTPException(status_code=404)

    draft.growth_factor_description = payload.growth_factor_description
    draft.growth_coefficient = payload.growth_coefficient
    draft.storage_impact_coefficient = payload.storage_impact_coefficient
    draft.growth_factor_status = "опубликован"
    draft.formed_at = UTC_NOW()

    await db.commit()
    await db.refresh(draft)
    return await _service_out(draft, db, current_user)


@router.get("/services/feed", response_model=ServiceOut)
async def get_feed_first(
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    first = (
        await db.execute(
            select(GrowthFactor)
            .where(GrowthFactor.growth_factor_status == "опубликован")
            .order_by(GrowthFactor.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if first is None:
        raise HTTPException(status_code=404)

    return await _service_out(first, db, user)


@router.get("/services/feed/{service_id}", response_model=ServiceOut)
async def get_feed_by_id(
    service_id: int,
    next: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    if service_id <= 0:
        raise HTTPException(status_code=400)

    if next:
        current = (
            await db.execute(
                select(GrowthFactor)
                .where(
                    GrowthFactor.growth_factor_status == "опубликован",
                    GrowthFactor.id > service_id,
                )
                .order_by(GrowthFactor.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if current is None:
            current = (
                await db.execute(
                    select(GrowthFactor)
                    .where(GrowthFactor.growth_factor_status == "опубликован")
                    .order_by(GrowthFactor.id.asc())
                    .limit(1)
                )
            ).scalar_one_or_none()
    else:
        current = (
            await db.execute(
                select(GrowthFactor).where(
                    GrowthFactor.id == service_id,
                    GrowthFactor.growth_factor_status == "опубликован",
                )
            )
        ).scalar_one_or_none()

    if current is None:
        raise HTTPException(status_code=404)

    return await _service_out(current, db, user)


@router.post("/services/{service_id}/like")
async def set_like(
    service_id: int,
    payload: LikeIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = (
        await db.execute(
            select(GrowthFactor).where(
                GrowthFactor.id == service_id,
                GrowthFactor.growth_factor_status == "опубликован",
            )
        )
    ).scalar_one_or_none()

    if service is None:
        raise HTTPException(status_code=404)

    existing = (
        await db.execute(
            select(Like)
            .where(
                Like.user_id == current_user.id,
                Like.growth_factor_id == service_id,
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    if payload.like == 1 and existing is None:
        db.add(Like(user_id=current_user.id, growth_factor_id=service_id))
    elif payload.like == 0 and existing is not None:
        await db.delete(existing)

    await db.commit()

    is_liked = (
        await db.scalar(
            select(Like.id).where(
                Like.user_id == current_user.id,
                Like.growth_factor_id == service_id,
            )
        )
        is not None
    )
    likes_count = (
        await db.scalar(
            select(func.count(Like.id)).where(Like.growth_factor_id == service_id)
        )
    ) or 0

    return {
        "like": int(is_liked),
        "likes_count": int(likes_count),
    }


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = await db.get(GrowthFactor, service_id)

    if service is None or service.creator_user_id != current_user.id:
        raise HTTPException(status_code=404)

    if service.growth_factor_status != "удален":
        service.growth_factor_status = "удален"
        await db.commit()

    return None
