import os
from decimal import Decimal

import pytest

from backend.app.models import (
    BankLoan,
    Business,
    Cartel,
    City,
    InsurancePolicy,
    Job,
    LaborUnion,
    Player,
    PoliceRecord,
    TransactionModelLog,
)
from backend.app.schemas.service_results import (
    FakeDiplomaPurchaseServiceResult,
    InsurancePolicyPurchaseServiceResult,
    LaborUnionStrikeServiceResult,
    LoanDailyServiceResult,
    LobbyFundDonationServiceResult,
    PoliceAuditBustedServiceResult,
)
from backend.app.seed import seed_initial_data
from backend.app.services.advanced import (
    buy_insurance_policy,
    donate_to_lobby_fund,
    process_daily_loan_installments_and_collectors,
    toggle_labor_union_strike,
)
from backend.app.services.economy import process_shift_work
from backend.app.services.education import purchase_fake_diploma, run_police_audit
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def test_fake_diploma_purchase_and_audit_do_not_create_treasury_money():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="fake-diploma-player",
            balance=Decimal("450.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        starting_treasury = Decimal(str(city.treasury_balance))
        purchase_result = purchase_fake_diploma(db, str(player.id))

        assert purchase_result["success"] is True
        FakeDiplomaPurchaseServiceResult.model_validate(purchase_result)
        db.refresh(player)
        db.refresh(city)
        assert Decimal(str(player.balance)) == Decimal("100.00")
        assert Decimal(str(city.treasury_balance)) == starting_treasury
        assert player.education_level == "College"
        assert player.diploma_verified is False
        assert (
            db.query(PoliceRecord).filter(PoliceRecord.player_id == player.id).count()
            == 1
        )

        purchase_log = (
            db.query(TransactionModelLog)
            .filter(TransactionModelLog.purpose == "fake_diploma_purchase")
            .one()
        )
        assert purchase_log.sender_id == player.id
        assert purchase_log.sender_type == "player"
        assert purchase_log.receiver_id == city.id
        assert purchase_log.receiver_type == "system"
        assert purchase_log.amount == Decimal("350.00")

        audit_result = run_police_audit(db, str(player.id))

        assert audit_result["busted"] is True
        PoliceAuditBustedServiceResult.model_validate(audit_result)
        db.refresh(player)
        db.refresh(city)
        assert Decimal(str(player.balance)) == Decimal("0.00")
        assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal(
            "100.00"
        )
        assert player.education_level == "High School"
        assert player.diploma_verified is True

        fine_log = (
            db.query(TransactionModelLog)
            .filter(TransactionModelLog.purpose == "fake_diploma_fine")
            .one()
        )
        assert fine_log.sender_id == player.id
        assert fine_log.sender_type == "player"
        assert fine_log.receiver_id == city.id
        assert fine_log.receiver_type == "treasury"
        assert fine_log.amount == Decimal("100.00")
    finally:
        db.close()


def test_insurance_policy_moves_premium_from_player_to_provider():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        target_business = db.query(Business).filter(Business.type == "shop").one()
        provider = db.query(Business).filter(Business.type == "utility_housing").one()
        player = Player(
            city_id=city.id,
            username="insured-player",
            balance=Decimal("500.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        starting_provider_cash = Decimal(str(provider.cash_balance))
        result = buy_insurance_policy(
            db, str(player.id), str(target_business.id), str(provider.id), 1000.0, 75.0
        )

        assert result["success"] is True
        InsurancePolicyPurchaseServiceResult.model_validate(result)
        db.refresh(player)
        db.refresh(provider)
        assert Decimal(str(player.balance)) == Decimal("425.00")
        assert Decimal(str(provider.cash_balance)) == starting_provider_cash + Decimal(
            "75.00"
        )
        assert (
            db.query(InsurancePolicy)
            .filter(InsurancePolicy.player_id == player.id)
            .count()
            == 1
        )

        premium_log = (
            db.query(TransactionModelLog)
            .filter(TransactionModelLog.purpose == "insurance_premium_initial")
            .one()
        )
        assert premium_log.sender_id == player.id
        assert premium_log.sender_type == "player"
        assert premium_log.receiver_id == provider.id
        assert premium_log.receiver_type == "business"
        assert premium_log.amount == Decimal("75.00")
    finally:
        db.close()


def test_loan_installments_and_collector_seizure_transfer_available_money_to_treasury():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        payer = Player(
            city_id=city.id,
            username="loan-payer",
            balance=Decimal("100.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        delinquent = Player(
            city_id=city.id,
            username="loan-delinquent",
            balance=Decimal("40.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add_all([payer, delinquent])
        db.flush()
        paid_loan = BankLoan(
            player_id=payer.id,
            principal_amount=Decimal("200.00"),
            remaining_debt=Decimal("200.00"),
            daily_payment=Decimal("80.00"),
            status="active",
        )
        seized_loan = BankLoan(
            player_id=delinquent.id,
            principal_amount=Decimal("200.00"),
            remaining_debt=Decimal("200.00"),
            daily_payment=Decimal("80.00"),
            status="active",
        )
        db.add_all([paid_loan, seized_loan])
        db.commit()

        starting_treasury = Decimal(str(city.treasury_balance))
        paid_result = process_daily_loan_installments_and_collectors(db, str(payer.id))
        seized_result = process_daily_loan_installments_and_collectors(
            db, str(delinquent.id)
        )
        assert paid_result["success"] is True
        assert seized_result["success"] is True
        LoanDailyServiceResult.model_validate(paid_result)
        LoanDailyServiceResult.model_validate(seized_result)

        db.refresh(payer)
        db.refresh(delinquent)
        db.refresh(paid_loan)
        db.refresh(seized_loan)
        db.refresh(city)
        assert Decimal(str(payer.balance)) == Decimal("20.00")
        assert Decimal(str(delinquent.balance)) == Decimal("20.00")
        assert Decimal(str(paid_loan.remaining_debt)) == Decimal("120.00")
        assert Decimal(str(seized_loan.remaining_debt)) == Decimal("180.00")
        assert paid_loan.status == "active"
        assert seized_loan.status == "delinquent"
        assert Decimal(str(city.treasury_balance)) == starting_treasury + Decimal(
            "100.00"
        )

        repayment_log = (
            db.query(TransactionModelLog)
            .filter(TransactionModelLog.purpose == "loan_repayment")
            .one()
        )
        assert repayment_log.amount == Decimal("80.00")
        seizure_log = (
            db.query(TransactionModelLog)
            .filter(TransactionModelLog.purpose == "collector_debt_seizure")
            .one()
        )
        assert seizure_log.amount == Decimal("20.00")
    finally:
        db.close()


def test_labor_union_strike_blocks_worker_shift():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        job = (
            db.query(Job)
            .filter(Job.min_education == "High School")
            .order_by(Job.salary_per_hour)
            .first()
        )
        business = db.query(Business).filter(Business.id == job.business_id).one()
        player = Player(
            city_id=city.id,
            username="strike-worker",
            balance=Decimal("100.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.flush()
        job.filled_by_player_id = player.id
        db.commit()

        strike_result = toggle_labor_union_strike(
            db, str(business.id), "Працівники MVP"
        )

        assert strike_result["success"] is True
        LaborUnionStrikeServiceResult.model_validate(strike_result)
        assert strike_result["strike_active"] is True

        union = db.query(LaborUnion).filter(LaborUnion.business_id == business.id).one()
        assert union.strike_active is True
        assert union.strike_ends_at is not None

        work_result = process_shift_work(db, str(player.id))
        assert work_result["success"] is False
        assert "СТРАЙК" in work_result["message"]
    finally:
        db.close()


def test_lobby_fund_donation_triggers_property_tax_cut_and_logs_transfer():
    db = make_test_session(TEST_DATABASE_URL)
    try:
        seed_initial_data(db)

        city = db.query(City).first()
        player = Player(
            city_id=city.id,
            username="lobby-donor",
            balance=Decimal("6000.00"),
            energy=100,
            mood=100,
            education_level="High School",
        )
        db.add(player)
        db.commit()

        starting_tax_rate = Decimal(str(city.tax_rate_property))
        result = donate_to_lobby_fund(
            db, "Ритейл Картель", str(city.id), "retail", str(player.id), 5000.0
        )

        assert result["success"] is True
        LobbyFundDonationServiceResult.model_validate(result)
        assert result["lobby_action"] is True

        db.refresh(player)
        db.refresh(city)
        cartel = (
            db.query(Cartel)
            .filter(Cartel.city_id == city.id, Cartel.industry_type == "retail")
            .one()
        )
        assert Decimal(str(player.balance)) == Decimal("1000.00")
        assert Decimal(str(cartel.lobby_fund)) == Decimal("0.00")
        assert Decimal(str(city.tax_rate_property)) == max(
            Decimal("0.50"), starting_tax_rate - Decimal("2.00")
        )

        donation_log = (
            db.query(TransactionModelLog)
            .filter(TransactionModelLog.purpose == "lobby_fund_donation")
            .one()
        )
        assert donation_log.sender_id == player.id
        assert donation_log.sender_type == "player"
        assert donation_log.receiver_id == cartel.id
        assert donation_log.receiver_type == "business"
        assert donation_log.amount == Decimal("5000.00")
    finally:
        db.close()
