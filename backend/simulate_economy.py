# Скрипт симуляції економічного циклу міста для тестування MVP
# Файл: backend/simulate_economy.py

import random
import time


class EconomySimulator:
    def __init__(self):
        # Початкові налаштування міста
        self.city_name = "Київ-Нейтральний"
        self.treasury_balance = 50000.00  # Скарбниця міста
        self.tax_rate_income = 0.10  # Прибутковий податок (10%)
        self.inflation_rate = 0.0  # Стартова інфляція

        # Список гравців міста
        self.players = [
            {
                "name": "Богдан (Новачок)",
                "balance": 500.0,
                "energy": 100,
                "mood": 100,
                "hourly_wage": 25.0,
                "rent": 15.0,
                "education": "High School",
            },
            {
                "name": "Олена (Менеджер)",
                "balance": 1200.0,
                "energy": 100,
                "mood": 100,
                "hourly_wage": 45.0,
                "rent": 25.0,
                "education": "College",
            },
            {
                "name": "Дмитро (Інвестор)",
                "balance": 5000.0,
                "energy": 100,
                "mood": 100,
                "hourly_wage": 80.0,
                "rent": 50.0,
                "education": "University",
            },
        ]

        # Комунальні та інші витрати міста
        self.utility_maintenance_cost = 80.00  # Витрати скарбниці на підтримку ЖКГ за хід

    def get_total_circulation(self) -> float:
        """Повертає загальну грошову масу в руках гравців"""
        return sum(p["balance"] for p in self.players)

    def calculate_inflation(self, initial_circulation: float):
        """Динамічний розрахунок інфляції на основі збільшення грошової маси в обігу"""
        current_circulation = self.get_total_circulation()
        growth = (current_circulation - initial_circulation) / initial_circulation

        if growth > 0.05:  # Якщо грошова маса виросла більш ніж на 5%
            self.inflation_rate = round(growth * 100, 2)
        else:
            self.inflation_rate = 0.0

    def trigger_disaster(self):
        """Випадкова стихійна подія (дефляційний інструмент)"""
        disasters = [
            {
                "name": "Прорив міського водоканалу 💧",
                "cost_treasury": 1500.0,
                "cost_player": 100.0,
                "desc": "Комунальна аварія вимагає фінансування з казенних коштів на ремонт та змушує гравців сплатити за позаплановий виклик сантехніка.",
            },
            {
                "name": "Локальний неврожай у регіоні 🌾",
                "cost_treasury": 500.0,
                "cost_player": 200.0,
                "desc": "Ціни на продукти харчування в магазинах зростають. Скарбниця виділяє дотації, гравці витрачають більше на відновлення енергії.",
            },
            {
                "name": "Аварія електромережі міста ⚡",
                "cost_treasury": 1000.0,
                "cost_player": 50.0,
                "desc": "Електрика вимкнулась на кілька годин, знижуючи настрій та вимагаючи казенного ремонту.",
            },
        ]

        event = random.choice(disasters)
        print(f"\n⚠️  [ПОДІЯ]: {event['name']}")
        print(f"   Опис: {event['desc']}")

        # Списання зі Скарбниці
        self.treasury_balance -= event["cost_treasury"]

        # Списання з гравців
        for p in self.players:
            p["balance"] = max(0.0, p["balance"] - event["cost_player"])
            p["mood"] = max(30, p["mood"] - 20)

        print(
            f"   Наслідки: Скарбниця втратила {event['cost_treasury']} грн, кожен гравець витратив {event['cost_player']} грн на усунення наслідків."
        )

    def run_shift_cycle(self, cycle_num: int, initial_circulation: float):
        """Запуск одного повного циклу (зміна роботи + списання оренди/податків)"""
        print(f"\n=== ЦИКЛ {cycle_num} ===")

        # 1. Робота (заробіток брутто та витрата енергії)
        for p in self.players:
            if p["energy"] >= 30:
                hours_worked = 8
                gross_earned = p["hourly_wage"] * hours_worked
                energy_spent = 35

                p["balance"] += gross_earned
                p["energy"] -= energy_spent
                print(f"🔨 {p['name']} відпрацював зміну: +{gross_earned} грн (Брутто), -{energy_spent} Енергії")
            else:
                print(f"❌ {p['name']} занадто втомлений для роботи! (Енергія: {p['energy']})")

        # 2. Оподаткування та оренда (Оплата житла та стягнення податку)
        for p in self.players:
            # Оплата оренди хостелу / квартири
            p["balance"] = max(0.0, p["balance"] - p["rent"])
            # В MVP оренда йде в Скарбницю міста (якщо житло державне)
            self.treasury_balance += p["rent"]

            # Розрахунок прибуткового податку
            income = p["hourly_wage"] * 8 if p["energy"] >= 65 else 0.0  # якщо працював
            tax = income * self.tax_rate_income
            p["balance"] = max(0.0, p["balance"] - tax)
            self.treasury_balance += tax

            print(f"💸 {p['name']} сплатив: {p['rent']} грн за житло, {round(tax, 2)} грн прибуткового податку")

        # 3. Відпочинок у хостелі (відновлення енергії за гроші)
        for p in self.players:
            rest_cost = 20.0
            if p["balance"] >= rest_cost:
                p["balance"] -= rest_cost
                p["energy"] = min(100, p["energy"] + 40)
                p["mood"] = min(100, p["mood"] + 10)
                self.treasury_balance += rest_cost  # кошти за обслуговування хостелу
                print(f"🛌 {p['name']} відпочив у хостелі: -{rest_cost} грн, +40 Енергії, +10 Настрою")
            else:
                p["energy"] = min(100, p["energy"] + 10)  # безкоштовний поганий сон
                p["mood"] = max(10, p["mood"] - 15)
                print(f"⚠️ {p['name']} не мав грошей на нормальний відпочинок! Енергія відновлена погано, настрій впав.")

        # 4. Витрати міста на ЖКГ
        self.treasury_balance -= self.utility_maintenance_cost
        print(f"🏛️ Скарбниця міста підтримала ЖКГ: -{self.utility_maintenance_cost} грн")

        # 5. Розрахунок інфляції
        self.calculate_inflation(initial_circulation)

        # Вивід статусів
        print("\n📊 СТАТИСТИКА МІСТА:")
        print(f"   Казна: {round(self.treasury_balance, 2)} грн")
        print(f"   Загалом грошей у гравців: {round(self.get_total_circulation(), 2)} грн")
        print(f"   Рівень інфляції: {self.inflation_rate}%")

        for p in self.players:
            print(
                f"   👤 {p['name']}: Баланс = {round(p['balance'], 2)} грн | Енергія = {p['energy']}% | Настрій = {p['mood']}%"
            )


# Запуск тесту
if __name__ == "__main__":
    sim = EconomySimulator()
    initial_circulation = sim.get_total_circulation()

    print("🚀 СТАРТ СИМУЛЯЦІЇ ЕКОНОМІКИ МІСТА")
    print(f"Початкова казна: {sim.treasury_balance} грн")
    print(f"Початкова маса грошей в обігу: {initial_circulation} грн\n")

    for cycle in range(1, 4):
        sim.run_shift_cycle(cycle, initial_circulation)
        time.sleep(1)

    # Спровокувати випадкове лихо для перевірки дефляції на 4-му циклі
    sim.trigger_disaster()
    sim.run_shift_cycle(4, initial_circulation)
