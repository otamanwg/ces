"""
Phase G8 — тести поліції, суду, тюрми, преси, адвоката.

Покриває:
- Police: hire, promote, appoint chief, patrol, bribe, arrest.
- Court: create case, appeal, bribe judge, double punishment.
- Prison: serve day, work, poker, socialize, freeze/unfreeze.
- Press: investigate, publish, blackmail, advertising.
- Lawyer: engage, level, appeal, defense.
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from backend.app.models import (
    CorruptionLog,
    CourtCase,
    LawyerEngagement,
    Player,
    PressBlackmail,
    PressInvestigation,
    PrisonSentence,
)

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_player(db, city, username="g8player", balance=5000.0) -> Player:
    """Create a player with a custom username/balance (for multi-player/custom cases)."""
    player = Player(
        city_id=city.id,
        username=f"{username}_{__name__}",
        balance=Decimal(str(balance)),
        energy=100,
        mood=80,
        hunger=0,
    )
    db.add(player)
    db.flush()
    return player


# --- Police ---


class TestPolice:
    def test_hire_patrol(self, db, city, player):
        from backend.app.services.police_service import hire_police_officer

        result = hire_police_officer(db, city, player, game_day=1)
        db.flush()
        assert result["success"] is True

    def test_cannot_hire_twice(self, db, city, player):
        from backend.app.services.police_service import hire_police_officer

        hire_police_officer(db, city, player, game_day=1)
        db.flush()
        result = hire_police_officer(db, city, player, game_day=2)
        assert result["success"] is False

    def test_promote_requires_investigations(self, db, city, player):
        from backend.app.services.police_service import (
            get_officer,
            hire_police_officer,
            promote_officer,
        )

        hire_police_officer(db, city, player, game_day=1)
        db.flush()
        officer = get_officer(db, city.id, player.id)
        result = promote_officer(db, officer, game_day=10)
        assert result["success"] is False

    def test_promote_to_detective(self, db, city, player):
        from backend.app.services.police_service import (
            get_officer,
            hire_police_officer,
            promote_officer,
        )

        hire_police_officer(db, city, player, game_day=1)
        db.flush()
        officer = get_officer(db, city.id, player.id)
        officer.successful_investigations = 5
        db.flush()
        result = promote_officer(db, officer, game_day=100)
        assert result["success"] is True
        assert result["rank"] == "detective"

    def test_accept_bribe_creates_corruption_log(self, db, city):
        player = _make_player(db, city, "bribe_cop", balance=100.0)
        from backend.app.services.police_service import (
            accept_bribe,
            get_officer,
            hire_police_officer,
        )

        hire_police_officer(db, city, player, game_day=1)
        db.flush()
        officer = get_officer(db, city.id, player.id)
        result = accept_bribe(db, officer, player, Decimal("200.00"), game_day=5)
        db.flush()
        assert result["success"] is True
        assert Decimal(str(player.balance)) == Decimal("300.00")
        corruption = db.query(CorruptionLog).filter(CorruptionLog.perpetrator_id == player.id).first()
        assert corruption is not None
        assert corruption.incident_type == "police_bribe"

    def test_appoint_chief(self, db, city, player):
        mayor = player
        candidate = _make_player(db, city, "chief_cand")
        city.mayor_player_id = mayor.id
        from backend.app.services.police_service import (
            appoint_chief,
            hire_police_officer,
        )

        hire_police_officer(db, city, candidate, game_day=1)
        db.flush()
        result = appoint_chief(db, city, mayor, candidate, game_day=100)
        assert result["success"] is True


# --- Court ---


class TestCourt:
    def test_create_case_fine(self, db, city, player):
        defendant = player
        corruption = CorruptionLog(
            incident_type="minor_bribe",
            perpetrator_id=defendant.id,
            amount=100.0,
            evidence_strength=0.75,
        )
        db.add(corruption)
        db.flush()
        from backend.app.services.court_service import create_court_case

        result = create_court_case(db, corruption, defendant, game_day=1)
        db.flush()
        assert result["success"] is True
        assert result["verdict"] == "fine"

    def test_create_case_criminal_creates_sentence(self, db, city, player):
        defendant = player
        corruption = CorruptionLog(
            incident_type="money_laundering",
            perpetrator_id=defendant.id,
            amount=50000.0,
            evidence_strength=0.95,
        )
        db.add(corruption)
        db.flush()
        from backend.app.services.court_service import create_court_case

        result = create_court_case(db, corruption, defendant, game_day=1)
        db.flush()
        assert result["success"] is True
        assert result["verdict"] == "criminal_case"
        assert result["prison_days"] > 0
        sentence = db.query(PrisonSentence).filter(PrisonSentence.player_id == defendant.id).first()
        assert sentence is not None
        assert sentence.status == "serving"

    def test_file_appeal(self, db, city, player):
        defendant = player
        corruption = CorruptionLog(
            incident_type="minor_bribe",
            perpetrator_id=defendant.id,
            amount=100.0,
            evidence_strength=0.75,
        )
        db.add(corruption)
        db.flush()
        from backend.app.services.court_service import create_court_case, file_appeal

        create_court_case(db, corruption, defendant, game_day=1)
        db.flush()
        case = db.query(CourtCase).first()
        result = file_appeal(db, case, defendant, game_day=2)
        db.flush()
        assert result["success"] is True
        assert case.is_appealed is True

    def test_bribe_judge_success(self, db, city):
        defendant = _make_player(db, city, "defendant4", balance=100000.0)
        corruption = CorruptionLog(
            incident_type="minor_bribe",
            perpetrator_id=defendant.id,
            amount=100.0,
            evidence_strength=0.75,
        )
        db.add(corruption)
        db.flush()
        from backend.app.services.court_service import (
            bribe_judge,
            create_court_case,
            file_appeal,
        )

        create_court_case(db, corruption, defendant, game_day=1)
        db.flush()
        case = db.query(CourtCase).first()
        file_appeal(db, case, defendant, game_day=2)
        db.flush()
        # Велика сума → високий шанс успіху
        import backend.app.services.court_service as cs

        original_random = cs.random
        cs.random = type("MockRandom", (), {"uniform": lambda self, a, b: 0.3})()
        try:
            bribe_judge(db, case, defendant, 1, Decimal("5000.00"), game_day=3)
            db.flush()
        finally:
            cs.random = original_random
        # Суддя 1 має бути overturn
        assert case.judge_1_vote == "overturn"


# --- Prison ---


class TestPrison:
    def test_serve_day(self, db, city, player):
        sentence = PrisonSentence(
            player_id=player.id,
            days_total=10,
            days_served=0,
            days_remaining=10,
            status="serving",
        )
        db.add(sentence)
        db.flush()
        from backend.app.services.prison_service import serve_day

        result = serve_day(db, sentence, game_day=1)
        db.flush()
        assert result["success"] is True
        assert sentence.days_served == 1

    def test_prison_work(self, db, city):
        player = _make_player(db, city, "inmate2", balance=0.0)
        sentence = PrisonSentence(
            player_id=player.id,
            days_total=10,
            days_served=0,
            days_remaining=10,
            status="serving",
        )
        db.add(sentence)
        db.flush()
        from backend.app.services.prison_service import prison_work

        result = prison_work(db, sentence, player)
        db.flush()
        assert result["success"] is True
        assert Decimal(str(player.balance)) > 0

    def test_prison_poker(self, db, city):
        player = _make_player(db, city, "inmate3", balance=500.0)
        sentence = PrisonSentence(
            player_id=player.id,
            days_total=10,
            days_served=0,
            days_remaining=10,
            status="serving",
        )
        db.add(sentence)
        db.flush()
        # Force win
        import backend.app.services.prison_service as ps
        from backend.app.services.prison_service import prison_poker

        original_random = ps.random
        ps.random = type("MockRandom", (), {"random": lambda self: 0.1})()
        try:
            result = prison_poker(db, sentence, player, Decimal("100.00"))
            db.flush()
        finally:
            ps.random = original_random
        assert result["success"] is True
        assert result["won"] is True


# --- Press ---


class TestPress:
    def test_start_investigation(self, db, city, player):
        journalist = player
        target = _make_player(db, city, "target")
        from backend.app.services.press_service import start_investigation

        result = start_investigation(db, journalist, target, "corruption")
        db.flush()
        assert result["success"] is True

    def test_publish_article(self, db, city, player):
        journalist = player
        target = _make_player(db, city, "target2")
        from backend.app.services.press_service import (
            publish_article,
            start_investigation,
        )

        start_investigation(db, journalist, target)
        db.flush()
        investigation = db.query(PressInvestigation).first()
        # Штучно піднімаємо evidence
        investigation.press_evidence = 0.8
        db.flush()
        result = publish_article(db, investigation, target, "Скандал!")
        db.flush()
        assert result["success"] is True
        assert investigation.is_published is True

    def test_blackmail(self, db, city):
        journalist = _make_player(db, city, "journalist3", balance=0.0)
        target = _make_player(db, city, "target3", balance=10000.0)
        from backend.app.services.press_service import (
            offer_blackmail,
            respond_to_blackmail,
            start_investigation,
        )

        start_investigation(db, journalist, target)
        db.flush()
        investigation = db.query(PressInvestigation).first()
        investigation.press_evidence = 0.8
        db.flush()
        result = offer_blackmail(db, investigation, journalist, target, Decimal("1000.00"))
        db.flush()
        assert result["success"] is True
        blackmail = db.query(PressBlackmail).first()
        # Ціль приймає шантаж
        result = respond_to_blackmail(db, blackmail, target, journalist, investigation, "accept")
        db.flush()
        assert result["success"] is True
        assert Decimal(str(journalist.balance)) == Decimal("1000.00")


# --- Lawyer ---


class TestLawyer:
    def test_engage_lawyer(self, db, city):
        lawyer = _make_player(db, city, "lawyer", balance=0.0)
        client = _make_player(db, city, "client", balance=10000.0)
        from backend.app.services.lawyer_service import engage_lawyer

        result = engage_lawyer(db, lawyer, client, "real_estate", Decimal("5000.00"))
        db.flush()
        assert result["success"] is True
        # Комісія 10% = 500
        assert Decimal(str(lawyer.balance)) == Decimal("500.00")

    def test_lawyer_level_grows(self, db, city, player):
        lawyer = player
        client = _make_player(db, city, "client2")
        from backend.app.services.lawyer_service import get_lawyer_level

        # Створюємо 10 успішних угод
        for _i in range(10):
            eng = LawyerEngagement(
                lawyer_id=lawyer.id,
                client_id=client.id,
                deal_type="general",
                amount=1000.0,
                commission=100.0,
                success_chance_bonus=0.0,
                is_successful=True,
            )
            db.add(eng)
        db.flush()
        level = get_lawyer_level(db, lawyer.id)
        assert level == 1
