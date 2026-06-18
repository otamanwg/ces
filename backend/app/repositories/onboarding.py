from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.models import Player, PlayerOnboarding
from backend.app.repositories.base import BaseRepository


class OnboardingRepository(BaseRepository[PlayerOnboarding]):
    """Репозиторій для операцій з онбордингом гравців."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, PlayerOnboarding)

    def get_by_player_id(self, player_id: UUID) -> PlayerOnboarding | None:
        """Отримати онбординг за ID гравця."""
        return self.db.query(PlayerOnboarding).filter(PlayerOnboarding.player_id == player_id).first()

    def get_by_id(self, id_: UUID) -> PlayerOnboarding | None:
        """PlayerOnboarding використовує player_id як primary key."""
        return self.get_by_player_id(id_)

    def get_by_id_for_update(self, id_: UUID) -> PlayerOnboarding | None:
        """Отримати онбординг із блокуванням за його primary key."""
        return self.db.query(PlayerOnboarding).filter(PlayerOnboarding.player_id == id_).with_for_update().first()

    def create_for_player(
        self,
        player_id: UUID,
        *,
        stage: str = "arrival_choice",
        police_report_status: str = "not_filed",
        police_recovery_amount: float | None = None,
        police_recovery_available_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> PlayerOnboarding:
        """Створити онбординг без завершення транзакції сервісу."""
        onboarding = PlayerOnboarding(
            player_id=player_id,
            stage=stage,
            police_report_status=police_report_status,
            police_recovery_amount=police_recovery_amount,
            police_recovery_available_at=police_recovery_available_at,
            completed_at=completed_at,
        )
        self.db.add(onboarding)
        self.db.flush()
        return onboarding

    def update_stage(self, player_id: UUID, stage: str) -> bool:
        """Оновити етап онбордингу без завершення транзакції."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding is None:
            return False

        onboarding.stage = stage
        self.db.add(onboarding)
        self.db.flush()
        return True

    def complete_onboarding(
        self,
        player_id: UUID,
        *,
        completed_at: datetime | None = None,
    ) -> bool:
        """Позначити онбординг завершеним без завершення транзакції."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding is None:
            return False

        onboarding.stage = "completed"
        onboarding.completed_at = completed_at or datetime.now(UTC)
        self.db.add(onboarding)
        self.db.flush()
        return True

    def set_police_recovery(
        self,
        player_id: UUID,
        *,
        status: str,
        amount: float | None = None,
        available_at: datetime | None = None,
    ) -> bool:
        """Оновити стан можливого повернення майна поліцією."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding is None:
            return False

        onboarding.police_report_status = status
        onboarding.police_recovery_amount = amount
        onboarding.police_recovery_available_at = available_at
        self.db.add(onboarding)
        self.db.flush()
        return True

    def get_claimable_police_recoveries(
        self,
        city_id: UUID,
        *,
        now: datetime | None = None,
    ) -> list[PlayerOnboarding]:
        """Отримати доступні для виплати повернення майна у місті."""
        current_time = now or datetime.now(UTC)
        return (
            self.db.query(PlayerOnboarding)
            .join(Player)
            .filter(
                Player.city_id == city_id,
                PlayerOnboarding.police_report_status == "pending",
                PlayerOnboarding.police_recovery_available_at.is_not(None),
                PlayerOnboarding.police_recovery_available_at <= current_time,
            )
            .all()
        )

    def mark_police_recovery_recovered(self, player_id: UUID) -> bool:
        """Позначити повернення майна виплаченим."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding is None or onboarding.police_report_status != "pending":
            return False

        onboarding.police_report_status = "recovered"
        self.db.add(onboarding)
        self.db.flush()
        return True

    def get_with_player(self, player_id: UUID) -> PlayerOnboarding | None:
        """Отримати онбординг з даними гравця."""
        return (
            self.db.query(PlayerOnboarding)
            .options(joinedload(PlayerOnboarding.player))
            .filter(PlayerOnboarding.player_id == player_id)
            .first()
        )

    def get_stats_by_city(self, city_id: UUID) -> dict[str, int]:
        """Отримати кількість гравців на кожному етапі онбордингу."""
        result = (
            self.db.query(
                PlayerOnboarding.stage,
                func.count(PlayerOnboarding.player_id),
            )
            .join(Player)
            .filter(Player.city_id == city_id)
            .group_by(PlayerOnboarding.stage)
            .all()
        )
        stats: dict[str, int] = {}
        for stage, count in result:
            stats[stage] = count
        return stats

    def get_recent_arrivals(
        self,
        city_id: UUID,
        hours: int = 24,
        *,
        now: datetime | None = None,
    ) -> list[PlayerOnboarding]:
        """Отримати нещодавніх прибулих гравців."""
        cutoff_time = (now or datetime.now(UTC)) - timedelta(hours=hours)
        return (
            self.db.query(PlayerOnboarding)
            .join(Player)
            .filter(
                Player.city_id == city_id,
                PlayerOnboarding.created_at >= cutoff_time,
            )
            .order_by(PlayerOnboarding.created_at.desc())
            .all()
        )
