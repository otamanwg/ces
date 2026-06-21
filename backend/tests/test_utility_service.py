"""
Phase G3 — тести комунальних служб як бізнесів.

Покриває:
- Utility blueprints (power_plant, water_works, waste_plant).
- Utility payments: бізнеси платять, служби отримують, платять податок.
- Bankruptcy: служба з negative balance → банкрот → екстрений контракт.
- Екстрений контракт: завищена ціна, мерія платить різницю.
- Mayor warnings: high load, low balance, no service, emergency contract.
- District metrics: реальні потужності utility замість базових 100.
- API /city/utility-status.
- Day tick інтеграція.
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from backend.app.models import Business, City, CityDistrict, UtilityEmergencyContract
from backend.app.services.business_blueprints import ensure_business_blueprints
from backend.app.services.utility_service import (
    EMERGENCY_PRICE_MULTIPLIER,
    NORMAL_PRICE_PER_UNIT,
    UTILITY_TAX_RATE,
    check_utility_bankruptcy,
    get_mayor_warnings,
    process_utility_payments,
)
from backend.tests.db import make_test_session

TEST_DATABASE_URL = os.getenv("CITY_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set CITY_TEST_DATABASE_URL to run PostgreSQL integration tests.",
)


def _make_city(db) -> City:
    city = City(
        name="UtilityTestCity",
        treasury_balance=Decimal("100000.00"),
        inflation_rate=Decimal("2.5"),
        game_day=0,
    )
    db.add(city)
    db.flush()
    return city


def _make_utility_business(
    db,
    city: City,
    *,
    service_type: str = "power",
    capacity: float = 100.0,
    cash: float = 5000.0,
    btype: str = "utility_power",
) -> Business:
    business = Business(
        city_id=city.id,
        name=f"Utility_{service_type}",
        type=btype,
        legal_form="tov",
        cash_balance=Decimal(str(cash)),
        status="active",
        utility_service_type=service_type,
        service_capacity=Decimal(str(capacity)),
        service_load=Decimal("0"),
    )
    db.add(business)
    db.flush()
    return business


def _make_regular_business(db, city: City, *, cash: float = 1000.0, btype: str = "shop") -> Business:
    business = Business(
        city_id=city.id,
        name=f"RegularBiz_{btype}",
        type=btype,
        legal_form="fop",
        cash_balance=Decimal(str(cash)),
        status="active",
    )
    db.add(business)
    db.flush()
    return business


# --- Blueprints ---


class TestUtilityBlueprints:
    def test_utility_blueprints_exist_after_seed(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            ensure_business_blueprints(db)
            db.commit()
            from backend.app.models import BusinessBlueprint

            codes = {bp.code for bp in db.query(BusinessBlueprint).all()}
            assert "power_plant" in codes
            assert "water_works" in codes
            assert "waste_plant" in codes
        finally:
            db.close()

    def test_utility_blueprints_have_utility_category(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            ensure_business_blueprints(db)
            db.commit()
            from backend.app.models import BusinessBlueprint

            for code in ("power_plant", "water_works", "waste_plant"):
                bp = db.query(BusinessBlueprint).filter(BusinessBlueprint.code == code).first()
                assert bp is not None
                assert bp.category == "utility"
        finally:
            db.close()


# --- Utility payments ---


class TestUtilityPayments:
    def test_regular_businesses_pay_utilities(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            utility = _make_utility_business(db, city, service_type="power", cash=0)
            regular = _make_regular_business(db, city, cash=100.0, btype="shop")
            db.flush()

            result = process_utility_payments(db, city.id, game_day=1)
            db.flush()
            # Shop платить 5.00 за типом
            assert result["total_collected"] == Decimal("5.00")
            assert Decimal(str(regular.cash_balance)) == Decimal("95.00")
            # Utility отримав частку
            assert Decimal(str(utility.cash_balance)) > 0
        finally:
            db.close()

    def test_utility_pays_tax_to_treasury(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            initial_treasury = Decimal(str(city.treasury_balance))
            _make_utility_business(db, city, service_type="power", cash=0)
            _make_regular_business(db, city, cash=100.0, btype="shop")
            db.flush()

            result = process_utility_payments(db, city.id, game_day=1)
            db.flush()
            db.refresh(city)
            # Податок = 10% від зібраного
            expected_tax = result["total_collected"] * UTILITY_TAX_RATE
            assert result["tax_to_treasury"] == expected_tax
            assert Decimal(str(city.treasury_balance)) == initial_treasury + expected_tax
        finally:
            db.close()

    def test_broke_business_skips_payment(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            _make_utility_business(db, city, service_type="power", cash=0)
            # Бізнес з недостатнім балансом
            _make_regular_business(db, city, cash=1.0, btype="factory")  # fee=15.00
            db.flush()

            result = process_utility_payments(db, city.id, game_day=1)
            db.flush()
            # Factory не може платити 15.00 з 1.00 → пропускає
            assert result["total_collected"] == Decimal("0.00")
        finally:
            db.close()


# --- Bankruptcy and emergency contracts ---


class TestUtilityBankruptcy:
    def test_no_service_triggers_emergency_contract(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            initial_treasury = Decimal(str(city.treasury_balance))
            # Немає power-служби → екстрений контракт
            contracts = check_utility_bankruptcy(db, city.id, game_day=1)
            db.flush()
            power_contracts = [c for c in contracts if c["service_type"] == "power"]
            assert len(power_contracts) == 1
            # Перевіряємо що контракт створено в БД
            db_contract = (
                db.query(UtilityEmergencyContract)
                .filter(
                    UtilityEmergencyContract.city_id == city.id,
                    UtilityEmergencyContract.utility_service_type == "power",
                    UtilityEmergencyContract.is_active.is_(True),
                )
                .first()
            )
            assert db_contract is not None
            assert db_contract.price_per_unit > db_contract.normal_price_per_unit
            # Мерія заплатила різницю
            db.refresh(city)
            assert Decimal(str(city.treasury_balance)) < initial_treasury
        finally:
            db.close()

    def test_active_service_prevents_emergency_contract(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            _make_utility_business(db, city, service_type="power", cash=5000.0)
            db.flush()
            contracts = check_utility_bankruptcy(db, city.id, game_day=1)
            db.flush()
            power_contracts = [c for c in contracts if c["service_type"] == "power"]
            assert len(power_contracts) == 0
        finally:
            db.close()

    def test_emergency_price_is_inflated(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            contracts = check_utility_bankruptcy(db, city.id, game_day=1)
            db.flush()
            power = [c for c in contracts if c["service_type"] == "power"][0]
            normal = NORMAL_PRICE_PER_UNIT["power"]
            expected_emergency = normal * EMERGENCY_PRICE_MULTIPLIER
            assert Decimal(str(power["price_per_unit"])) == expected_emergency
        finally:
            db.close()

    def test_existing_emergency_contract_not_duplicated(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            # Перший виклик створює контракт
            check_utility_bankruptcy(db, city.id, game_day=1)
            db.flush()
            # Другий виклик не повинен створити дублікат
            contracts = check_utility_bankruptcy(db, city.id, game_day=2)
            db.flush()
            power_contracts = [c for c in contracts if c["service_type"] == "power"]
            assert len(power_contracts) == 0
        finally:
            db.close()


# --- Mayor warnings ---


class TestMayorWarnings:
    def test_warning_for_no_service(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            warnings = get_mayor_warnings(db, city.id)
            # Для кожного типу без служби — попередження
            assert any("Немає активної служби" in w for w in warnings)
        finally:
            db.close()

    def test_warning_for_high_load(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            utility = _make_utility_business(db, city, service_type="power", capacity=100.0)
            utility.service_load = Decimal("85.0")  # 85% > 80% threshold
            db.flush()
            warnings = get_mayor_warnings(db, city.id)
            assert any("близько до ліміту" in w for w in warnings)
        finally:
            db.close()

    def test_warning_for_low_balance(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            _make_utility_business(db, city, service_type="power", cash=100.0)
            db.flush()
            warnings = get_mayor_warnings(db, city.id)
            assert any("низький баланс" in w for w in warnings)
        finally:
            db.close()

    def test_warning_for_emergency_contract(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            check_utility_bankruptcy(db, city.id, game_day=1)
            db.flush()
            warnings = get_mayor_warnings(db, city.id)
            assert any("екстрений контракт" in w for w in warnings)
        finally:
            db.close()

    def test_no_warnings_when_healthy(self):
        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            for st in ("power", "water", "waste", "housing"):
                _make_utility_business(
                    db,
                    city,
                    service_type=st,
                    capacity=100.0,
                    cash=5000.0,
                    btype=f"utility_{st}",
                )
            db.flush()
            warnings = get_mayor_warnings(db, city.id)
            # Не має бути попереджень про відсутність служби чи екстрені контракти
            assert not any("Немає активної служби" in w for w in warnings)
            assert not any("екстрений контракт" in w for w in warnings)
        finally:
            db.close()


# --- District metrics integration ---


class TestUtilityDistrictMetricsIntegration:
    def test_real_capacity_replaces_default_100(self):
        from backend.app.services.district_metrics import recalculate_district_metrics

        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            district = CityDistrict(
                city_id=city.id,
                code="test",
                name="Test",
                zone_type="residential",
                description="t",
                display_order=0,
                land_available_hectares=Decimal("10.00"),
            )
            db.add(district)
            db.flush()
            # Без utility-служб → fallback 100
            snap1 = recalculate_district_metrics(db, district, game_day=0)
            db.flush()
            power_with_default = snap1.power_supply

            # Додаємо power-службу з capacity=200
            _make_utility_business(db, city, service_type="power", capacity=200.0)
            db.flush()
            snap2 = recalculate_district_metrics(db, district, game_day=1)
            db.flush()
            # З більшою потужністю power_supply має бути вищим
            assert snap2.power_supply > power_with_default
        finally:
            db.close()


# --- API ---


class TestUtilityApi:
    def test_utility_status_endpoint_returns_data(self):
        from backend.app.api.routes.mvp import get_utility_status_endpoint

        db = make_test_session(TEST_DATABASE_URL)
        try:
            city = _make_city(db)
            _make_utility_business(db, city, service_type="power", capacity=100.0)
            db.commit()
            result = get_utility_status_endpoint(db)
            assert result["success"] is True
            data = result["data"]
            assert "services" in data
            assert "mayor_warnings" in data
            assert len(data["services"]) == 4  # power, water, waste, housing
            power = [s for s in data["services"] if s["service_type"] == "power"][0]
            assert power["active_businesses"] == 1
            assert power["total_capacity"] == 100.0
        finally:
            db.close()

    def test_utility_status_endpoint_no_city(self):
        from backend.app.api.routes.mvp import get_utility_status_endpoint

        db = make_test_session(TEST_DATABASE_URL)
        try:
            result = get_utility_status_endpoint(db)
            assert result["success"] is False
        finally:
            db.close()


# --- Day tick integration ---


class TestUtilityDayTickIntegration:
    def test_day_tick_processes_utility_payments(self):
        from backend.app.seed import seed_initial_data
        from backend.app.services.economy import game_day_tick

        db = make_test_session(TEST_DATABASE_URL)
        try:
            seed_initial_data(db)
            city = db.query(City).one()
            initial_treasury = Decimal(str(city.treasury_balance))
            result = game_day_tick(db, str(city.id))
            db.commit()
            assert result["success"] is True
            # Utility-платежі мають збільшити казну (податок)
            db.refresh(city)
            # Тільки якщо є utility-бізнеси і регулярні бізнеси
            # Seeded має ЖКГ, Водоканал, Кав'ярня — Водоканал і ЖКГ utility
            assert Decimal(str(city.treasury_balance)) != initial_treasury
        finally:
            db.close()
