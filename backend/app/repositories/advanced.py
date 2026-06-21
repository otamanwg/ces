from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import (
    BankLoan,
    Business,
    Cartel,
    InsurancePolicy,
    LaborUnion,
    Player,
)
from backend.app.repositories.base import BaseRepository


class InsuranceRepository(BaseRepository[InsurancePolicy]):
    """Репозиторій для страхових полісів."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, InsurancePolicy)

    def get_active_for_player(self, player_id: UUID) -> InsurancePolicy | None:
        """Отримати активний поліс гравця."""
        return (
            self.db.query(InsurancePolicy)
            .filter(
                InsurancePolicy.player_id == player_id,
                InsurancePolicy.status == "active",
            )
            .first()
        )

    def list_by_city(self, city_id: UUID) -> list[InsurancePolicy]:
        """Отримати всі поліси в місті."""
        return self.db.query(InsurancePolicy).join(Player).filter(Player.city_id == city_id).all()

    def create_policy(
        self, player_id: UUID, business_id: UUID, provider_business_id: UUID, coverage: float, premium: float
    ) -> InsurancePolicy:
        """Створити страховий поліс."""
        policy = InsurancePolicy(
            player_id=player_id,
            business_id=business_id,
            provider_business_id=provider_business_id,
            coverage_amount=coverage,
            daily_premium=premium,
            status="active",
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def cancel_policy(self, policy_id: UUID) -> bool:
        """Скасувати поліс."""
        policy = self.get_by_id(policy_id)
        if policy:
            policy.status = "expired"
            self.db.commit()
            return True
        return False


class BankLoanRepository(BaseRepository[BankLoan]):
    """Репозиторій для банківських кредитів."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, BankLoan)

    def get_active_for_player(self, player_id: UUID) -> list[BankLoan]:
        """Отримати активні кредити гравця."""
        return (
            self.db.query(BankLoan)
            .filter(
                BankLoan.player_id == player_id,
                BankLoan.status.in_(["active", "delinquent"]),
            )
            .all()
        )

    def create_loan(self, player_id: UUID, amount: int, interest_rate: float, term_days: int) -> BankLoan:
        """Створити кредит."""
        principal = Decimal(str(amount))
        remaining_debt = principal * (Decimal("1") + Decimal(str(interest_rate)))
        loan = BankLoan(
            player_id=player_id,
            principal_amount=principal,
            remaining_debt=remaining_debt,
            daily_payment=remaining_debt / max(term_days, 1),
            status="active",
        )
        self.db.add(loan)
        self.db.commit()
        self.db.refresh(loan)
        return loan

    def mark_as_repaid(self, loan_id: UUID) -> bool:
        """Позначити кредит як погашений."""
        loan = self.get_by_id(loan_id)
        if loan:
            loan.remaining_debt = Decimal("0")
            loan.status = "paid"
            self.db.commit()
            return True
        return False

    def get_overdue_loans(self, city_id: UUID) -> list[BankLoan]:
        """Отримати прострочені кредити в місті."""
        return (
            self.db.query(BankLoan)
            .join(Player)
            .filter(
                Player.city_id == city_id,
                BankLoan.status == "delinquent",
            )
            .all()
        )


class LaborUnionRepository(BaseRepository[LaborUnion]):
    """Репозиторій для профспілок."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, LaborUnion)

    def get_by_business(self, business_id: UUID) -> LaborUnion | None:
        """Отримати профспілку за бізнесом."""
        return self.db.query(LaborUnion).filter(LaborUnion.business_id == business_id).first()

    def create_union(self, business_id: UUID, name: str) -> LaborUnion:
        """Створити профспілку."""
        union = LaborUnion(
            business_id=business_id,
            name=name,
            strike_active=False,
        )
        self.db.add(union)
        self.db.commit()
        self.db.refresh(union)
        return union

    def toggle_strike(self, union_id: UUID) -> bool:
        """Перемкнути страйк."""
        union = self.get_by_id(union_id)
        if union:
            union.strike_active = not union.strike_active
            if union.strike_active:
                union.strike_ends_at = datetime.now(UTC) + timedelta(days=1)
            else:
                union.strike_ends_at = None
            self.db.commit()
            return True
        return False

    def get_active_strikes_in_city(self, city_id: UUID) -> list[LaborUnion]:
        """Отримати активні страйки в місті."""
        return (
            self.db.query(LaborUnion)
            .join(Business, LaborUnion.business_id == Business.id)
            .filter(
                Business.city_id == city_id,
                LaborUnion.strike_active,
            )
            .all()
        )


class CartelRepository(BaseRepository[Cartel]):
    """Репозиторій для картелів і лобістських фондів."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, Cartel)

    def get_by_city_and_industry(self, city_id: UUID, industry_type: str) -> Cartel | None:
        return (
            self.db.query(Cartel)
            .filter(
                Cartel.city_id == city_id,
                Cartel.industry_type == industry_type,
            )
            .first()
        )
