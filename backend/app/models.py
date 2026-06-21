# Моделі бази даних SQLAlchemy для MVP Економічного Симулятора
# Файл: backend/app/models.py

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Numeric as Decimal,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# === МОДЕЛІ МІСЬКИХ МЕТРИК ТА ПРЕСТИЖУ ===
class CityMetrics(Base):
    """Динамічні показники міста"""

    __tablename__ = "city_metrics"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, unique=True)

    gdp_per_capita: Mapped[float] = mapped_column(Decimal(15, 2), default=1000.00)
    unemployment_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=10.00)
    business_density: Mapped[float] = mapped_column(Decimal(5, 2), default=5.00)
    startup_success_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=60.00)
    average_business_profit: Mapped[float] = mapped_column(Decimal(15, 2), default=500.00)

    crime_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=5.00)
    happiness_index: Mapped[float] = mapped_column(Decimal(5, 2), default=70.00)
    education_level: Mapped[float] = mapped_column(Decimal(5, 2), default=60.00)
    social_mobility: Mapped[float] = mapped_column(Decimal(5, 2), default=50.00)

    infrastructure_quality: Mapped[float] = mapped_column(Decimal(5, 2), default=70.00)
    traffic_index: Mapped[float] = mapped_column(Decimal(5, 2), default=50.00)
    environmental_score: Mapped[float] = mapped_column(Decimal(5, 2), default=75.00)

    inflation_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=2.00)
    property_price_index: Mapped[float] = mapped_column(Decimal(5, 2), default=100.00)
    consumer_spending: Mapped[float] = mapped_column(Decimal(15, 2), default=50000.00)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    city: Mapped["City"] = relationship("City", back_populates="metrics")


class CityEconomySnapshot(Base):
    """Daily active-money snapshot used for inflation and balance diagnostics."""

    __tablename__ = "city_economy_snapshots"
    __table_args__ = (
        UniqueConstraint("city_id", "game_day", name="uq_city_economy_snapshots_city_day"),
        Index("ix_city_economy_snapshots_city_day", "city_id", "game_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    game_day: Mapped[int] = mapped_column(Integer, nullable=False)

    active_money_supply: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    previous_active_money_supply: Mapped[float | None] = mapped_column(Decimal(15, 2))
    target_growth_rate: Mapped[float] = mapped_column(Decimal(6, 4), nullable=False, default=0.0300)
    money_growth_rate: Mapped[float] = mapped_column(Decimal(8, 4), nullable=False, default=0.0000)
    inflation_rate: Mapped[float] = mapped_column(Decimal(5, 2), nullable=False, default=0.00)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped["City"] = relationship("City", back_populates="economy_snapshots")


class DistrictPrestige(Base):
    """Престиж та характеристики районів міста"""

    __tablename__ = "district_prestige"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("city_districts.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    business_friendly_rating: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)
    tax_incentives: Mapped[float] = mapped_column(Decimal(5, 2), default=0.00)
    development_level: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    prestige_level: Mapped[int] = mapped_column(Integer, default=3)
    safety_rating: Mapped[float] = mapped_column(Decimal(5, 2), default=7.0)
    cultural_significance: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    transport_access: Mapped[float] = mapped_column(Decimal(5, 2), default=6.0)
    utility_quality: Mapped[float] = mapped_column(Decimal(5, 2), default=7.0)
    green_spaces: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    average_property_value: Mapped[float] = mapped_column(Decimal(15, 2), default=50000.00)
    commercial_rent_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=10.00)
    foot_traffic_index: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    district: Mapped["CityDistrict"] = relationship("CityDistrict", back_populates="prestige")


class PlayerInteraction(Base):
    """Логи взаємодій між гравцями"""

    __tablename__ = "player_interactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player1_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    player2_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)

    interaction_type: Mapped[str] = mapped_column(String(20))
    business_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id"))

    impact_score: Mapped[float] = mapped_column(Decimal(5, 2))
    relationship_change: Mapped[float] = mapped_column(Decimal(5, 2))
    amount_involved: Mapped[float | None] = mapped_column(Decimal(15, 2))

    description: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    player1: Mapped["Player"] = relationship("Player", foreign_keys=[player1_id])
    player2: Mapped["Player"] = relationship("Player", foreign_keys=[player2_id])
    business: Mapped[Optional["Business"]] = relationship("Business")


class PlayerBusinessRating(Base):
    """Рейтинг гравця в бізнес-спільноті"""

    __tablename__ = "player_business_ratings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    total_businesses: Mapped[int] = mapped_column(Integer, default=0)
    successful_startups: Mapped[int] = mapped_column(Integer, default=0)
    failed_businesses: Mapped[int] = mapped_column(Integer, default=0)
    total_employees: Mapped[int] = mapped_column(Integer, default=0)

    business_reputation: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)
    influence_level: Mapped[int] = mapped_column(Integer, default=1)
    trust_score: Mapped[float] = mapped_column(Decimal(5, 2), default=5.0)

    city_contribution: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    employment_created: Mapped[int] = mapped_column(Integer, default=0)
    taxes_paid: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)

    total_investments: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    investment_returns: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    portfolio_value: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    player: Mapped["Player"] = relationship("Player", back_populates="business_rating")


