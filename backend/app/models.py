# Моделі бази даних SQLAlchemy для MVP Економічного Симулятора
# Файл: backend/app/models.py

from datetime import datetime
import secrets
import uuid
from typing import List, Optional
from sqlalchemy import String, Numeric as Decimal, Integer, Boolean, ForeignKey, DateTime, JSON, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# 1. МОДЕЛЬ МІСТА (СЕРВЕРА)
class City(Base):
    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    treasury_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=50000.00)
    tax_rate_income: Mapped[float] = mapped_column(Decimal(5, 2), default=10.00)
    tax_rate_property: Mapped[float] = mapped_column(Decimal(5, 2), default=2.00)
    inflation_rate: Mapped[float] = mapped_column(Decimal(5, 2), default=0.00)
    mayor_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL", use_alter=True, name="fk_cities_mayor_player_id")
    )

    # Зв'язки ORM
    players: Mapped[List["Player"]] = relationship("Player", back_populates="city", foreign_keys="Player.city_id")
    businesses: Mapped[List["Business"]] = relationship("Business", back_populates="city")
    mayor: Mapped[Optional["Player"]] = relationship("Player", foreign_keys=[mayor_player_id], post_update=True)
    transactions: Mapped[List["TransactionModelLog"]] = relationship("TransactionModelLog", back_populates="city")
    districts: Mapped[List["CityDistrict"]] = relationship(
        "CityDistrict",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    land_parcels: Mapped[List["LandParcel"]] = relationship(
        "LandParcel",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    building_applications: Mapped[List["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="city",
        cascade="all, delete-orphan",
    )
    buildings: Mapped[List["Building"]] = relationship(
        "Building",
        back_populates="city",
        cascade="all, delete-orphan",
    )


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped["City"] = relationship("City", back_populates="districts")
    land_parcels: Mapped[List["LandParcel"]] = relationship(
        "LandParcel",
        back_populates="district",
        cascade="all, delete-orphan",
    )
    building_applications: Mapped[List["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="district",
        cascade="all, delete-orphan",
    )
    buildings: Mapped[List["Building"]] = relationship(
        "Building",
        back_populates="district",
        cascade="all, delete-orphan",
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
    owner_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    city: Mapped["City"] = relationship("City", back_populates="land_parcels")
    district: Mapped["CityDistrict"] = relationship("CityDistrict", back_populates="land_parcels")
    owner: Mapped[Optional["Player"]] = relationship("Player", back_populates="land_parcels")
    building_applications: Mapped[List["BuildingApplication"]] = relationship(
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
    business_blueprint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
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
    business_blueprint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("business_blueprints.id", ondelete="SET NULL")
    )
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("businesses.id", ondelete="SET NULL"), unique=True
    )
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

    applications: Mapped[List["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="business_blueprint",
    )
    buildings: Mapped[List["Building"]] = relationship(
        "Building",
        back_populates="business_blueprint",
    )


# 2. МОДЕЛЬ ГРАВЦЯ
class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    auth_token: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32)
    )
    balance: Mapped[float] = mapped_column(Decimal(15, 2), default=500.00)
    energy: Mapped[int] = mapped_column(Integer, default=100)
    mood: Mapped[int] = mapped_column(Integer, default=100)
    hunger: Mapped[int] = mapped_column(Integer, default=0)
    tutorial_age_group: Mapped[str] = mapped_column(String(20), default="adult")
    education_level: Mapped[str] = mapped_column(String(50), default="High School")
    diploma_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="players", foreign_keys=[city_id])
    businesses: Mapped[List["Business"]] = relationship("Business", back_populates="owner")
    job: Mapped[Optional["Job"]] = relationship("Job", back_populates="worker", uselist=False)
    hostel_rented: Mapped[Optional["Hostel"]] = relationship("Hostel", back_populates="tenant", uselist=False)
    police_records: Mapped[List["PoliceRecord"]] = relationship("PoliceRecord", back_populates="player")
    pets: Mapped[List["Pet"]] = relationship("Pet", back_populates="owner")
    athlete_contract: Mapped[Optional["PlayerAthleteContract"]] = relationship(
        "PlayerAthleteContract", back_populates="player", uselist=False
    )
    loans: Mapped[List["BankLoan"]] = relationship("BankLoan", back_populates="player")
    insurance_policies: Mapped[List["InsurancePolicy"]] = relationship("InsurancePolicy", back_populates="player")
    land_parcels: Mapped[List["LandParcel"]] = relationship("LandParcel", back_populates="owner")
    building_applications: Mapped[List["BuildingApplication"]] = relationship(
        "BuildingApplication",
        back_populates="applicant",
    )
    buildings: Mapped[List["Building"]] = relationship("Building", back_populates="owner")
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
    police_recovery_amount: Mapped[Optional[float]] = mapped_column(Decimal(15, 2))
    police_recovery_available_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
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
    owner_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    owner_share_pct: Mapped[float] = mapped_column(Decimal(5, 2), default=100.00)
    cash_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=10000.00)
    status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'bankrupt', 'damaged'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="businesses")
    owner: Mapped[Optional["Player"]] = relationship("Player", back_populates="businesses")
    building: Mapped[Optional["Building"]] = relationship("Building", back_populates="business", uselist=False)
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="business")
    hostels: Mapped[List["Hostel"]] = relationship("Hostel", back_populates="business")


# 4. МОДЕЛЬ РОБОТИ ТА ВАКАНСІЇ
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    salary_per_hour: Mapped[float] = mapped_column(Decimal(10, 2), nullable=False)
    min_education: Mapped[str] = mapped_column(String(50), default="High School")
    energy_cost_per_shift: Mapped[int] = mapped_column(Integer, default=30)
    filled_by_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"), unique=True
    )
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
    tenant_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(
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
    player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# 7. МОДЕЛЬ ПОЛІЦЕЙСЬКИХ ЗАПИСІВ
class PoliceRecord(Base):
    __tablename__ = "police_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    offense_type: Mapped[str] = mapped_column(String(100), nullable=False)  # 'fake_diploma', 'tax_evasion'
    fine_amount: Mapped[Optional[float]] = mapped_column(Decimal(10, 2))
    status: Mapped[str] = mapped_column(
        String(20), default="under_investigation"
    )  # 'fined', 'imprisoned', 'case_closed'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="police_records")


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
    owner_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    cash_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=50000.00)
    stadium_capacity: Mapped[int] = mapped_column(Integer, default=5000)
    ticket_price: Mapped[float] = mapped_column(Decimal(10, 2), default=10.00)
    training_efficiency: Mapped[float] = mapped_column(Decimal(5, 2), default=1.00)
    league_points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    contracts: Mapped[List["PlayerAthleteContract"]] = relationship("PlayerAthleteContract", back_populates="club")


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
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
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
    strike_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
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
    owner_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    ticket_price: Mapped[float] = mapped_column(Decimal(10, 2), default=2.00)
    passenger_capacity: Mapped[int] = mapped_column(Integer, default=100)
    maintenance_cost: Mapped[float] = mapped_column(Decimal(10, 2), default=50.00)
    operational_status: Mapped[str] = mapped_column(String(20), default="active")  # 'active', 'inactive', 'overloaded'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
