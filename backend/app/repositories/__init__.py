from backend.app.repositories.advanced import (
    BankLoanRepository,
    CartelRepository,
    InsuranceRepository,
    LaborUnionRepository,
)
from backend.app.repositories.base import BaseRepository
from backend.app.repositories.buildings import BuildingApplicationRepository, BuildingRepository
from backend.app.repositories.business import BusinessRepository
from backend.app.repositories.business_blueprints import BusinessBlueprintRepository
from backend.app.repositories.city import CityRepository
from backend.app.repositories.hostel import HostelRepository
from backend.app.repositories.job import JobRepository
from backend.app.repositories.land_parcel import LandParcelRepository
from backend.app.repositories.onboarding import OnboardingRepository
from backend.app.repositories.player import PlayerRepository
from backend.app.repositories.sports import AthleteContractRepository, SportsRepository

__all__ = [
    "BaseRepository",
    "BankLoanRepository",
    "BusinessRepository",
    "BusinessBlueprintRepository",
    "BuildingApplicationRepository",
    "BuildingRepository",
    "CartelRepository",
    "CityRepository",
    "HostelRepository",
    "InsuranceRepository",
    "JobRepository",
    "LandParcelRepository",
    "LaborUnionRepository",
    "OnboardingRepository",
    "PlayerRepository",
    "SportsRepository",
    "AthleteContractRepository",
]