class CityEvent(Base):
    """Динамічні події в місті"""

    __tablename__ = "city_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000))
    event_type: Mapped[str] = mapped_column(String(30))

    business_revenue_modifier: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)
    employment_modifier: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)
    crime_rate_modifier: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_days: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    affected_districts: Mapped[dict] = mapped_column(JSON, default=list)
    affected_business_types: Mapped[dict] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped["City"] = relationship("City", back_populates="events")


# 1. МОДЕЛЬ МІСТА (СЕРВЕРА)
class City(Base):
    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    treasury_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=50000.00)
    tax_rate_income: Mapped[float] = mapped_column(Decimal(5, 2), default=10.00)
    tax_rate_property: Mapped[float] = mapped_column(Decimal(5, 2), default=2.00)
    inflation_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=0.00)
    game_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    mayor_player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "players.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_cities_mayor_player_id",
        )
    )
    mayor_term_started_game_day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Зв'язки ORM
    players: Mapped[list["Player"]] = relationship("Player", back_populates="city", foreign_keys="Player.city_id")
    businesses: Mapped[list["Business"]] = relationship("Business", back_populates="city")
    mayor: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[mayor_player_id], post_update=True)
    transactions: Mapped[list["TransactionModelLog"]] = relationship("TransactionModelLog", back_populates="city")
    districts: Mapped[list["CityDistrict"]] = relationship(
        "CityDistrict",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    land_parcels: Mapped[list["LandParcel"]] = relationship(
        "LandParcel",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    building_applications: Mapped[list["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    buildings: Mapped[list["Building"]] = relationship(
        "Building",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    metrics: Mapped[Optional["CityMetrics"]] = relationship("CityMetrics", back_populates="city", uselist=False)
    economy_snapshots: Mapped[list["CityEconomySnapshot"]] = relationship(
        "CityEconomySnapshot",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["CityEvent"]] = relationship("CityEvent", back_populates="city", cascade="all, delete-orphan")


class CityDistrict(Base):
    __tablename__ = "city_districts"
    __table_args__ = (UniqueConstraint("city_id", "code", name="uq_city_districts_city_code"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    zone_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    land_available_hectares: Mapped[float] = mapped_column(Decimal(10, 2), default=0.00)
    rent_level: Mapped[int] = mapped_column(Integer, default=0)
    job_supply: Mapped[int] = mapped_column(Integer, default=0)
    crime_risk: Mapped[int] = mapped_column(Integer, default=0)
    traffic: Mapped[int] = mapped_column(Integer, default=0)
    service_coverage: Mapped[int] = mapped_column(Integer, default=0)
    medical_coverage: Mapped[int] = mapped_column(Integer, default=0)
    land_value: Mapped[int] = mapped_column(Integer, default=0)
    desirability: Mapped[int] = mapped_column(Integer, default=0)
    # Post-MVP dynamic metrics (Phase G1). Float for finer granularity; default 50.0.
    pollution: Mapped[float] = mapped_column(Float, default=50.0)
    education_coverage: Mapped[float] = mapped_column(Float, default=50.0)
    fire_safety: Mapped[float] = mapped_column(Float, default=50.0)
    power_supply: Mapped[float] = mapped_column(Float, default=50.0)
    water_supply: Mapped[float] = mapped_column(Float, default=50.0)
    waste_management: Mapped[float] = mapped_column(Float, default=50.0)
    population: Mapped[float] = mapped_column(Float, default=50.0)
    housing_capacity: Mapped[float] = mapped_column(Float, default=50.0)
    green_space: Mapped[float] = mapped_column(Float, default=50.0)
    happiness: Mapped[float] = mapped_column(Float, default=50.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped["City"] = relationship("City", back_populates="districts")
    land_parcels: Mapped[list["LandParcel"]] = relationship(
        "LandParcel",
        back_populates="district",
        cascade="all, delete-orphan",
    )
    building_applications: Mapped[list["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="district",
        cascade="all, delete-orphan",
    )
    buildings: Mapped[list["Building"]] = relationship(
        "Building",
        back_populates="district",
        cascade="all, delete-orphan",
    )
    prestige: Mapped[Optional["DistrictPrestige"]] = relationship(
        "DistrictPrestige", back_populates="district", uselist=False
    )


class LandParcel(Base):
    __tablename__ = "land_parcels"
    __table_args__ = (UniqueConstraint("city_id", "code", name="uq_land_parcels_city_code"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    district_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("city_districts.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(70), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    land_type: Mapped[str] = mapped_column(String(50), nullable=False)
    zoning_type: Mapped[str] = mapped_column(String(50), nullable=False)
    area_hectares: Mapped[float] = mapped_column(Decimal(10, 2), nullable=False)
    base_price_per_hectare: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    current_price: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="city_owned")
    owner_player_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped["City"] = relationship("City", back_populates="land_parcels")
    district: Mapped["CityDistrict"] = relationship("CityDistrict", back_populates="land_parcels")
    owner: Mapped[Optional["Player"]] = relationship("Player", back_populates="land_parcels")
    building_applications: Mapped[list["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="land_parcel",
        cascade="all, delete-orphan",
    )
    building: Mapped[Optional["Building"]] = relationship("Building", back_populates="land_parcel", uselist=False)


class BuildingApplication(Base):
    __tablename__ = "building_applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    district_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("city_districts.id", ondelete="CASCADE"), nullable=False)
    land_parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("land_parcels.id", ondelete="CASCADE"), nullable=False)
    business_blueprint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("business_blueprints.id", ondelete="SET NULL")
    )
    applicant_player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    proposed_name: Mapped[str] = mapped_column(String(120), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False)
    land_area_hectares: Mapped[float] = mapped_column(Decimal(10, 2), nullable=False)
    expected_jobs: Mapped[int] = mapped_column(Integer, default=0)
    traffic_load: Mapped[int] = mapped_column(Integer, default=0)
    service_load: Mapped[int] = mapped_column(Integer, default=0)
    medical_load: Mapped[int] = mapped_column(Integer, default=0)
    public_benefit: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="revision_required")
    mayor_score: Mapped[int] = mapped_column(Integer, default=0)
    mayor_summary: Mapped[str] = mapped_column(String(300), nullable=False)
    mayor_issues: Mapped[list] = mapped_column(JSON, default=list)
    mayor_questions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped["City"] = relationship("City", back_populates="building_applications")
    district: Mapped["CityDistrict"] = relationship("CityDistrict", back_populates="building_applications")
    land_parcel: Mapped["LandParcel"] = relationship("LandParcel", back_populates="building_applications")
    business_blueprint: Mapped[Optional["BusinessBlueprint"]] = relationship(
        "BusinessBlueprint", back_populates="applications"
    )
    applicant: Mapped["Player"] = relationship("Player", back_populates="building_applications")
    building: Mapped[Optional["Building"]] = relationship(
        "Building", back_populates="source_application", uselist=False
    )


class Building(Base):
    __tablename__ = "buildings"
    __table_args__ = (
        UniqueConstraint("land_parcel_id", name="uq_buildings_land_parcel_id"),
        UniqueConstraint("source_application_id", name="uq_buildings_source_application_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    district_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("city_districts.id", ondelete="CASCADE"), nullable=False)
    land_parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("land_parcels.id", ondelete="CASCADE"), nullable=False)
    source_application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("building_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    business_blueprint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("business_blueprints.id", ondelete="SET NULL")
    )
    business_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id", ondelete="SET NULL"), unique=True)
    owner_player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="built")
    operating_status: Mapped[str] = mapped_column(String(30), default="inactive")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped["City"] = relationship("City", back_populates="buildings")
    district: Mapped["CityDistrict"] = relationship("CityDistrict", back_populates="buildings")
    land_parcel: Mapped["LandParcel"] = relationship("LandParcel", back_populates="building")
    source_application: Mapped["BuildingApplication"] = relationship("BuildingApplication", back_populates="building")
    business_blueprint: Mapped[Optional["BusinessBlueprint"]] = relationship(
        "BusinessBlueprint", back_populates="buildings"
    )
    owner: Mapped["Player"] = relationship("Player", back_populates="buildings")
    business: Mapped[Optional["Business"]] = relationship("Business", back_populates="building")


class BusinessBlueprint(Base):
    __tablename__ = "business_blueprints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(70), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    business_type: Mapped[str] = mapped_column(String(50), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(600), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(30), nullable=False)
    allowed_land_types: Mapped[list] = mapped_column(JSON, default=list)
    allowed_zoning_types: Mapped[list] = mapped_column(JSON, default=list)
    min_area_hectares: Mapped[float] = mapped_column(Decimal(10, 2), default=0.00)
    construction_cost: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    opening_fee: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    recommended_cash_reserve: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    daily_profit_min: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    daily_profit_max: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    upkeep_daily: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    risk_level: Mapped[int] = mapped_column(Integer, default=1)
    risks: Mapped[list] = mapped_column(JSON, default=list)
    metric_effects: Mapped[dict] = mapped_column(JSON, default=dict)
    visual_archetype: Mapped[str] = mapped_column(String(80), nullable=False)
    style_tags: Mapped[list] = mapped_column(JSON, default=list)
    player_hints: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    applications: Mapped[list["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="business_blueprint",
    )
    buildings: Mapped[list["Building"]] = relationship(
        "Building",
        back_populates="business_blueprint",
    )


# 2. МОДЕЛЬ ГРАВЦЯ
class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    auth_token: Mapped[str | None] = mapped_column(
        String(120),
        unique=True,
        nullable=True,
    )
    auth_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    balance: Mapped[float] = mapped_column(Decimal(15, 2), default=500.00)
    energy: Mapped[int] = mapped_column(Integer, default=100)
    mood: Mapped[int] = mapped_column(Integer, default=100)
    hunger: Mapped[int] = mapped_column(Integer, default=0)
    tutorial_age_group: Mapped[str] = mapped_column(String(20), default="adult")
    education_level: Mapped[str] = mapped_column(String(50), default="High School")
    diploma_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    # Post-MVP foundation fields (Phase G1). criminal_rep grows from background
    # coefficients per profession/business and from shadow operations (Phase G9).
    # successful_deals grows from lawyer/police/journalist successful engagements (Phase G8).
    criminal_rep: Mapped[float] = mapped_column(Float, default=0.0)
    successful_deals: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="players", foreign_keys=[city_id])
    businesses: Mapped[list["Business"]] = relationship("Business", back_populates="owner")
    job: Mapped[Optional["Job"]] = relationship("Job", back_populates="worker", uselist=False)
    hostel_rented: Mapped[Optional["Hostel"]] = relationship("Hostel", back_populates="tenant", uselist=False)
    police_records: Mapped[list["PoliceRecord"]] = relationship("PoliceRecord", back_populates="player")
    pets: Mapped[list["Pet"]] = relationship("Pet", back_populates="owner")
    athlete_contract: Mapped[Optional["PlayerAthleteContract"]] = relationship(
        "PlayerAthleteContract", back_populates="player", uselist=False
    )
    loans: Mapped[list["BankLoan"]] = relationship("BankLoan", back_populates="player")
    insurance_policies: Mapped[list["InsurancePolicy"]] = relationship("InsurancePolicy", back_populates="player")
    land_parcels: Mapped[list["LandParcel"]] = relationship("LandParcel", back_populates="owner")
    building_applications: Mapped[list["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="applicant",
    )
    buildings: Mapped[list["Building"]] = relationship("Building", back_populates="owner")
    onboarding: Mapped[Optional["PlayerOnboarding"]] = relationship(
        "PlayerOnboarding",
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )
    avatar: Mapped[Optional["PlayerAvatar"]] = relationship(
        "PlayerAvatar",
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )
    business_rating: Mapped[Optional["PlayerBusinessRating"]] = relationship(
        "PlayerBusinessRating", back_populates="player", uselist=False
    )


class PlayerAvatar(Base):
    __tablename__ = "player_avatars"

    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        primary_key=True,
    )
    body_preset_code: Mapped[str] = mapped_column(String(40), default="body_standard")
    face_preset_code: Mapped[str] = mapped_column(String(40), default="face_01")
    skin_tone_code: Mapped[str] = mapped_column(String(40), default="skin_03")
    hair_style_code: Mapped[str] = mapped_column(String(40), default="hair_short_01")
    hair_color_code: Mapped[str] = mapped_column(String(40), default="hair_brown")
    equipped_outfit: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "upper": "upper_stock_jacket",
            "lower": "lower_stock_jeans",
            "footwear": "footwear_stock_sneakers",
        },
    )
    animation_profile_code: Mapped[str] = mapped_column(String(50), default="humanoid_context_v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    player: Mapped["Player"] = relationship("Player", back_populates="avatar")


class PlayerOnboarding(Base):
    __tablename__ = "player_onboarding"

    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        primary_key=True,
    )
    stage: Mapped[str] = mapped_column(String(30), default="arrival_choice")
    police_report_status: Mapped[str] = mapped_column(String(30), default="not_filed")
    police_recovery_amount: Mapped[float | None] = mapped_column(Decimal(15, 2))
    police_recovery_available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    player: Mapped["Player"] = relationship("Player", back_populates="onboarding")


# 3. МОДЕЛЬ ПІДПРИЄМСТВА (БІЗНЕСУ)
class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'utility_water', 'utility_housing', 'shop', 'factory', 'private_hostel'
    owner_player_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    owner_share_pct: Mapped[float] = mapped_column(Decimal(5, 2), default=100.00)
    cash_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=10000.00)
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'bankrupt', 'damaged'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Нові поля для управління бізнесом
    management_mode: Mapped[str] = mapped_column(String(20), default="manual")  # ai/manual/shadow
    legal_form: Mapped[str] = mapped_column(String(10), default="fop")  # fop/tov/vat
    business_size: Mapped[int] = mapped_column(Integer, default=1)  # кількість працівників
    ai_profit_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=0.10)  # динамічний % для AI
    daily_revenue: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)  # щоденний дохід

    # Поля для стартапів
    is_startup: Mapped[bool] = mapped_column(Boolean, default=False)
    startup_stage: Mapped[str] = mapped_column(String(20), default="idea")  # idea/prototype/mvp/growth
    startup_funding: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    startup_investors: Mapped[dict] = mapped_column(JSON, default=dict)
    startup_success_chance: Mapped[float] = mapped_column(Decimal(5, 2), default=60.00)

    # Економічні показники
    profit_margin: Mapped[float] = mapped_column(Decimal(5, 2), default=15.00)  # рентабельність %
    market_share: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)  # частка ринку %

    # Phase G3: Utility-служби (power/water/waste/housing)
    utility_service_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    service_capacity: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    service_load: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    is_emergency_contract: Mapped[bool] = mapped_column(Boolean, default=False)

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="businesses")
    owner: Mapped[Optional["Player"]] = relationship("Player", back_populates="businesses")
    building: Mapped[Optional["Building"]] = relationship("Building", back_populates="business", uselist=False)
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="business")
    hostels: Mapped[list["Hostel"]] = relationship("Hostel", back_populates="business")


