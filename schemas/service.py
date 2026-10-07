from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    growth_factor_name: str
    growth_factor_description: str | None = None
    growth_factor_status: str

    image_url: str | None = None
    video_url: str | None = None

    growth_coefficient: float | None = None
    storage_impact_coefficient: float | None = None

    created_at: datetime
    formed_at: datetime | None = None

    likes_count: int = 0
    is_creator: int = Field(ge=0, le=1)
    is_liked: int = Field(ge=0, le=1)


class DraftOut(BaseModel):
    id: int
    growth_factor_name: str
    growth_factor_description: str | None = None
    growth_factor_status: str

    image_url: str | None = None
    video_url: str | None = None

    growth_coefficient: float | None = None
    storage_impact_coefficient: float | None = None

    created_at: datetime


class PublishIn(BaseModel):
    growth_factor_description: str = Field(
        min_length=1,
        max_length=500
    )

    growth_coefficient: float = Field(
        ge=1.0,
        le=2.0
    )

    storage_impact_coefficient: float = Field(
        ge=0.0,
        le=2.0
    )

    @field_validator("growth_factor_description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Описание не должно быть пустым")

        return value


class LikeIn(BaseModel):
    like: int = Field(ge=0, le=1)


class UserRegisterIn(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Логин не должен быть пустым")

        return value


class UserOut(BaseModel):
    id: int
    username: str