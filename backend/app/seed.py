import logging

from sqlalchemy.orm import Session

from backend.app.models import Business, City, Hostel, Job, SportsClub
from backend.app.services.business_blueprints import ensure_business_blueprints
from backend.app.services.land import ensure_starter_land_parcels

logger = logging.getLogger("CityServer")


def seed_initial_data(db: Session) -> None:
    """Create the neutral MVP city and starter gameplay data when DB is empty."""
    ensure_business_blueprints(db)

    existing_cities = db.query(City).all()
    if existing_cities:
        for city in existing_cities:
            ensure_starter_land_parcels(db, city)
        db.commit()
        return

    logger.info("Створення початкового нейтрального міста та комунальних підприємств...")

    city = City(
        name="Київ-Нейтральний",
        treasury_balance=50000.00,
        tax_rate_income=10.00,
        tax_rate_property=2.00,
    )
    db.add(city)
    db.flush()
    ensure_starter_land_parcels(db, city)

    gkh = Business(
        city_id=city.id,
        name="МіськЕнерго (ЖКГ)",
        type="utility_housing",
        owner_player_id=None,
        cash_balance=20000.00,
        utility_service_type="housing",
        service_capacity=100,
    )
    voda = Business(
        city_id=city.id,
        name="Водоканал",
        type="utility_water",
        owner_player_id=None,
        cash_balance=15000.00,
        utility_service_type="water",
        service_capacity=100,
    )
    coffee_shop = Business(
        city_id=city.id,
        name="Кав'ярня біля вокзалу",
        type="shop",
        owner_player_id=None,
        cash_balance=1000.00,
    )
    db.add_all([gkh, voda, coffee_shop])
    db.flush()

    db.add_all(
        [
            Job(
                business_id=voda.id,
                title="Сантехнік Водоканалу",
                salary_per_hour=25.00,
                min_education="High School",
                energy_cost_per_shift=30,
            ),
            Job(
                business_id=gkh.id,
                title="Електрик ЖКГ",
                salary_per_hour=30.00,
                min_education="High School",
                energy_cost_per_shift=30,
            ),
            Job(
                business_id=gkh.id,
                title="Головний Диспетчер ЖКГ",
                salary_per_hour=50.00,
                min_education="College",
                energy_cost_per_shift=25,
            ),
        ]
    )

    for room_number in range(1, 6):
        db.add(
            Hostel(
                business_id=gkh.id,
                room_number=room_number,
                rent_price_per_day=15.00,
                energy_regen_per_hour=10,
            )
        )

    db.add_all(
        [
            SportsClub(
                city_id=city.id,
                name="ФК Київ-Енерджі (Футбол)",
                sport_type="football",
                owner_player_id=None,
                stadium_capacity=8000,
                ticket_price=15.00,
            ),
            SportsClub(
                city_id=city.id,
                name="БК Дніпровські Титани (Баскетбол)",
                sport_type="basketball",
                owner_player_id=None,
                stadium_capacity=4000,
                ticket_price=12.00,
            ),
            SportsClub(
                city_id=city.id,
                name="Київські Соколи (Бейсбол)",
                sport_type="baseball",
                owner_player_id=None,
                stadium_capacity=6000,
                ticket_price=10.00,
            ),
        ]
    )

    db.commit()
    logger.info("Початковий сидінг бази даних завершено успішно!")