# 4. МОДЕЛЬ РОБОТИ ТА ВАКАНСІЇ
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    salary_per_hour: Mapped[float] = mapped_column(Decimal(10, 2), nullable=False)
    min_education: Mapped[str] = mapped_column(String(50), default="High School")
    energy_cost_per_shift: Mapped[int] = mapped_column(Integer, default=30)
    filled_by_player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"), unique=True
    )
    # Phase G4: розширення вакансій
    bonus_pct: Mapped[float] = mapped_column(Decimal(5, 2), default=0.00)  # % від чистого прибутку
    shift_type: Mapped[str] = mapped_column(String(20), default="day")  # day/evening/student
    is_npc_position: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    business: Mapped["Business"] = relationship("Business", back_populates="jobs")
    worker: Mapped[Optional["Player"]] = relationship("Player", back_populates="job")


# 5. МОДЕЛЬ КІМНАТИ ХОСТЕЛУ
class Hostel(Base):
    __tablename__ = "hostels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    room_number: Mapped[int] = mapped_column(Integer, nullable=False)
    rent_price_per_day: Mapped[float] = mapped_column(Decimal(10, 2), default=15.00)
    energy_regen_per_hour: Mapped[int] = mapped_column(Integer, default=10)
    tenant_player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"), unique=True
    )

    # Зв'язки ORM
    business: Mapped["Business"] = relationship("Business", back_populates="hostels")
    tenant: Mapped[Optional["Player"]] = relationship("Player", back_populates="hostel_rented")


