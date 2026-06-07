from sqlalchemy.orm import Session

from backend.app.models import Business, City
from backend.app.repositories.business import BusinessRepository
from backend.app.repositories.player import PlayerRepository
from backend.app.schemas.mvp import CityNewsItem


def _news_item(news_type: str, title: str, message: str, severity: str, priority: int) -> dict:
    return CityNewsItem(
        type=news_type,
        title=title,
        message=message,
        severity=severity,
        priority=priority,
    ).model_dump()


def _limit_news(news: list[dict], max_items: int) -> list[dict]:
    if max_items <= 0:
        return []
    return news[:max_items]


def build_city_news(db: Session, city: City, max_items: int = 4) -> list[dict]:
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
    owned_count = BusinessRepository(db).count_owned_in_city(city.id)
    hungry_count = PlayerRepository(db).count_hungry_in_city(city.id)
    homeless_count = PlayerRepository(db).count_homeless_in_city(city.id)

    news: list[dict] = []
    if buyable_count:
        news.append(
            _news_item(
                "business_market",
                "Міський ринок бізнесів",
                f"Доступно бізнесів для купівлі: {buyable_count}.",
                "info",
                40,
            )
        )
    if owned_count:
        news.append(
            _news_item(
                "business_ownership",
                "Приватний сектор",
                f"Гравці вже володіють бізнесами: {owned_count}.",
                "info",
                30,
            )
        )
    if hungry_count:
        news.append(
            _news_item(
                "needs",
                "Побутові потреби",
                f"Гравців із високим голодом: {hungry_count}.",
                "warning",
                80,
            )
        )
    if homeless_count:
        news.append(
            _news_item(
                "housing",
                "Житло",
                f"Гравців без житла: {homeless_count}.",
                "warning",
                70,
            )
        )
    if float(city.inflation_rate or 0) > 0:
        news.append(
            _news_item(
                "inflation",
                "Інфляція",
                f"Інфляція міста: {float(city.inflation_rate):.2f}%.",
                "watch",
                60,
            )
        )

    news.sort(key=lambda item: item["priority"], reverse=True)
    return _limit_news(news, max_items)


def build_day_tick_news(stats: dict, max_items: int = 4) -> list[dict]:
    news = [
        _news_item(
            "day_tick",
            "Новий день",
            f"Оновлено гравців: {stats['players_updated']}.",
            "info",
            20,
        )
    ]
    if stats.get("homeless_players", 0) > 0:
        news.append(
            _news_item(
                "housing",
                "Ніч без житла",
                f"Гравців без житла: {stats['homeless_players']}. Настрій знижено.",
                "warning",
                70,
            )
        )
    if stats.get("hungry_players", 0) > 0:
        news.append(
            _news_item(
                "needs",
                "Голод",
                f"Гравців із критичним голодом: {stats['hungry_players']}.",
                "warning",
                80,
            )
        )
    if stats.get("buildings_upkeep_failed", 0) > 0:
        news.append(
            _news_item(
                "building_upkeep",
                "Утримання будівель",
                f"Будівель із простроченим утриманням: {stats['buildings_upkeep_failed']}.",
                "warning",
                75,
            )
        )
    if stats.get("building_upkeep_charged", 0.0) > 0:
        news.append(
            _news_item(
                "building_upkeep",
                "Утримання будівель",
                f"Списано на утримання активних будівель: {stats['building_upkeep_charged']:.2f} ₴.",
                "info",
                35,
            )
        )
    return _limit_news(news, max_items)
