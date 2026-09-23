from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from db.base import Base


class GrowthFactor(Base):
    __tablename__ = "growth_factors"
    id = Column(Integer, primary_key=True, index=True)
    growth_factor_name = Column(String(100), nullable=False)
    growth_factor_description = Column(String(500), nullable=True)
    growth_factor_status = Column(
        String(20),
        nullable=False,
        default="черновик"
    )
    image_key = Column(String(255), nullable=True)
    video_key = Column(String(255), nullable=True)
    growth_coefficient = Column(Float, nullable=True)
    storage_impact_coefficient = Column(Float, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False
    )
    creator_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    formed_at = Column(
        DateTime,
        nullable=True
    )