# 6. МОДЕЛЬ ЛОГУВАННЯ ТРАНЗАКЦІЙ
class TransactionModelLog(Base):
    __tablename__ = "transactions_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'player', 'business', 'treasury', 'system'
    receiver_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    receiver_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'player', 'business', 'treasury', 'system'
    amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    tax_deducted: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False)  # 'salary', 'rent', 'tax_payment'
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="transactions")


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("action", "key", "player_id", name="uq_idempotency_action_key_player"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    player_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 7. МОДЕЛЬ ПОЛІЦЕЙСЬКИХ ЗАПИСІВ
class PoliceRecord(Base):
    __tablename__ = "police_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    offense_type: Mapped[str] = mapped_column(String(100), nullable=False)  # 'fake_diploma', 'tax_evasion'
    fine_amount: Mapped[float | None] = mapped_column(Decimal(10, 2))
    status: Mapped[str] = mapped_column(
        String(20), default="under_investigation"
    )  # 'fined', 'imprisoned', 'case_closed'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="police_records")


# 7b. МОДЕЛЬ ПОЛІЦЕЙСЬКОГО (Phase G8)
class PoliceOfficer(Base):
    """Гравець-поліцейський: ієрархія patrol → detective → chief."""

    __tablename__ = "police_officers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    rank: Mapped[str] = mapped_column(String(20), nullable=False, default="patrol")  # patrol|detective|chief
    department: Mapped[str | None] = mapped_column(String(50), nullable=True)
    patrol_district_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("city_districts.id", ondelete="SET NULL"))
    successful_investigations: Mapped[int] = mapped_column(Integer, default=0)
    bribes_taken: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hired_at_game_day: Mapped[int] = mapped_column(Integer, default=0)
    promoted_at_game_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    appointed_by_mayor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 8. МОДЕЛЬ ДОМАШНЬОГО УЛУБЛЕНЦЯ
