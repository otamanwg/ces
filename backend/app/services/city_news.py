from sqlalchemy.orm import Session

from backend.app.models import Business, City, Hostel, Player


def build_city_news(db: Session, city: City) -> list[dict]:
    buyable_count = (
        db.query(Business)
        .filter(
            Business.city_id == city.id,
            Business.owner_player_id.is_(None),
            Business.type.in_(["shop", "factory", "private_hostel"]),
            Business.status == "active",
        )
        .count()
    )
    owned_count = db.query(Business).filter(Business.city_id == city.id, Business.owner_player_id.isnot(None)).count()
    hungry_count = db.query(Player).filter(Player.city_id == city.id, Player.hunger >= 70).count()
    homeless_count = (
        db.query(Player)
        .outerjoin(Hostel, Hostel.tenant_player_id == Player.id)
        .filter(Player.city_id == city.id, Hostel.id.is_(None))
        .count()
    )

    news: list[dict] = []
    if buyable_count:
        news.append(
            {
                "type": "business_market",
                "title": "Міський ринок бізнесів",
                "message": f"Доступно бізнесів для купівлі: {buyable_count}.",
            }
        )
    if owned_count:
        news.append(
            {
                "type": "business_ownership",
                "title": "Приватний сектор",
                "message": f"Гравці вже володіють бізнесами: {owned_count}.",
            }
        )
    if hungry_count:
        news.append(
            {
                "type": "needs",
                "title": "Побутові потреби",
                "message": f"Гравців із високим голодом: {hungry_count}.",
            }
        )
    if homeless_count:
        news.append(
            {
                "type": "housing",
                "title": "Житло",
                "message": f"Гравців без житла: {homeless_count}.",
            }
        )
    if float(city.inflation_rate or 0) > 0:
        news.append(
            {
                "type": "inflation",
                "title": "Інфляція",
                "message": f"Інфляція міста: {float(city.inflation_rate):.1f}%.",
            }
        )

    return news


def build_day_tick_news(stats: dict) -> list[dict]:
    news = [
        {
            "type": "day_tick",
            "title": "Новий день",
            "message": f"Оновлено гравців: {stats['players_updated']}.",
        }
    ]
    if stats.get("homeless_players", 0) > 0:
        news.append(
            {
                "type": "housing",
                "title": "Ніч без житла",
                "message": f"Гравців без житла: {stats['homeless_players']}. Настрій знижено.",
            }
        )
    if stats.get("hungry_players", 0) > 0:
        news.append(
            {
                "type": "needs",
                "title": "Голод",
                "message": f"Гравців із критичним голодом: {stats['hungry_players']}.",
            }
        )
    return news
