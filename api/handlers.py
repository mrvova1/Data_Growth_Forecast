import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.user import User
from models.growth_factor import GrowthFactor
from models.like import Like

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DEFAULT_IMAGE = "/static/images/default.png"
DEFAULT_VIDEO = "/static/videos/default.mp4"
# Временно creator_user_id=1

# DEFAULT_IMAGE = "http://localhost:9000/media/operations_frequency.png"
# DEFAULT_VIDEO = "http://localhost:9000/media/operations_frequency.mp4"

async def _prepare_growth_factor(growth_factor: GrowthFactor, db: AsyncSession) -> GrowthFactor:
    """Вспомогательный метод для подсчета лайков и настройки медиа-ссылок по умолчанию"""
    stmt = select(func.count(Like.id)).where(Like.growth_factor_id == growth_factor.id)
    result = await db.execute(stmt)
    growth_factor.likes_count = result.scalar_one()

    if not growth_factor.image_key or growth_factor.image_key.strip() == "":
        growth_factor.image_url = DEFAULT_IMAGE
    else:
        growth_factor.image_url = f"http://localhost:9000/media/{growth_factor.image_key}"

    if not growth_factor.video_key or growth_factor.video_key.strip() == "":
        growth_factor.video_url = DEFAULT_VIDEO
    else:
        growth_factor.video_url = f"http://localhost:9000/media/{growth_factor.video_key}"

    return growth_factor

@router.get("/")
@router.get("/growth-factors")
async def get_growth_factors(
    request: Request,
    db: AsyncSession = Depends(get_db),
    growth_coefficient_min: Optional[float] = Query(default=None),
    growth_coefficient_max: Optional[float] = Query(default=None),
):
    stmt = select(GrowthFactor).where(GrowthFactor.growth_factor_status == "опубликован")

    if growth_coefficient_min is not None:
        stmt = stmt.where(GrowthFactor.growth_coefficient >= growth_coefficient_min)
    if growth_coefficient_max is not None:
        stmt = stmt.where(GrowthFactor.growth_coefficient <= growth_coefficient_max)

    stmt = stmt.order_by(GrowthFactor.id.asc())
    result = await db.execute(stmt)
    visible_growth_factors = result.scalars().all()

    prepared_list = []
    for gf in visible_growth_factors:
        prepared_list.append(await _prepare_growth_factor(gf, db))

    return templates.TemplateResponse(
        request=request,
        name="growth_factors.html",
        context={
            "growth_factors": prepared_list,
            "growth_coefficient_min": growth_coefficient_min,
            "growth_coefficient_max": growth_coefficient_max,
        },
    )


@router.get("/growth-factor/{growth_factor_id:int}")
@router.get("/growth-factor/")
async def get_growth_factor(
    request: Request,
    db: AsyncSession = Depends(get_db),
    growth_factor_id: Optional[int] = None,
    go_next: bool = Query(default=False, alias="next"),
):
    if not growth_factor_id:
        stmt = select(GrowthFactor).where(GrowthFactor.growth_factor_status == "опубликован").limit(1)
        res = await db.execute(stmt)
        current_gf = res.scalar_one_or_none()
        if not current_gf:
            raise HTTPException(status_code=404, detail="Опубликованные факторы роста не найдены")
        growth_factor_id = current_gf.id

    if go_next:
        stmt_next = (
            select(GrowthFactor)
            .where(GrowthFactor.growth_factor_status == "опубликован")
            .where(GrowthFactor.id > growth_factor_id)
            .order_by(GrowthFactor.id.asc())
            .limit(1)
        )
        res_next = await db.execute(stmt_next)
        displayed_growth_factor = res_next.scalar_one_or_none()

        if not displayed_growth_factor:
            stmt_first = (
                select(GrowthFactor)
                .where(GrowthFactor.growth_factor_status == "опубликован")
                .order_by(GrowthFactor.id.asc())
                .limit(1)
            )
            res_first = await db.execute(stmt_first)
            displayed_growth_factor = res_first.scalar_one_or_none()
    else:
        stmt_curr = select(GrowthFactor).where(GrowthFactor.id == growth_factor_id)
        res_curr = await db.execute(stmt_curr)
        displayed_growth_factor = res_curr.scalar_one_or_none()

    if not displayed_growth_factor or displayed_growth_factor.growth_factor_status == "удален":
        raise HTTPException(status_code=404, detail="Фактор роста не найден или удален")

    await _prepare_growth_factor(displayed_growth_factor, db)

    return templates.TemplateResponse(
        request=request,
        name="growth_factor.html",
        context={"growth_factor": displayed_growth_factor},
    )


@router.get("/growth-factor-draft")
async def get_growth_factor_draft(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(GrowthFactor).where(
        GrowthFactor.growth_factor_status == "черновик",
        GrowthFactor.creator_user_id == 1
    ).limit(1)

    result = await db.execute(stmt)
    draft_growth_factor = result.scalar_one_or_none()

    if draft_growth_factor:
        await _prepare_growth_factor(draft_growth_factor, db)
        return templates.TemplateResponse(
            request=request,
            name="growth_factor_draft.html",
            context={"growth_factor": draft_growth_factor, "is_exist": True},
        )

    return templates.TemplateResponse(
        request=request,
        name="growth_factor_draft.html",
        context={"growth_factor": None, "is_exist": False},
    )


@router.post("/growth-factor/create")
async def create_growth_factor_post(
    growth_factor_name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(GrowthFactor).where(
        GrowthFactor.growth_factor_status == "черновик",
        GrowthFactor.creator_user_id == 1
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return RedirectResponse(url="/growth-factor-draft", status_code=status.HTTP_303_SEE_OTHER)

    new_draft = GrowthFactor(
        growth_factor_name=growth_factor_name,
        growth_factor_status="черновик",
        created_at=datetime.datetime.now(),
        creator_user_id=1,
        image_key="",
        video_key=""
    )
    db.add(new_draft)
    await db.commit()

    return RedirectResponse(url="/growth-factor-draft", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/growth-factor/publish")
async def publish_growth_factor_post(
    growth_factor_description: str = Form(...),
    growth_coefficient: float = Form(...),
    storage_impact_coefficient: float = Form(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(GrowthFactor).where(
        GrowthFactor.growth_factor_status == "черновик",
        GrowthFactor.creator_user_id == 1
    )
    result = await db.execute(stmt)
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(status_code=404, detail="Черновик для публикации не найден")

    draft.growth_factor_description = growth_factor_description
    draft.growth_coefficient = growth_coefficient
    draft.storage_impact_coefficient = storage_impact_coefficient
    draft.growth_factor_status = "опубликован"
    draft.formed_at = datetime.datetime.now()

    await db.commit()
    return RedirectResponse(url="/growth-factors", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/growth-factor/delete")
async def delete_growth_factor_post(
    growth_factor_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):

    sql_query = text(
        "UPDATE growth_factors "
        "SET growth_factor_status = 'удален' "
        "WHERE id = :gf_id"
    )

    await db.execute(sql_query, {"gf_id": growth_factor_id})
    await db.commit()

    return RedirectResponse(url="/growth-factors", status_code=status.HTTP_303_SEE_OTHER)
