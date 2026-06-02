# Логіка додаткових ігрових механік: Профспілки (Страйки), Кредити (Колектори), Страхування та Картелі
# Файл: backend/app/services/advanced.py

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.models import Player, Business, LaborUnion, BankLoan, InsurancePolicy, Cartel, City
from backend.app.services.ledger import credit, debit, log_transaction
from backend.app.services.ids import to_uuid
from backend.app.services.money import money

def toggle_labor_union_strike(db: Session, business_id: str, union_name: str) -> dict:
    """Оголошення або завершення страйку профспілкою підприємства"""
    business_uuid = to_uuid(business_id)
    union = db.query(LaborUnion).filter(LaborUnion.business_id == business_uuid).first()
    business = db.query(Business).filter(Business.id == business_uuid).first()
    if not business:
        return {"success": False, "message": "Підприємство не знайдено"}

    if not union:
        # Якщо профспілки немає, створюємо її
        union = LaborUnion(
            business_id=business_uuid,
            name=union_name,
            strike_active=False
        )
        db.add(union)
        db.commit()

    # Тоглимо стан страйку
    union.strike_active = not union.strike_active
    
    if union.strike_active:
        union.strike_ends_at = datetime.utcnow() + timedelta(days=1) # страйк на 1 день
        message = f"✊ УВАГА! Робітники компанії '{business.name}' оголосили СТРАЙК! Робочі зміни заблоковано на 24 години."
    else:
        union.strike_ends_at = None
        message = f"🤝 Профспілка припинила страйк на '{business.name}'. Виробництво відновлено."

    db.commit()
    return {"success": True, "strike_active": union.strike_active, "message": message}

