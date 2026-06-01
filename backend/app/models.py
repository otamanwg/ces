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

# 2. МОДЕЛЬ ГРАВЦЯ
class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    auth_token: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    balance: Mapped[float] = mapped_column(Decimal(15, 2), default=500.00)
    energy: Mapped[int] = mapped_column(Integer, default=100)
    mood: Mapped[int] = mapped_column(Integer, default=100)
    hunger: Mapped[int] = mapped_column(Integer, default=0)
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
    athlete_contract: Mapped[Optional["PlayerAthleteContract"]] = relationship("PlayerAthleteContract", back_populates="player", uselist=False)
    loans: Mapped[List["BankLoan"]] = relationship("BankLoan", back_populates="player")
    insurance_policies: Mapped[List["InsurancePolicy"]] = relationship("InsurancePolicy", back_populates="player")

# 3. МОДЕЛЬ ПІДПРИЄМСТВА (БІЗНЕСУ)
class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # 'utility_water', 'utility_housing', 'shop', 'factory', 'private_hostel'
    owner_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    owner_share_pct: Mapped[float] = mapped_column(Decimal(5, 2), default=100.00)
    cash_balance: Mapped[float] = mapped_column(Decimal(15, 2), default=10000.00)
    status: Mapped[str] = mapped_column(String(20), default="active") # 'active', 'bankrupt', 'damaged'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="businesses")
    owner: Mapped[Optional["Player"]] = relationship("Player", back_populates="businesses")
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
    filled_by_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"), unique=True)
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
    tenant_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"), unique=True)

    # Зв'язки ORM
    business: Mapped["Business"] = relationship("Business", back_populates="hostels")
    tenant: Mapped[Optional["Player"]] = relationship("Player", back_populates="hostel_rented")

# 6. МОДЕЛЬ ЛОГУВАННЯ ТРАНЗАКЦІЙ
class TransactionModelLog(Base):
    __tablename__ = "transactions_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False) # 'player', 'business', 'treasury', 'system'
    receiver_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    receiver_type: Mapped[str] = mapped_column(String(20), nullable=False) # 'player', 'business', 'treasury', 'system'
    amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    tax_deducted: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False) # 'salary', 'rent', 'tax_payment'
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    city: Mapped["City"] = relationship("City", back_populates="transactions")


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("action", "key", "player_id", name="uq_idempotency_action_key_player"),
    )

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
    offense_type: Mapped[str] = mapped_column(String(100), nullable=False) # 'fake_diploma', 'tax_evasion'
    fine_amount: Mapped[Optional[float]] = mapped_column(Decimal(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="under_investigation") # 'fined', 'imprisoned', 'case_closed'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="police_records")

# 8. МОДЕЛЬ ДОМАШНЬОГО УЛУБЛЕНЦЯ
class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False) # 'dog', 'cat', 'raccoon', 'robotic'
    breed: Mapped[str] = mapped_column(String(50), nullable=False)
    hunger: Mapped[int] = mapped_column(Integer, default=0)
    health: Mapped[int] = mapped_column(Integer, default=100)
    loyalty: Mapped[int] = mapped_column(Integer, default=50)
    status: Mapped[str] = mapped_column(String(20), default="active") # 'active', 'sick', 'shelter_lost'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    owner: Mapped["Player"] = relationship("Player", back_populates="pets")

# 9. МОДЕЛЬ СПОРТИВНОГО КЛУБУ
class SportsClub(Base):
    __tablename__ = "sports_clubs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    sport_type: Mapped[str] = mapped_column(String(30), nullable=False) # 'football', 'baseball', 'basketball', 'cybersport'
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
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), unique=True, nullable=False)
    club_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sports_clubs.id", ondelete="CASCADE"), nullable=False)
    salary_per_match: Mapped[float] = mapped_column(Decimal(10, 2), default=200.00)
    role: Mapped[str] = mapped_column(String(30), default="player") # 'player', 'star_player', 'coach'
    contract_status: Mapped[str] = mapped_column(String(20), default="active") # 'active', 'bench', 'expired'
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
    status: Mapped[str] = mapped_column(String(20), default="active") # 'active', 'delinquent', 'paid', 'defaulted'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="loans")

# 12. МОДЕЛЬ СТРАХОВОГО ПОЛІСУ
class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    business_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    provider_business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False)
    coverage_amount: Mapped[float] = mapped_column(Decimal(15, 2), nullable=False)
    daily_premium: Mapped[float] = mapped_column(Decimal(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active") # 'active', 'claimed', 'expired'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Зв'язки ORM
    player: Mapped["Player"] = relationship("Player", back_populates="insurance_policies")

# 13. МОДЕЛЬ ПРОФСПІЛКИ
class LaborUnion(Base):
    __tablename__ = "labor_unions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), unique=True, nullable=False)
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
    industry_type: Mapped[str] = mapped_column(String(50), nullable=False) # 'transport', 'factory', 'retail'
    lobby_fund: Mapped[float] = mapped_column(Decimal(15, 2), default=0.00)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# 15. МОДЕЛЬ МІСЬКОГО ТРАНСПОРТУ
class Transport(Base):
    __tablename__ = "transports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False) # 'bus', 'tram', 'subway', 'taxi_fleet'
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_player_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"))
    ticket_price: Mapped[float] = mapped_column(Decimal(10, 2), default=2.00)
    passenger_capacity: Mapped[int] = mapped_column(Integer, default=100)
    maintenance_cost: Mapped[float] = mapped_column(Decimal(10, 2), default=50.00)
    operational_status: Mapped[str] = mapped_column(String(20), default="active") # 'active', 'inactive', 'overloaded'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

