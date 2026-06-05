from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from backend.app.models import Business, Building, BuildingApplication, City, Player
from backend.app.services.ledger import credit, debit, log_transaction
from backend.app.services.money import money


BUILT = "built"
INACTIVE = "inactive"
ACTIVE = "active"
MAINTENANCE_DUE = "maintenance_due"
APPLICATION_ACTIVATED = "activated"
PARCEL_BUILT = "built"
BUILDING_UPKEEP_PURPOSE = "building_upkeep"
BUILDING_REPAIR_PURPOSE = "building_repair_fee"
MIN_BUILDING_REPAIR_FEE = money("25.00")
BUILDING_REPAIR_UPKEEP_MULTIPLIER = money("2.00")
BUSINESS_PROJECT_TYPES = {
    "commercial": "shop",
    "industrial": "factory",
}
BUILDING_OPENING_FEES = {
    "commercial": money("100.00"),
    "industrial": money("150.00"),
    "residential": money("60.00"),
    "medical": money("80.00"),
    "civic": money("0.00"),
}


def activate_building_application(db: Session, player: Player, application_id: UUID) -> dict:
    application = (
        db.query(BuildingApplication)
        .filter(BuildingApplication.id == application_id)
        .with_for_update()
        .first()
    )
    if not application or application.city_id != player.city_id:
        return {"success": False, "message": "Будівельну заявку не знайдено."}

    if application.applicant_player_id != player.id:
        return {"success": False, "message": "Активувати можна лише власну будівельну заявку."}

    if application.status == APPLICATION_ACTIVATED:
        return {"success": False, "message": "Цю будівельну заявку вже активовано."}

    if application.status != "approved":
        return {"success": False, "message": "Активувати можна лише погоджену AI-мером заявку."}

    parcel = application.land_parcel
    if parcel.owner_player_id != player.id or parcel.status != "owned":
        return {"success": False, "message": "Ділянка має бути у власності заявника і без готової будівлі."}

    existing_building = (
        db.query(Building)
        .filter(
            (Building.land_parcel_id == parcel.id)
            | (Building.source_application_id == application.id)
        )
        .first()
    )
    if existing_building:
        return {"success": False, "message": "Для цієї ділянки або заявки вже існує будівля."}

    building = Building(
        city_id=application.city_id,
        district_id=application.district_id,
        land_parcel_id=application.land_parcel_id,
        source_application_id=application.id,
        business_blueprint_id=application.business_blueprint_id,
        owner_player_id=player.id,
        name=application.proposed_name,
        project_type=application.project_type,
        status=BUILT,
        operating_status=INACTIVE,
    )
    db.add(building)
    application.status = APPLICATION_ACTIVATED
    parcel.status = PARCEL_BUILT
    db.commit()
    db.refresh(building)

    return {
        "success": True,
        "message": f"Будівлю '{building.name}' створено як міський актив.",
        "building": building,
    }


def get_building_opening_fee(building: Building):
    if building.business_blueprint:
        return money(building.business_blueprint.opening_fee)
    return BUILDING_OPENING_FEES.get(building.project_type, money("100.00"))


def get_building_repair_fee(building: Building):
    if building.business_blueprint:
        return max(money(building.business_blueprint.upkeep_daily) * BUILDING_REPAIR_UPKEEP_MULTIPLIER, MIN_BUILDING_REPAIR_FEE)
    return money("50.00")


def get_building_upkeep_daily(building: Building):
    if building.business_blueprint:
        return money(building.business_blueprint.upkeep_daily)
    return money("0.00")


def get_building_available_actions(building: Building) -> list[str]:
    if building.status != BUILT:
        return []
    if building.operating_status == INACTIVE:
        return ["open"]
    if building.operating_status == MAINTENANCE_DUE:
        return ["repair"]
    return []


def get_player_building_portfolio(db: Session, player: Player) -> list[Building]:
    return (
        db.query(Building)
        .options(
            joinedload(Building.district),
            joinedload(Building.land_parcel),
            joinedload(Building.business_blueprint),
            joinedload(Building.business),
        )
        .filter(Building.city_id == player.city_id, Building.owner_player_id == player.id)
        .order_by(Building.created_at.desc(), Building.name)
        .all()
    )