class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)  # 'dog', 'cat', 'raccoon', 'robotic'
    breed: Mapped[str] = mapped_column(String(50), nullable=False)
    hunger: Mapped[int] = mapped_column(Integer, default=0)
    health: Mapped[int] = mapped_column(Integer, default=100)
    loyalty: Mapped[int] = mapped_column(Integer, default=50)
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'sick', 'shelter_lost'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    owner: Mapped["Player"] = relationship("Player", back_populates="pets")


# 9. МОДЕЛЬ СПОРТИВНОГО КЛУБУ
class SportsClub(Base):
    __tablename__ = "sports_clubs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    sport_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # 'football', 'baseball', 'basketball', 'cybersport'
    owner_player_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    cash_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=50000.00)
    stadium_capacity: Mapped[int] = mapped_column(Integer, default=5000)
    ticket_price: Mapped[float] = mapped_column(Decimal(10, 2), default=10.00)
    training_efficiency: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)
    league_points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    contracts: Mapped[list["PlayerAthleteContract"]] = relationship("PlayerAthleteContract", back_populates="club")
    owner: Mapped["Player"] = relationship("Player", foreign_keys=[owner_player_id])


# 10. МОДЕЛЬ СПОРТИВНОГО КОНТРАКТУ
class PlayerAthleteContract(Base):
    __tablename__ = "player_athlete_contracts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    club_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sports_clubs.id", ondelete="CASCADE"), nullable=False)
    salary_per_match: Mapped[float] = mapped_column(Decimal(10, 2), default=200.00)
    role: Mapped[str] = mapped_column(String(30), default="player")  # 'player', 'star_player', 'coach'
    contract_status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'bench', 'expired'
    strength_stat: Mapped[int] = mapped_column(Integer, default=10)
    stamina_stat: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="athlete_contract")
    club: Mapped["SportsClub"] = relationship("SportsClub", back_populates="contracts")


