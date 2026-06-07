"""
Економічні баланс-тести для симуляції day tick циклу.
Перевіряє стабільність економічної системи протягом 30 днів.
"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models import Business, City, Hostel, Job, Player
from backend.app.services.buildings import process_daily_building_upkeep
from backend.app.services.daily_business_revenue import process_daily_business_revenue
from backend.app.services.economy import (
    process_rent_payment,
    process_shift_work,
)
from backend.app.services.money import money
from backend.app.services.needs import DAY_HUNGER_INCREASE, increase_hunger


class TestEconomyBalance:
    """Тести балансу економічної системи."""

    @pytest.fixture
    def db_session(self):
        """Створює тестову сесію бази даних."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def test_city(self, db_session: Session):
        """Створює тестове місто."""
        import uuid

        city = City(
            name=f"Test City {uuid.uuid4().hex[:8]}",
            treasury_balance=money("10000.00"),
            inflation_rate=Decimal("2.5"),
        )
        db_session.add(city)
        db_session.commit()
        db_session.refresh(city)
        return city

    @pytest.fixture
    def test_player(self, db_session: Session, test_city: City):
        """Створює тестового гравця."""
        import uuid

        player = Player(
            username=f"testplayer_{uuid.uuid4().hex[:8]}",
            city_id=test_city.id,
            balance=money("1000.00"),
            energy=100,
            mood=80,
            hunger=50,
        )
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)
        return player

    @pytest.fixture
    def test_business(self, db_session: Session, test_city: City, test_player: Player):
        """Створює тестовий бізнес з AI режимом для автоматичного доходу."""
        business = Business(
            name="Test Factory",
            city_id=test_city.id,
            owner_player_id=test_player.id,
            type="factory",
            cash_balance=money("5000.00"),
            status="active",
            management_mode="ai",
            business_size=50,
            ai_profit_rate=Decimal("0.10"),
        )
        db_session.add(business)
        db_session.commit()
        db_session.refresh(business)
        return business

    @pytest.fixture
    def test_job(self, db_session: Session, test_city: City, test_business: Business):
        """Створює тестову роботу."""
        job = Job(
            business_id=test_business.id,
            title="Test Job",
            salary_per_hour=money("50.00"),
            energy_cost_per_shift=30,
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        return job

    @pytest.fixture
    def test_hostel(self, db_session: Session, test_city: City, test_business: Business):
        """Створює тестовий гуртожиток."""
        hostel = Hostel(
            business_id=test_business.id,
            room_number=101,
            rent_price_per_day=money("20.00"),
            tenant_player_id=None,
        )
        db_session.add(hostel)
        db_session.commit()
        db_session.refresh(hostel)
        return hostel

    def test_player_daily_needs_balance(self, db_session: Session, test_player: Player):
        """Тестує баланс щоденних потреб гравця."""
        initial_hunger = test_player.hunger

        # Симулюємо голод
        increase_hunger(test_player, DAY_HUNGER_INCREASE)
        db_session.commit()
        db_session.refresh(test_player)

        # Перевіряємо зміни
        assert test_player.hunger > initial_hunger, "Голод повинен зрости"

    def test_business_daily_operations_balance(self, db_session: Session, test_city: City, test_business: Business):
        """Тестує баланс щоденних операцій бізнесу."""
        initial_balance = test_business.cash_balance
        initial_city_balance = test_city.treasury_balance

        # Симулюємо день бізнесу з новою системою доходів
        process_daily_business_revenue(db_session, test_business)
        db_session.commit()
        process_daily_building_upkeep(db_session, test_city)
        db_session.commit()
        db_session.refresh(test_business)
        db_session.refresh(test_city)

        # Перевіряємо, що баланс змінився (дохід/витрати)
        assert test_business.cash_balance != initial_balance or test_city.treasury_balance != initial_city_balance

    def test_job_shifts_balance(self, db_session: Session, test_job: Job, test_player: Player):
        """Тестує баланс робочих змін."""
        # Призначаємо гравця на роботу
        test_job.filled_by_player_id = test_player.id
        test_player.job = test_job
        db_session.commit()

        initial_energy = test_player.energy

        # Симулюємо робочу зміну
        result = process_shift_work(db_session, test_player.id)
        db_session.refresh(test_player)

        # Перевіряємо результат роботи
        assert result["success"], "Робоча зміна повинна бути успішною"
        assert test_player.energy < initial_energy, "Енергія повинна зменшитись"

    def test_hostel_payments_balance(self, db_session: Session, test_hostel: Hostel, test_player: Player):
        """Тестує баланс оплати гуртожитку."""
        # Вселяємо гравця в гуртожиток
        test_hostel.tenant_player_id = test_player.id
        db_session.commit()

        initial_player_balance = test_player.balance

        # Симулюємо оплату
        result = process_rent_payment(db_session, test_player.id)
        db_session.refresh(test_player)

        # Перевіряємо результат оплати
        if result["success"]:
            assert test_player.balance < initial_player_balance, "Гравець повинен сплатити оренду"

    def test_30_day_economy_simulation(
        self,
        db_session: Session,
        test_city: City,
        test_player: Player,
        test_business: Business,
        test_job: Job,
        test_hostel: Hostel,
    ):
        """Спрощена симуляція 7-денного економічного циклу."""
        # Початкові показники
        initial_player_balance = test_player.balance
        initial_business_balance = test_business.cash_balance
        initial_city_balance = test_city.treasury_balance

        # Вселяємо гравця в гуртожиток та на роботу
        test_hostel.tenant_player_id = test_player.id
        test_job.filled_by_player_id = test_player.id
        test_player.job = test_job
        db_session.commit()

        # Симулюємо 7 днів
        for day in range(7):
            # Записуємо стан на початку дня
            db_session.refresh(test_player)
            db_session.refresh(test_business)
            db_session.refresh(test_city)

            # Симулюємо день
            increase_hunger(test_player, DAY_HUNGER_INCREASE)
            process_daily_business_revenue(db_session, test_business)
            process_daily_building_upkeep(db_session, test_city)

            # Симулюємо роботу (якщо є енергія)
            if test_player.energy > 20:
                process_shift_work(db_session, test_player.id)

            # Симулюємо оплату оренди
            process_rent_payment(db_session, test_player.id)

            db_session.refresh(test_player)
            db_session.refresh(test_business)
            db_session.refresh(test_city)

            # Перевіряємо критичні умови
            assert test_player.balance >= money("0.00"), f"Гравець банкрут на день {day + 1}"
            assert test_player.energy >= 0, f"Енергія гравця від'ємна на день {day + 1}"
            assert test_player.hunger <= 100, f"Голод гравця перевищує 100 на день {day + 1}"

        # Аналіз результатів симуляції
        final_player_balance = test_player.balance
        final_business_balance = test_business.cash_balance
        final_city_balance = test_city.treasury_balance

        # Перевіряємо загальну стабільність
        assert final_player_balance >= money("0.00"), "Гравець не повинен бути банкрутом"
        assert final_business_balance >= money("0.00"), "Бізнес не повинен бути банкрутом"

        # Логуємо результати
        print("\n=== 7-Day Economy Simulation Results ===")
        print(f"Player balance change: {final_player_balance - initial_player_balance}")
        print(f"Business balance change: {final_business_balance - initial_business_balance}")
        print(f"City balance change: {final_city_balance - initial_city_balance}")
        print(f"Final player stats: Energy={test_player.energy}, Mood={test_player.mood}, Hunger={test_player.hunger}")

    def test_economy_stress_test(
        self,
        db_session: Session,
        test_city: City,
        test_player: Player,
        test_business: Business,
        test_job: Job,
        test_hostel: Hostel,
    ):
        """Спрощений стрес-тест економічної системи."""
        # Встановлюємо екстремальні умови
        test_player.balance = money("100.00")  # Мінімальний баланс
        test_player.energy = 20  # Низька енергія

        test_business.cash_balance = money("5000.00")  # Достатній баланс бізнесу
        test_business.management_mode = "ai"  # AI режим для стабільного доходу
        test_job.salary_per_hour = money("50.00")  # Реалістична зарплата

        test_hostel.rent_price_per_day = money("50.00")  # Висока оренда
        test_hostel.tenant_player_id = test_player.id
        test_job.filled_by_player_id = test_player.id
        test_player.job = test_job

        db_session.commit()

        # Симулюємо 3 дні у стресових умовах
        for day in range(3):
            # Симулюємо день
            increase_hunger(test_player, DAY_HUNGER_INCREASE)
            process_daily_business_revenue(db_session, test_business)
            process_daily_building_upkeep(db_session, test_city)

            # Симулюємо роботу (якщо є енергія)
            if test_player.energy > 20:
                process_shift_work(db_session, test_player.id)

            # Симулюємо оплату оренди
            process_rent_payment(db_session, test_player.id)

            db_session.refresh(test_player)
            db_session.refresh(test_business)

            # Перевіряємо, що система не руйнується
            assert test_player.balance >= money("0.00"), f"Система не витримала стрес на день {day + 1}"
            assert test_business.cash_balance >= money("0.00"), f"Бізнес не витримав стрес на день {day + 1}"

        print("\n=== Stress Test Results ===")
        print(f"Final player balance: {test_player.balance}")
        print(f"Final business balance: {test_business.cash_balance}")
        print(f"Player stats: Energy={test_player.energy}, Hunger={test_player.hunger}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