def open_building_operations(db: Session, player: Player, building_id: UUID) -> dict:
    building = db.query(Building).filter(Building.id == building_id).with_for_update().first()
    if not building or building.city_id != player.city_id:
        return {"success": False, "message": "Будівлю не знайдено."}

    if building.owner_player_id != player.id:
        return {"success": False, "message": "Відкрити можна лише власну будівлю."}

    if building.status != BUILT:
        return {"success": False, "message": "Відкрити можна лише готову будівлю."}

    if building.operating_status == ACTIVE:
        return {"success": False, "message": "Будівля вже працює."}

    if building.operating_status != INACTIVE:
        return {"success": False, "message": "Будівля зараз не готова до відкриття."}

    fee = get_building_opening_fee(building)
    if money(player.balance) < fee:
        return {"success": False, "message": f"Недостатньо коштів для відкриття будівлі! Потрібно: {fee:.2f} ₴."}

    city = db.query(City).filter(City.id == player.city_id).first()
    if not city:
        return {"success": False, "message": "Місто не знайдено"}

    if fee > money("0.00"):
        debit(db, player, "balance", fee)
        credit(db, city, "treasury_balance", fee)
        log_transaction(
            db,
            city.id,
            sender_id=player.id,
            sender_type="player",
            receiver_id=city.id,
            receiver_type="treasury",
            amount=float(fee),
            tax=0.0,
            purpose="building_opening_fee",
        )

    business = building.business
    business_type = (
        building.business_blueprint.business_type
        if building.business_blueprint
        else BUSINESS_PROJECT_TYPES.get(building.project_type)
    )
    if business is None and business_type is not None:
        business = Business(
            city_id=building.city_id,
            name=building.name,
            type=business_type,
            owner_player_id=player.id,
            owner_share_pct=100.00,
            cash_balance=0.00,
            status="active",
        )
        db.add(business)
        db.flush()
        building.business_id = business.id

    building.operating_status = ACTIVE
    db.commit()
    db.refresh(building)
    if building.business_id:
        db.refresh(building.business)

    return {
        "success": True,
        "message": f"Будівлю '{building.name}' відкрито для роботи.",
        "building": building,
        "opening_fee": float(fee),
    }


def repair_building_operations(db: Session, player: Player, building_id: UUID) -> dict:
    building = db.query(Building).filter(Building.id == building_id).with_for_update().first()
    if not building or building.city_id != player.city_id:
        return {"success": False, "message": "Будівлю не знайдено."}

    if building.owner_player_id != player.id:
        return {"success": False, "message": "Ремонтувати можна лише власну будівлю."}

    if building.status != BUILT:
        return {"success": False, "message": "Ремонтувати можна лише готову будівлю."}

    if building.operating_status == ACTIVE:
        return {"success": False, "message": "Будівля вже працює."}

    if building.operating_status == INACTIVE:
        return {"success": False, "message": "Будівля ще не відкрита для роботи."}

    if building.operating_status != MAINTENANCE_DUE:
        return {"success": False, "message": "Будівля зараз не потребує ремонту."}

    fee = get_building_repair_fee(building)
    if money(player.balance) < fee:
        return {"success": False, "message": f"Недостатньо коштів для ремонту будівлі! Потрібно: {fee:.2f} ₴."}

    city = db.query(City).filter(City.id == player.city_id).first()
    if not city:
        return {"success": False, "message": "Місто не знайдено"}

    debit(db, player, "balance", fee)
    credit(db, city, "treasury_balance", fee)
    log_transaction(
        db,
        city.id,
        sender_id=player.id,
        sender_type="player",
        receiver_id=city.id,
        receiver_type="treasury",
        amount=float(fee),
        tax=0.0,
        purpose=BUILDING_REPAIR_PURPOSE,
    )
    building.operating_status = ACTIVE

    db.commit()
    db.refresh(building)

    return {
        "success": True,
        "message": f"Будівлю '{building.name}' відремонтовано і повернуто в роботу.",
        "building": building,
        "repair_fee": float(fee),
    }


def process_daily_building_upkeep(db: Session, city: City) -> dict:
    stats = {
        "building_upkeep_charged": 0.0,
        "buildings_upkeep_charged": 0,
        "buildings_upkeep_failed": 0,
    }

    buildings = (
        db.query(Building)
        .filter(
            Building.city_id == city.id,
            Building.status == BUILT,
            Building.operating_status == ACTIVE,
        )
        .all()
    )

    for building in buildings:
        blueprint = building.business_blueprint
        if not blueprint:
            continue

        upkeep = money(blueprint.upkeep_daily)
        if upkeep <= money("0.00"):
            continue

        sender = None
        sender_type = ""
        if building.business and money(building.business.cash_balance) >= upkeep:
            sender = building.business
            sender_type = "business"
            debit(db, building.business, "cash_balance", upkeep)
        elif building.owner and money(building.owner.balance) >= upkeep:
            sender = building.owner
            sender_type = "player"
            debit(db, building.owner, "balance", upkeep)
        else:
            building.operating_status = MAINTENANCE_DUE
            stats["buildings_upkeep_failed"] += 1
            continue

        credit(db, city, "treasury_balance", upkeep)
        log_transaction(
            db,
            city.id,
            sender_id=sender.id,
            sender_type=sender_type,
            receiver_id=city.id,
            receiver_type="treasury",
            amount=float(upkeep),
            tax=0.0,
            purpose=BUILDING_UPKEEP_PURPOSE,
        )
        stats["building_upkeep_charged"] = float(money(stats["building_upkeep_charged"]) + upkeep)
        stats["buildings_upkeep_charged"] += 1

    return stats