# 11. МОДЕЛЬ КРЕДИТУ
class BankLoan(Base):
    __tablename__ = "bank_loans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    principal_amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    remaining_debt: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    daily_payment: Mapped[float] = mapped_column(Decimal(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'delinquent', 'paid', 'defaulted'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="loans")


# 12. МОДЕЛЬ СТРАХОВОГО ПОЛІСУ
class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    business_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    provider_business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    coverage_amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    daily_premium: Mapped[float] = mapped_column(Decimal(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'claimed', 'expired'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="insurance_policies")


# 13. МОДЕЛЬ ПРОФСПІЛКИ
class LaborUnion(Base):
    __tablename__ = "labor_unions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    strike_active: Mapped[bool] = mapped_column(Boolean, default=False)
    strike_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 14. МОДЕЛЬ КАРТЕЛЮ
class Cartel(Base):
    __tablename__ = "cartels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'transport', 'factory', 'retail'
    lobby_fund: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 15. МОДЕЛЬ МІСЬКОГО ТРАНСПОРТУ
class Transport(Base):
    __tablename__ = "transports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)  # 'bus', 'tram', 'subway', 'taxi_fleet'
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_player_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    ticket_price: Mapped[float] = mapped_column(Decimal(10, 2), default=2.00)
    passenger_capacity: Mapped[int] = mapped_column(Integer, default=100)
    maintenance_cost: Mapped[float] = mapped_column(Decimal(10, 2), default=50.00)
    operational_status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'inactive', 'overloaded'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# === POST-MVP GAMEPLAY FOUNDATION (Phase G1) ===
# These models mirror the schema laid down by migration g1a2b3c4d5e6.
# Services for them arrive in later phases (G2-G12); for now they exist
# only as ORM mappings so the dynamic-district-metrics service can read
# related rows and so future phases have a stable schema to build on.


class DistrictMetricSnapshot(Base):
    """Per-day snapshot of all district metrics + composite indices.

    Written by district_metrics.recalculate_district_metrics on each day tick.
    Read by /api/districts/{id}/radar to compute 7-day trends.
    """

    __tablename__ = "district_metric_snapshots"
    __table_args__ = (UniqueConstraint("district_id", "game_day", name="uq_district_metric_snapshots_district_day"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    district_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("city_districts.id", ondelete="CASCADE"), nullable=False)
    game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    # Raw metrics (existing + new)
    rent_level: Mapped[float] = mapped_column(Float, nullable=False)
    job_supply: Mapped[float] = mapped_column(Float, nullable=False)
    crime_risk: Mapped[float] = mapped_column(Float, nullable=False)
    traffic: Mapped[float] = mapped_column(Float, nullable=False)
    service_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    medical_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    land_value: Mapped[float] = mapped_column(Float, nullable=False)
    desirability: Mapped[float] = mapped_column(Float, nullable=False)
    pollution: Mapped[float] = mapped_column(Float, nullable=False)
    education_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    fire_safety: Mapped[float] = mapped_column(Float, nullable=False)
    power_supply: Mapped[float] = mapped_column(Float, nullable=False)
    water_supply: Mapped[float] = mapped_column(Float, nullable=False)
    waste_management: Mapped[float] = mapped_column(Float, nullable=False)
    population: Mapped[float] = mapped_column(Float, nullable=False)
    housing_capacity: Mapped[float] = mapped_column(Float, nullable=False)
    green_space: Mapped[float] = mapped_column(Float, nullable=False)
    happiness: Mapped[float] = mapped_column(Float, nullable=False)
    # Composite indices (0-100)
    economy_score: Mapped[float] = mapped_column(Float, nullable=False)
    production_score: Mapped[float] = mapped_column(Float, nullable=False)
    household_score: Mapped[float] = mapped_column(Float, nullable=False)
    commerce_score: Mapped[float] = mapped_column(Float, nullable=False)
    infrastructure_score: Mapped[float] = mapped_column(Float, nullable=False)
    social_score: Mapped[float] = mapped_column(Float, nullable=False)
    season: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    district: Mapped["CityDistrict"] = relationship("CityDistrict")


class NpcResident(Base):
    """Lightweight NPC account (Phase G2). Not a Player: no auth, no onboarding."""

    __tablename__ = "npc_residents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    district_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("city_districts.id", ondelete="CASCADE"), nullable=False)
    workplace_business_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id", ondelete="SET NULL"))
    cash_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    salary: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    employed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    npc_type: Mapped[str] = mapped_column(String(30), default="worker")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Skin(Base):
    """Player-designed character skin (Phase G9 / atelier)."""

    __tablename__ = "skins"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    designer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    atelier_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), default="common")
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False)
    copies_total: Mapped[int] = mapped_column(Integer, default=1)
    copies_sold: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlayerSkin(Base):
    __tablename__ = "player_skins"
    __table_args__ = (UniqueConstraint("player_id", "skin_id", name="uq_player_skins_player_skin"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    skin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skins.id", ondelete="CASCADE"), nullable=False)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Education(Base):
    """Education enrollment (Phase G10). Course opens decision-tree branches."""

    __tablename__ = "education"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    course: Mapped[str] = mapped_column(String(40), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="full_time")  # full_time | part_time
    status: Mapped[str] = mapped_column(String(20), default="enrolled")  # enrolled|completed|revoked
    is_fake: Mapped[bool] = mapped_column(Boolean, default=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EducationExam(Base):
    __tablename__ = "education_exams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(40), nullable=False)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CriminalRepLog(Base):
    """History of criminal_rep changes (Phase G9)."""

    __tablename__ = "criminal_rep_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CorruptionLog(Base):
    """Hidden incident log (Phase G8). Accessed by police, AI detector, mayor."""

    __tablename__ = "corruption_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    incident_type: Mapped[str] = mapped_column(String(40), nullable=False)
    perpetrator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    victim_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    amount: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    district_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("city_districts.id", ondelete="SET NULL"))
    evidence_strength: Mapped[float] = mapped_column(Float, default=0.1)
    is_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    reported_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    is_investigated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_proven: Mapped[bool] = mapped_column(Boolean, default=False)
    consequence: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PressInvestigation(Base):
    __tablename__ = "press_investigations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    target_player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    journalist_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    incident_type: Mapped[str] = mapped_column(String(40), nullable=False)
    press_evidence: Mapped[float] = mapped_column(Float, default=0.0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scale: Mapped[str] = mapped_column(String(20), default="local")
    article_title: Mapped[str | None] = mapped_column(String(200))
    happiness_impact: Mapped[int] = mapped_column(Integer, default=0)
    reputation_impact: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CourtCase(Base):
    __tablename__ = "court_cases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    corruption_log_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("corruption_log.id", ondelete="SET NULL"))
    defendant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    verdict: Mapped[str] = mapped_column(String(40), nullable=False)
    is_appealed: Mapped[bool] = mapped_column(Boolean, default=False)
    appeal_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    judge_1_vote: Mapped[str | None] = mapped_column(String(20))
    judge_2_vote: Mapped[str | None] = mapped_column(String(20))
    judge_3_vote: Mapped[str | None] = mapped_column(String(20))
    judge_1_bribed: Mapped[bool] = mapped_column(Boolean, default=False)
    judge_2_bribed: Mapped[bool] = mapped_column(Boolean, default=False)
    judge_3_bribed: Mapped[bool] = mapped_column(Boolean, default=False)
    final_verdict: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PrisonSentence(Base):
    __tablename__ = "prison_sentences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    court_case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("court_cases.id", ondelete="SET NULL"))
    days_total: Mapped[int] = mapped_column(Integer, nullable=False)
    days_served: Mapped[int] = mapped_column(Integer, default=0)
    days_remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    good_behavior_reduction: Mapped[int] = mapped_column(Integer, default=0)
    business_impact: Mapped[str] = mapped_column(String(20), default="none")  # none|frozen|confiscated
    frozen_business_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(20), default="serving")  # serving|released|escaped
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CasinoGame(Base):
    __tablename__ = "casino_games"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    casino_business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    game_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="waiting")
    players: Mapped[dict] = mapped_column(JSON, nullable=False)
    pot: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    rake: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    winner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ShadowBusiness(Base):
    __tablename__ = "shadow_businesses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    district_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("city_districts.id", ondelete="CASCADE"), nullable=False)
    cash_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    is_discovered: Mapped[bool] = mapped_column(Boolean, default=False)
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LawyerEngagement(Base):
    __tablename__ = "lawyer_engagements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lawyer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    deal_type: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    commission: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    success_chance_bonus: Mapped[float] = mapped_column(Float, default=0.0)
    is_successful: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PressBlackmail(Base):
    __tablename__ = "press_blackmails"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    journalist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("press_investigations.id", ondelete="SET NULL")
    )
    amount_demanded: Mapped[float] = mapped_column(Decimal(15, 2), default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# 14. МОДЕЛЬ ЕКСТРЕНИХ КОНТРАКТІВ (Phase G3)
class UtilityEmergencyContract(Base):
    """Контракт з сусіднім містом при банкрутстві комунальної служби.

    Створується коли utility-служба банкротиться і тендер не закритий за 1 день.
    Мерія платить різницю між нормальною і завищеною ціною — це руйнує рейтинг мера.
    """

    __tablename__ = "utility_emergency_contracts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    utility_service_type: Mapped[str] = mapped_column(String(20), nullable=False)  # power/water/waste
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    normal_price_per_unit: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    started_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    ended_at_game_day: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 15. МОДЕЛЬ БАНКУ (Phase G5)
class BankDeposit(Base):
    """Депозит гравця у банку."""

    __tablename__ = "bank_deposits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    bank_business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    interest_rate: Mapped[float] = mapped_column(Decimal(5, 2), nullable=False)
    created_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    last_interest_game_day: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BankCredit(Base):
    """Кредит, виданий банком гравцю (Phase G5). Окремо від frozen BankLoan."""

    __tablename__ = "bank_credits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    bank_business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    borrower_player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    principal_amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    remaining_amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    interest_rate: Mapped[float] = mapped_column(Decimal(5, 2), nullable=False)
    term_days: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    due_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/repaid/defaulted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 16. МОДЕЛЬ АУКЦІОНУ БАНКРУТІВ (Phase G5)
class BankruptcyAuction(Base):
    """Аукціон банкрутів: 24 години реального часу, будь-який гравець."""

    __tablename__ = "bankruptcy_auctions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    starting_price: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    debt_amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    city_percentage: Mapped[float] = mapped_column(Decimal(5, 2), default=10.00)
    highest_bid: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    highest_bidder_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/won/closed
    winner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    winning_bid: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)


