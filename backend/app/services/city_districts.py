from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import City, CityDistrict


@dataclass(frozen=True)
class StarterDistrict:
    code: str
    name: str
    zone_type: str
    description: str
    display_order: int
    land_available_hectares: Decimal
    rent_level: int
    job_supply: int
    crime_risk: int
    traffic: int
    service_coverage: int
    medical_coverage: int
    land_value: int
    desirability: int


STARTER_DISTRICTS: tuple[StarterDistrict, ...] = (
    StarterDistrict(
        code="bus_station",
        name="Автовокзал",
        zone_type="transit",
        description="Точка прибуття нових гравців біля комерційного району.",
        display_order=10,
        land_available_hectares=Decimal("2.00"),
        rent_level=45,
        job_supply=30,
        crime_risk=35,
        traffic=70,
        service_coverage=55,
        medical_coverage=45,
        land_value=60,
        desirability=50,
    ),
    StarterDistrict(
        code="commercial_core",
        name="Комерційне ядро",
        zone_type="commercial",
        description="Магазини, перші офіси, міські сервіси і короткі стартові роботи.",
        display_order=20,
        land_available_hectares=Decimal("12.00"),
        rent_level=70,
        job_supply=75,
        crime_risk=30,
        traffic=65,
        service_coverage=65,
        medical_coverage=60,
        land_value=80,
        desirability=65,
    ),
    StarterDistrict(
        code="highrise_residential",
        name="Житлова висотна забудова",
        zone_type="residential",
        description="Невеликі багатоповерхівки, хостели і перше доступне житло.",
        display_order=30,
        land_available_hectares=Decimal("18.00"),
        rent_level=55,
        job_supply=35,
        crime_risk=28,
        traffic=45,
        service_coverage=60,
        medical_coverage=55,
        land_value=65,
        desirability=62,
    ),
    StarterDistrict(
        code="industrial_edge",
        name="Промзона",
        zone_type="industrial",
        description="Виробництво, комунальні підприємства і фізично важчі вакансії.",
        display_order=40,
        land_available_hectares=Decimal("25.00"),
        rent_level=30,
        job_supply=80,
        crime_risk=45,
        traffic=60,
        service_coverage=45,
        medical_coverage=35,
        land_value=45,
        desirability=35,
    ),
    StarterDistrict(
        code="suburb_private_sector",
        name="Передмістя з приватним сектором",
        zone_type="suburban",
        description="Спокійніший район із приватними будинками і нижчою щільністю.",
        display_order=50,
        land_available_hectares=Decimal("40.00"),
        rent_level=40,
        job_supply=20,
        crime_risk=20,
        traffic=30,
        service_coverage=40,
        medical_coverage=35,
        land_value=50,
        desirability=70,
    ),
    StarterDistrict(
        code="outer_land",
        name="Зовнішні землі",
        zone_type="expansion",
        description="Поля, ліс і резерв для майбутнього розширення міста.",
        display_order=60,
        land_available_hectares=Decimal("250.00"),
        rent_level=15,
        job_supply=10,
        crime_risk=15,
        traffic=10,
        service_coverage=20,
        medical_coverage=15,
        land_value=25,
        desirability=45,
    ),
)


def ensure_starter_districts(db: Session, city: City) -> None:
    existing_codes = {
        row[0]
        for row in db.query(CityDistrict.code)
        .filter(CityDistrict.city_id == city.id)
        .all()
    }
    missing_districts = [
        district
        for district in STARTER_DISTRICTS
        if district.code not in existing_codes
    ]
    if not missing_districts:
        return

    db.add_all(
        [
            CityDistrict(
                city_id=city.id,
                code=district.code,
                name=district.name,
                zone_type=district.zone_type,
                description=district.description,
                display_order=district.display_order,
                land_available_hectares=district.land_available_hectares,
                rent_level=district.rent_level,
                job_supply=district.job_supply,
                crime_risk=district.crime_risk,
                traffic=district.traffic,
                service_coverage=district.service_coverage,
                medical_coverage=district.medical_coverage,
                land_value=district.land_value,
                desirability=district.desirability,
            )
            for district in missing_districts
        ]
    )


def get_city_districts(db: Session, city_id: UUID) -> list[CityDistrict]:
    return (
        db.query(CityDistrict)
        .filter(CityDistrict.city_id == city_id)
        .order_by(CityDistrict.display_order, CityDistrict.name)
        .all()
    )
