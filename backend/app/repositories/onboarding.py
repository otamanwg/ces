from datetime import datetime, timedelta
from uuid import UUID

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

    def create_for_player(self, player_id: UUID, **kwargs) -> PlayerOnboarding:
        """Створити онбординг для гравця."""
        onboarding = PlayerOnboarding(player_id=player_id, **kwargs)
        self.db.add(onboarding)
        self.db.commit()
        self.db.refresh(onboarding)
        return onboarding

    def update_stage(self, player_id: UUID, stage: str) -> bool:
        """Оновити етап онбордингу."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding:
            onboarding.current_stage = stage
            onboarding.stage_updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def complete_onboarding(self, player_id: UUID) -> bool:
        """Завершити онбординг."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding:
            onboarding.is_completed = True
            onboarding.completed_at = datetime.utcnow()
            onboarding.current_stage = "completed"
            self.db.commit()
            return True
        return False

    def set_police_choice(self, player_id: UUID, choice: str) -> bool:
        """Встановити вибір щодо поліції."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding:
            onboarding.police_choice = choice
            onboarding.police_choice_made_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def set_initial_money(self, player_id: UUID, amount: int) -> bool:
        """Встановити початкову суму грошей."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding:
            onboarding.initial_money_amount = amount
            self.db.commit()
            return True
        return False

    def get_pending_police_claims(self, city_id: UUID) -> list[PlayerOnboarding]:
        """Отримати очікуючі заяви до поліції."""
        cutoff_time = datetime.utcnow() - timedelta(hours=2)  # 2 години очікування

        return (
            self.db.query(PlayerOnboarding)
            .join(Player)
            .filter(
                Player.city_id == city_id,
                PlayerOnboarding.police_choice == "report",
                ~PlayerOnboarding.police_claim_processed,
                PlayerOnboarding.police_choice_made_at <= cutoff_time,
            )
            .all()
        )

    def process_police_claim(self, player_id: UUID, amount: int) -> bool:
        """Обробити заяву до поліції."""
        onboarding = self.get_by_player_id(player_id)
        if onboarding and not onboarding.police_claim_processed:
            onboarding.police_claim_processed = True
            onboarding.police_claim_amount = amount
            onboarding.police_claim_processed_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def get_with_player(self, player_id: UUID) -> PlayerOnboarding | None:
        """Отримати онбординг з даними гравця."""
        return (
            self.db.query(PlayerOnboarding)
            .options(joinedload(PlayerOnboarding.player))
            .filter(PlayerOnboarding.player_id == player_id)
            .first()
        )

    def get_stats_by_city(self, city_id: UUID) -> dict:
        """Отримати статистику онбордингу в місті."""
        from sqlalchemy import func

        result = (
            self.db.query(
                PlayerOnboarding.current_stage,
                func.count(PlayerOnboarding.id).label("count"),
            )
            .join(Player)
            .filter(Player.city_id == city_id)
            .group_by(PlayerOnboarding.current_stage)
            .all()
        )

        return {row.current_stage: row.count for row in result}

    def get_recent_arrivals(self, city_id: UUID, hours: int = 24) -> list[PlayerOnboarding]:
        """Отримати нещодавніх прибулих гравців."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

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
