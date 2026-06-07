"""
Моделі для міських метрик та престижу районів.
Файл: backend/app/models/city_metrics.py
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy import (
    Numeric as Decimal,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from backend.app.models import Business, City, CityDistrict, Player


class CityMetrics(Base):
    """Динамічні показники міста що змінюються залежно від діяльності гравців."""

    __tablename__ = "city_metrics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Економічні метрики
    gdp_per_capita: Mapped[float] = mapped_column(Decimal(15, 2), default=1000.00)
    unemployment_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=10.00)
    business_density: Mapped[float] = mapped_column(Decimal(5, 2), default=5.00)  # бізнесів на 1000 мешканців
    startup_success_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=60.00)
    average_business_profit: Mapped[float] = mapped_column(Decimal(15, 2), default=500.00)

    # Соціальні метрики
    crime_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=5.00)
    happiness_index: Mapped[float] = mapped_column(Decimal(5, 2), default=70.00)
    education_level: Mapped[float] = mapped_column(Decimal(5, 2), default=60.00)
    social_mobility: Mapped[float] = mapped_column(Decimal(5, 2), default=50.00)

    # Інфраструктурні метрики
    infrastructure_quality: Mapped[float] = mapped_column(Decimal(5, 2), default=70.00)
    traffic_index: Mapped[float] = mapped_column(Decimal(5, 2), default=50.00)
    environmental_score: Mapped[float] = mapped_column(Decimal(5, 2), default=75.00)

    # Ринкові показники
    inflation_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=2.00)
    property_price_index: Mapped[float] = mapped_column(Decimal(5, 2), default=100.00)
    consumer_spending: Mapped[float] = mapped_column(Decimal(15, 2), default=50000.00)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="metrics")


class DistrictPrestige(Base):
    """Престиж та характеристики районів міста."""

    __tablename__ = "district_prestige"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("city_districts.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Бізнес-клімат
    business_friendly_rating: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)  # 1-10
    tax_incentives: Mapped[float] = mapped_column(Decimal(5, 2), default=0.00)  # % знижки податків
    development_level: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)  # 1-10

    # Соціальний статус
    prestige_level: Mapped[int] = mapped_column(Integer, default=3)  # 1-10
    safety_rating: Mapped[float] = mapped_column(Decimal(5, 2), default=7.0)
    cultural_significance: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    # Інфраструктура
    transport_access: Mapped[float] = mapped_column(Decimal(5, 2), default=6.0)
    utility_quality: Mapped[float] = mapped_column(Decimal(5, 2), default=7.0)
    green_spaces: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    # Економічні показники
    average_property_value: Mapped[float] = mapped_column(Decimal(15, 2), default=50000.00)
    commercial_rent_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=10.00)
    foot_traffic_index: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Зв'язки ORM
    district: Mapped["CityDistrict"] = relationship("CityDistrict", back_populates="prestige")


class PlayerInteraction(Base):
    """Логи взаємодій між гравцями."""

    __tablename__ = "player_interactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player1_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    player2_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)

    interaction_type: Mapped[str] = mapped_column(String(20))  # competition/partnership/investment/conflict
    business_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id"))

    impact_score: Mapped[float] = mapped_column(Decimal(5, 2))  # -10 до +10
    relationship_change: Mapped[float] = mapped_column(Decimal(5, 2))  # зміна відносин
    amount_involved: Mapped[float | None] = mapped_column(Decimal(15, 2))  # сума угоди

    description: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player1: Mapped["Player"] = relationship("Player", foreign_keys=[player1_id])
    player2: Mapped["Player"] = relationship("Player", foreign_keys=[player2_id])
    business: Mapped[Optional["Business"]] = relationship("Business")


class PlayerBusinessRating(Base):
    """Рейтинг гравця в бізнес-спільноті."""

    __tablename__ = "player_business_ratings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Бізнес-показники
    total_businesses: Mapped[int] = mapped_column(Integer, default=0)
    successful_startups: Mapped[int] = mapped_column(Integer, default=0)
    failed_businesses: Mapped[int] = mapped_column(Integer, default=0)
    total_employees: Mapped[int] = mapped_column(Integer, default=0)

    # Соціальний статус
    business_reputation: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)  # 1-10
    influence_level: Mapped[int] = mapped_column(Integer, default=1)  # 1-10
    trust_score: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    # Економічний вплив
    city_contribution: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    employment_created: Mapped[int] = mapped_column(Integer, default=0)
    taxes_paid: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)

    # Інвестиційна активність
    total_investments: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    investment_returns: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    portfolio_value: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="business_rating")


class CityEvent(Base):
    """Динамічні події в місті що впливають на бізнес."""

    __tablename__ = "city_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000))
    event_type: Mapped[str] = mapped_column(String(30))  # festival/crisis/construction/celebration

    # Вплив на метрики
    business_revenue_modifier: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)  # множник доходу
    employment_modifier: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)  # множник зайнятості
    crime_rate_modifier: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)  # множник криміналу

    # Часові параметри
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_days: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Цільові параметри
    affected_districts: Mapped[dict] = mapped_column(JSON, default=list)  # ID районів
    affected_business_types: Mapped[dict] = mapped_column(JSON, default=list)  # типи бізнесу

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="events")