class AuctionBid(Base):
    """Ставка на аукціоні банкрутів."""

    __tablename__ = "auction_bids"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    auction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bankruptcy_auctions.id", ondelete="CASCADE"), nullable=False
    )
    bidder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 17. МОДЕЛІ ПОЛІТИЧНОЇ СИСТЕМИ (Phase G6)
class CityOffice(Base):
    """Посада у мерії: worker → department_head → deputy → mayor."""

    __tablename__ = "city_offices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[str] = mapped_column(String(30), nullable=False)
    department: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hired_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MayorElection(Base):
    """Вибори мера: відкрите голосування, мандат 6 місяців ігрового часу."""

    __tablename__ = "mayor_elections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    started_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    ends_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/concluded
    winner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ElectionCandidate(Base):
    """Кандидат у виборах мера."""

    __tablename__ = "election_candidates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    election_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mayor_elections.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    platform_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MayorVote(Base):
    """Голос виборця (відкрите голосування)."""

    __tablename__ = "mayor_votes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    election_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mayor_elections.id", ondelete="CASCADE"), nullable=False)
    voter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("election_candidates.id", ondelete="CASCADE"), nullable=False
    )
    voted_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VoteBribe(Base):
    """Підкуп голосів: тіньовий фонд, анонімна пропозиція."""

    __tablename__ = "vote_bribes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    election_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mayor_elections.id", ondelete="CASCADE"), nullable=False)
    briber_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    voter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="offered")  # offered/accepted/rejected/reported
    created_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PoliticalCorruptionLog(Base):
    """Журнал політичної корупції (Phase G6). Окремо від frozen CorruptionLog."""

    __tablename__ = "political_corruption_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_strength: Mapped[float] = mapped_column(Decimal(5, 2), default=0.00)
    is_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at_game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
