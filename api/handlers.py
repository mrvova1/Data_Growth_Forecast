from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates

from data.collections import growth_factors_collection

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def _published_growth_factors():
    return [
        growth_factor
        for growth_factor in growth_factors_collection
        if growth_factor["growth_factor_status"] == "опубликован"
    ]


def _get_published_growth_factor(growth_factor_id: int):
    growth_factor = next(
        (
            item
            for item in growth_factors_collection
            if item["id"] == growth_factor_id and item["growth_factor_status"] == "опубликован"
        ),
        None,
    )
    if growth_factor is None:
        raise HTTPException(status_code=404, detail="Фактор роста не найден")
    return growth_factor


def _prepare_growth_factor(growth_factor: dict) -> dict:
    prepared = growth_factor.copy()
    prepared["likes_count"] = len(prepared["like_user_ids"])
    prepared["image_url"] = f"http://localhost:9000/media/{prepared['image_key']}"
    prepared["video_url"] = f"http://localhost:9000/media/{prepared['video_key']}"
    return prepared

@router.get("/")
@router.get("/growth-factors")
def get_growth_factors(
    request: Request,
    growth_coefficient_min: Optional[float] = Query(default=None),
):
    visible_growth_factors = _published_growth_factors()

    if growth_coefficient_min is not None:
        visible_growth_factors = [
            growth_factor
            for growth_factor in visible_growth_factors
            if growth_factor["growth_coefficient"] >= growth_coefficient_min
        ]

    return templates.TemplateResponse(
        request=request,
        name="growth_factors.html",
        context={
            "growth_factors": [
                _prepare_growth_factor(growth_factor)
                for growth_factor in visible_growth_factors
            ],
            "growth_coefficient_min": growth_coefficient_min,
        },
    )

@router.get("/growth-factor/{growth_factor_id:int}")
@router.get("/growth-factor/")
def get_growth_factor(
    request: Request,
    growth_factor_id: Optional[int] = None,
    go_next: bool = Query(default=False, alias="next"),
):
    if not growth_factor_id:
        published_growth_factors = _published_growth_factors()
        if not published_growth_factors:
            raise HTTPException(status_code=404, detail="Опубликованные факторы роста не найдены")
        growth_factor_id = published_growth_factors[0]["id"]

    current_growth_factor = _get_published_growth_factor(growth_factor_id)

    published_growth_factors = _published_growth_factors()
    current_position = next(
        index
        for index, item in enumerate(published_growth_factors)
        if item["id"] == current_growth_factor["id"]
    )

    displayed_growth_factor = current_growth_factor
    print(len(published_growth_factors))
    print((current_position + 1))
    if go_next:
        next_position = (current_position + 1) % len(published_growth_factors)
        displayed_growth_factor = published_growth_factors[next_position]

    return templates.TemplateResponse(
        request=request,
        name="growth_factor.html",
        context={"growth_factor": _prepare_growth_factor(displayed_growth_factor)},
    )


@router.get("/growth-factor-draft")
def get_growth_factor_draft(request: Request):
    draft_growth_factor = next(
        (
            item
            for item in growth_factors_collection
            if item["growth_factor_status"] == "черновик"
        ),
        None,
    )
    if draft_growth_factor is None:
        raise HTTPException(status_code=404, detail="Черновик фактора роста не найден")

    return templates.TemplateResponse(
        request=request,
        name="growth_factor_draft.html",
        context={"growth_factor": _prepare_growth_factor(draft_growth_factor)},
    )
