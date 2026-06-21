"""Phase G6-G10 day tick integration.

Wires post-MVP gameplay systems into the main game_day_tick loop:
- G8 Police: auto-patrol for officers with assigned district.
- G8 Press: tick investigations (evidence accumulation).
- G9 Shadow: shadow business income, discovery checks, fraud offers,
  monthly criminal_rep decay.
- G10 Education: daily energy consumption + scholarship + auto-completion.

All integrations are defensive — if no relevant records exist, they
silently no-op. This keeps the tick stable for cities that haven't
engaged with these systems yet.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.models import (
    City,
    Education,
    Player,
    PoliceOfficer,
    PressInvestigation,
    ShadowBusiness,
)

logger = logging.getLogger("PhaseG6G10Tick")

# Education auto-completion: check if enrolled_at + duration_days <= now
EDUCATION_COMPLETION_CHECK = True

# Criminal rep decay: once per 30 game days
CRIMINAL_REP_DECAY_INTERVAL_DAYS = 30


def run_g8_police_tick(db: Session, city: City, game_day: int) -> dict:
    """Auto-patrol for all active officers with an assigned district."""
    from backend.app.models import CityDistrict
    from backend.app.services.police_service import patrol_district

    officers = (
        db.query(PoliceOfficer)
        .filter(
            PoliceOfficer.city_id == city.id,
            PoliceOfficer.is_active.is_(True),
            PoliceOfficer.patrol_district_id.is_not(None),
        )
        .all()
    )
    patrols = 0
    events = 0
    for officer in officers:
        district = db.query(CityDistrict).filter(CityDistrict.id == officer.patrol_district_id).first()
        if district is None:
            continue
        try:
            result = patrol_district(db, officer, district, game_day)
            if result.get("event") != "empty":
                events += 1
            patrols += 1
        except Exception as e:  # noqa: BLE001 — defensive in tick
            logger.warning("Police patrol failed for officer %s: %s", officer.id, e)
    db.flush()
    return {"patrols": patrols, "events": events}


def run_g8_press_tick(db: Session, city: City, game_day: int) -> dict:
    """Tick all active (unpublished) press investigations."""
    from backend.app.services.press_service import tick_investigation

    investigations = db.query(PressInvestigation).filter(PressInvestigation.is_published.is_(False)).all()
    ticked = 0
    ready_to_publish = 0
    for inv in investigations:
        try:
            result = tick_investigation(db, inv)
            ticked += 1
            if result.get("can_publish"):
                ready_to_publish += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("Press tick failed for investigation %s: %s", inv.id, e)
    db.flush()
    return {"investigations_ticked": ticked, "ready_to_publish": ready_to_publish}


def run_g9_shadow_tick(db: Session, city: City, game_day: int) -> dict:
    """Shadow businesses: income, discovery checks, fraud offers, rep decay."""
    from backend.app.services.shadow_service import (
        check_discovery,
        decay_criminal_rep,
        offer_fraud,
        shadow_business_income,
    )

    # Shadow business income + discovery
    shadow_biz = db.query(ShadowBusiness).filter(ShadowBusiness.is_discovered.is_(False)).all()
    biz_income_count = 0
    discoveries = 0
    for biz in shadow_biz:
        try:
            owner = db.query(Player).filter(Player.id == biz.owner_id).first()
            if owner is None:
                continue
            shadow_business_income(db, biz, game_day)
            biz_income_count += 1
            disc_result = check_discovery(db, biz, owner)
            if disc_result.get("discovered"):
                discoveries += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("Shadow biz tick failed for %s: %s", biz.id, e)
    db.flush()

    # Fraud offers for all players in city
    players = db.query(Player).filter(Player.city_id == city.id).all()
    fraud_offers = 0
    for player in players:
        try:
            result = offer_fraud(db, player, game_day)
            if result.get("offered"):
                fraud_offers += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("Fraud offer failed for player %s: %s", player.id, e)

    # Monthly criminal_rep decay (every 30 game days)
    decay_count = 0
    if game_day > 0 and game_day % CRIMINAL_REP_DECAY_INTERVAL_DAYS == 0:
        for player in players:
            if player.criminal_rep > 0:
                try:
                    decay_criminal_rep(db, player)
                    decay_count += 1
                except Exception as e:  # noqa: BLE001
                    logger.warning("Rep decay failed for player %s: %s", player.id, e)
    db.flush()
    return {
        "shadow_biz_income": biz_income_count,
        "discoveries": discoveries,
        "fraud_offers": fraud_offers,
        "rep_decays": decay_count,
    }


def run_g10_education_tick(db: Session, city: City, game_day: int) -> dict:
    """Education: daily energy/scholarship + auto-completion check."""
    from backend.app.services.education_service import COURSES, complete_education, daily_tick

    players = db.query(Player).filter(Player.city_id == city.id).all()
    ticked = 0
    completed = 0
    for player in players:
        active = db.query(Education).filter(Education.player_id == player.id, Education.status == "enrolled").all()
        if not active:
            continue
        try:
            daily_tick(db, player, game_day)
            ticked += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("Education daily tick failed for player %s: %s", player.id, e)

        # Auto-complete courses past duration
        if EDUCATION_COMPLETION_CHECK:
            now = datetime.now(UTC)
            for edu in active:
                info = COURSES.get(edu.course)
                if info is None:
                    continue
                enrolled = edu.enrolled_at
                if enrolled is None:
                    continue
                # Make enrolled tz-aware if needed
                if enrolled.tzinfo is None:
                    enrolled = enrolled.replace(tzinfo=UTC)
                if now >= enrolled + timedelta(days=info["duration_days"]):
                    try:
                        complete_education(db, edu)
                        completed += 1
                    except Exception as e:  # noqa: BLE001
                        logger.warning("Education auto-complete failed for %s: %s", edu.id, e)
    db.flush()
    return {"education_ticked": ticked, "education_completed": completed}


def run_g6_to_g10_tick(db: Session, city: City, game_day: int) -> dict:
    """Run all G6-G10 day tick integrations.

    Returns aggregate stats for logging/news.
    """
    stats: dict = {}
    try:
        stats["police"] = run_g8_police_tick(db, city, game_day)
    except Exception as e:  # noqa: BLE001
        logger.error("G8 police tick failed: %s", e)
        stats["police"] = {"error": str(e)}
    try:
        stats["press"] = run_g8_press_tick(db, city, game_day)
    except Exception as e:  # noqa: BLE001
        logger.error("G8 press tick failed: %s", e)
        stats["press"] = {"error": str(e)}
    try:
        stats["shadow"] = run_g9_shadow_tick(db, city, game_day)
    except Exception as e:  # noqa: BLE001
        logger.error("G9 shadow tick failed: %s", e)
        stats["shadow"] = {"error": str(e)}
    try:
        stats["education"] = run_g10_education_tick(db, city, game_day)
    except Exception as e:  # noqa: BLE001
        logger.error("G10 education tick failed: %s", e)
        stats["education"] = {"error": str(e)}
    return stats