def buy_insurance_policy(db: Session, player_id: str, business_id: str, 
                           provider_business_id: str, coverage: float, premium: float) -> dict:
    """Купівля страхового полісу у страхової компанії іншого гравця"""
    player_uuid = to_uuid(player_id)
    business_uuid = to_uuid(business_id)
    provider_uuid = to_uuid(provider_business_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    provider = db.query(Business).filter(Business.id == provider_uuid).first()

    if not player or not provider:
        return {"success": False, "message": "Гравця чи страхового провайдера не знайдено"}

    premium_amount = money(premium)
    if money(player.balance) < premium_amount:
        return {"success": False, "message": "Недостатньо грошей для першого страхового внеску!"}

    # Оплата внеску
    debit(db, player, "balance", premium_amount)
    credit(db, provider, "cash_balance", premium_amount)

    policy = InsurancePolicy(
        player_id=player.id,
        business_id=business_uuid,
        provider_business_id=provider.id,
        coverage_amount=money(coverage),
        daily_premium=premium_amount,
        status="active"
    )
    db.add(policy)

    log_transaction(
        db, player.city_id,
        sender_id=player.id, sender_type="player",
        receiver_id=provider.id, receiver_type="business",
        amount=float(premium_amount), tax=0.0,
        purpose="insurance_premium_initial"
    )

    db.commit()
    return {"success": True, "message": f"Ви успішно застрахували активи на суму {coverage:.2f} ₴. Внесок: {premium:.2f} ₴ сплачено."}

def process_daily_loan_installments_and_collectors(db: Session, player_id: str) -> dict:
    """Списання щоденних платежів за кредитом. При несплаті запускаються ШІ-Колектори!"""
    player_uuid = to_uuid(player_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    loans = db.query(BankLoan).filter(
        BankLoan.player_id == player_uuid,
        BankLoan.status.in_(["active", "delinquent"]),
    ).all()

    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    city = db.query(City).filter(City.id == player.city_id).first()
    results = []

    for loan in loans:
        payment = money(loan.daily_payment)
        
        if money(player.balance) >= payment:
            # Успішна сплата кредиту
            debit(db, player, "balance", payment)
            loan.remaining_debt = max(money("0.00"), money(loan.remaining_debt) - payment)
            
            # Гроші повертаються в міський банк (Скарбницю)
            credit(db, city, "treasury_balance", payment)
            
            if money(loan.remaining_debt) == money("0.00"):
                loan.status = "paid"
                results.append(f"🎉 Кредит №{str(loan.id)[:8]} повністю виплачено!")
            else:
                loan.status = "active"
                results.append(f"✅ Сплачено внесок за кредит: -{payment:.2f} ₴. Борг: {loan.remaining_debt:.2f} ₴.")
                
            log_transaction(
                db, player.city_id,
                sender_id=player.id, sender_type="player",
                receiver_id=city.id, receiver_type="treasury",
                amount=float(payment), tax=0.0,
                purpose="loan_repayment"
            )
        else:
            # Несплата! Запуск ШІ-Колекторів (Debt Collectors)
            loan.status = "delinquent"
            
            # Колектори конфісковують 50% від усіх поточних грошей гравця на рахунку
            seizure = money(player.balance) * money("0.50")
            debit(db, player, "balance", seizure)
            loan.remaining_debt = max(money("0.00"), money(loan.remaining_debt) - seizure)
            
            # Кошти вилучаються в Скарбницю
            credit(db, city, "treasury_balance", seizure)
            
            results.append(
                f"🚨 ШІ-КОЛЕКТОРИ! Кредит прострочено. Заморожено рахунки гравця {player.username}. "
                f"Примусово конфісковано {seizure:.2f} ₴ в рахунок боргу. Борг: {loan.remaining_debt:.2f} ₴."
            )
            
            log_transaction(
                db, player.city_id,
                sender_id=player.id, sender_type="player",
                receiver_id=city.id, receiver_type="treasury",
                amount=seizure, tax=0.0,
                purpose="collector_debt_seizure"
            )

    db.commit()
    return {"success": True, "details": results}

def donate_to_lobby_fund(db: Session, cartel_name: str, city_id: str, industry: str, 
                           player_id: str, amount: float) -> dict:
    """Внесення коштів гравцем до Лобістського Фонду промислового Картелю"""
    player_uuid = to_uuid(player_id)
    city_uuid = to_uuid(city_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    donation = money(amount)
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}
    if money(player.balance) < donation:
        return {"success": False, "message": "Недостатньо грошей для внеску в лобі-фонд!"}

    cartel = db.query(Cartel).filter(Cartel.city_id == city_uuid, Cartel.industry_type == industry).first()
    if not cartel:
        cartel = Cartel(
            city_id=city_uuid,
            name=cartel_name,
            industry_type=industry,
            lobby_fund=money("0.00")
        )
        db.add(cartel)
        db.commit()
        db.refresh(cartel)

    # Переказ коштів у фонд картелю
    debit(db, player, "balance", donation)
    credit(db, cartel, "lobby_fund", donation)

    log_transaction(
        db, city_id,
        sender_id=player.id, sender_type="player",
        receiver_id=cartel.id, receiver_type="business",
        amount=float(donation), tax=0.0,
        purpose="lobby_fund_donation"
    )

    db.commit()
    
    # Лобіювання: якщо фонд перевищує 5000 ₴, картель автоматично подає петицію 
    # на зниження податків для цієї індустрії на 2% Мером міста
    action_triggered = False
    if money(cartel.lobby_fund) >= money("5000.00"):
        city = db.query(City).filter(City.id == city_uuid).first()
        city.tax_rate_property = max(money("0.50"), money(city.tax_rate_property) - money("2.00"))
        debit(db, cartel, "lobby_fund", money("5000.00"))
        action_triggered = True
        message = (
            f"📈 ЛОБІЗМ! Промисловий Картель '{cartel.name}' успішно протиснув законопроект! "
            f"Податок на майно цієї індустрії знижено на 2.0% (Новий податок: {city.tax_rate_property}%)."
        )
    else:
        message = f"Внесок у сумі {amount:.2f} ₴ успішно перераховано до фонду лобіювання Картелю '{cartel.name}'."

    db.commit()
    return {"success": True, "message": message, "lobby_action": action_triggered}
