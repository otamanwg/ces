from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import City, CityDistrict, LandParcel
from backend.app.services.city_districts import ensure_starter_districts


CITY_OWNED = "city_owned"
OWNED = "owned"


@dataclass(frozen=True)
class StarterLandParcel:
    code: str
    district_code: str
    label: str
    land_type: str
    zoning_type: str
    area_hectares: Decimal
    base_price_per_hectare: Decimal


STARTER_LAND_PARCELS: tuple[StarterLandParcel, ...] = (
    StarterLandParcel(
        code="bus_station_kiosk_lot",
        district_code="bus_station",
        label="Мала ділянка біля автовокзалу",
        land_type="in_city",
        zoning_type="commercial",
        area_hectares=Decimal("0.25"),
        base_price_per_hectare=Decimal("800.00"),
    ),
    StarterLandParcel(
        code="commercial_core_small_lot",
        district_code="commercial_core",
        label="Комерційна ділянка в центрі",
        land_type="in_city",
        zoning_type="commercial",
        area_hectares=Decimal("0.50"),
        base_price_per_hectare=Decimal("1200.00"),
    ),
    StarterLandParcel(
        code="residential_hostel_lot",
        district_code="highrise_residential",
        label="Житлова ділянка біля хостелів",
        land_type="in_city",
        zoning_type="residential",
        area_hectares=Decimal("0.75"),
        base_price_per_hectare=Decimal("900.00"),
    ),
    StarterLandParcel(
        code="industrial_workshop_lot",
        district_code="industrial_edge",
        label="Ділянка під майстерню в промзоні",
        land_type="in_city",
        zoning_type="industrial",
        area_hectares=Decimal("1.50"),
        base_price_per_hectare=Decimal("650.00"),
    ),
    StarterLandParcel(
        code="suburban_home_lot",
        district_code="suburb_private_sector",
        label="Передміська ділянка під житло",
        land_type="suburb",
        zoning_type="residential",
        area_hectares=Decimal("1.00"),
        base_price_per_hectare=Decimal("550.00"),
    ),
    StarterLandParcel(
        code="outer_expansion_lot",
        district_code="outer_land",
        label="Зовнішня земля під майбутній розвиток",
        land_type="near_city",
        zoning_type="mixed",
        area_hectares=Decimal("5.00"),
        base_price_per_hectare=Decimal("250.00"),
    ),
)


def ensure_starter_land_parcels(db: Session, city: City) -> None:
    ensure_starter_districts(db, city)
    db.flush()
    district_by_code = {
        district.code: district
        for district in db.query(CityDistrict).filter(CityDistrict.city_id == city.id).all()
    }
    existing_codes = {
        row[0]
        for row in db.query(LandParcel.code)
        .filter(LandParcel.city_id == city.id)
        .all()
    }
    missing_parcels = [parcel for parcel in STARTER_LAND_PARCELS if parcel.code not in existing_codes]
    if not missing_parcels:
        return

    db.add_all(
        [
            LandParcel(
                city_id=city.id,
                district_id=district_by_code[parcel.district_code].id,
                code=parcel.code,
                label=parcel.label,
                land_type=parcel.land_type,
                zoning_type=parcel.zoning_type,
                area_hectares=parcel.area_hectares,
                base_price_per_hectare=parcel.base_price_per_hectare,
                current_price=parcel.area_hectares * parcel.base_price_per_hectare,
                status=CITY_OWNED,
                owner_player_id=None,
            )
            for parcel in missing_parcels
            if parcel.district_code in district_by_code
        ]
    )


def get_land_parcels(db: Session, city_id: UUID) -> list[LandParcel]:
    return (
        db.query(LandParcel)
        .join(CityDistrict, CityDistrict.id == LandParcel.district_id)
        .filter(LandParcel.city_id == city_id)
        .order_by(CityDistrict.display_order, LandParcel.current_price, LandParcel.label)
        .all()
    )


def calculate_player_city_land_share_pct(db: Session, city_id: UUID, player_id: UUID) -> Decimal:
    all_parcels = db.query(LandParcel).filter(LandParcel.city_id == city_id).all()
    total_area = sum((Decimal(str(parcel.area_hectares)) for parcel in all_parcels), Decimal("0.00"))
    if total_area <= Decimal("0.00"):
        return Decimal("0.00")

    owned_area = sum(
        (
            Decimal(str(parcel.area_hectares))
            for parcel in all_parcels
            if parcel.owner_player_id == player_id
        ),
        Decimal("0.00"),
    )
    return (owned_area / total_area * Decimal("100.00")).quantize(Decimal("0.01"))
