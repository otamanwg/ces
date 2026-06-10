from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from backend.app.models import PlayerAthleteContract, SportsClub
from backend.app.repositories.base import BaseRepository


class SportsRepository(BaseRepository[SportsClub]):
    """Репозиторій для операцій зі спортивними клубами."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, SportsClub)

    def list_by_city(self, city_id: UUID) -> list[SportsClub]:
        """Отримати список спортивних клубів у місті."""
        return self.db.query(SportsClub).filter(SportsClub.city_id == city_id).all()

    def get_by_city_and_code(self, city_id: UUID, club_code: str) -> SportsClub | None:
        """Знайти клуб за кодом у місті."""
        return self.db.query(SportsClub).filter(SportsClub.city_id == city_id, SportsClub.code == club_code).first()

    def get_with_contracts(self, club_id: UUID) -> SportsClub | None:
        """Отримати клуб з усіма контрактами гравців."""
        return (
            self.db.query(SportsClub)
            .options(joinedload(SportsClub.player_contracts))
            .filter(SportsClub.id == club_id)
            .first()
        )


class AthleteContractRepository(BaseRepository[PlayerAthleteContract]):
    """Репозиторій для контрактів гравців-атлетів."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, PlayerAthleteContract)

    def get_active_for_player(self, player_id: UUID) -> PlayerAthleteContract | None:
        """Отримати активний контракт гравця."""
        return (
            self.db.query(PlayerAthleteContract)
            .filter(
                PlayerAthleteContract.player_id == player_id,
                PlayerAthleteContract.is_active,
            )
            .first()
        )

    def list_by_club(self, club_id: UUID, active_only: bool = True) -> list[PlayerAthleteContract]:
        """Отримати контракти клубу."""
        query = self.db.query(PlayerAthleteContract).filter(PlayerAthleteContract.club_id == club_id)
        if active_only:
            query = query.filter(PlayerAthleteContract.is_active)
        return query.all()

    def list_by_club_with_players(self, club_id: UUID) -> list[PlayerAthleteContract]:
        """Отримати контракти клубу з даними гравців."""
        return (
            self.db.query(PlayerAthleteContract)
            .options(joinedload(PlayerAthleteContract.player))
            .filter(PlayerAthleteContract.club_id == club_id, PlayerAthleteContract.is_active)
            .all()
        )

    def count_active_for_club(self, club_id: UUID) -> int:
        """Підрахувати активні контракти в клубі."""
        return (
            self.db.query(PlayerAthleteContract)
            .filter(PlayerAthleteContract.club_id == club_id, PlayerAthleteContract.is_active)
            .count()
        )

    def deactivate_for_player(self, player_id: UUID) -> bool:
        """Деактивувати контракт гравця."""
        contract = self.get_active_for_player(player_id)
        if contract:
            contract.is_active = False
            self.db.commit()
            return True
        return False
