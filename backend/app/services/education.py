# Логіка освіти, іспитів у коледжі та тіньового ринку дипломів
# Файл: backend/app/services/education.py

import json
import os
from decimal import Decimal
from typing import Dict, List

from sqlalchemy.orm import Session

from backend.app.models import Player, PoliceRecord, City
from backend.app.schemas.service_results import (
    ExamSubmissionServiceResult,
    FakeDiplomaPurchaseServiceResult,
    PoliceAuditBustedServiceResult,
    PoliceAuditClearServiceResult,
)
from backend.app.services.ids import to_uuid
from backend.app.services.ledger import credit, debit, log_transaction
from backend.app.services.money import money

COLLEGE_EXAM_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "database", "college_exams_manager.json")
)


def load_manager_exam() -> dict:
    """Завантаження квізу фінансової грамотності з JSON файлу"""
    if not os.path.exists(COLLEGE_EXAM_FILE):
        return {}
    with open(COLLEGE_EXAM_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def process_exam_submission(db: Session, player_id: str, submitted_answers: Dict[str, int]) -> dict:
    """Оцінювання відповідей гравця та надання диплома"""
    player_uuid = to_uuid(player_id)
    player = db.query(Player).filter(Player.id == player_uuid).with_for_update().first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}
    if player.education_level != "High School":
        return {"success": False, "message": "Іспит доступний лише для переходу з High School до College."}

    exam = load_manager_exam()
    if not exam:
        return {"success": False, "message": "Файл іспиту не знайдено"}

    # Перевірка наявності грошей на іспит
    cost = money(exam["cost_to_take"])
    if money(player.balance) < cost:
        return {"success": False, "message": f"Недостатньо грошей для складання іспиту! Потрібно: {cost} ₴"}

    # Списання оплати в Скарбницю
    debit(db, player, "balance", cost)
    city = db.query(City).filter(City.id == player.city_id).first()
    credit(db, city, "treasury_balance", cost)
    log_transaction(
        db,
        city.id,
        sender_id=player.id,
        sender_type="player",
        receiver_id=city.id,
        receiver_type="treasury",
        amount=float(cost),
        tax=0.0,
        purpose="exam_fee",
    )

    # Оцінювання відповідей
    correct_count = 0
    total_questions = len(exam["questions"])
    details = []

    for q in exam["questions"]:
        q_id = str(q["id"])
        correct_idx = q["correct_option_index"]
        user_answer = submitted_answers.get(q_id)

        is_correct = user_answer == correct_idx
        if is_correct:
            correct_count += 1

        details.append({"question_id": q["id"], "correct": is_correct, "explanation": q["explanation"]})

    passed = correct_count >= int(exam["passing_score"])

    if passed:
        # Успішне складання — підвищення кваліфікації
        player.education_level = "College"
        player.diploma_verified = True  # Чесний диплом
        message = f"Вітаємо! Ви успішно склали іспит ({correct_count}/{total_questions}) та отримали диплом Коледжу!"
    else:
        message = f"Ви провалили іспит ({correct_count}/{total_questions}). Спробуйте ще раз після підготовки."

    db.commit()

    return ExamSubmissionServiceResult(
        success=True,
        passed=passed,
        score=f"{correct_count}/{total_questions}",
        message=message,
        details=details,
        player={"balance": float(player.balance), "education_level": player.education_level},
    ).model_dump()


def purchase_fake_diploma(db: Session, player_id: str) -> dict:
    """Тіньова купівля підробленого диплома Коледжу (Швидко, але небезпечно)"""
    player_uuid = to_uuid(player_id)
    player = db.query(Player).filter(Player.id == player_uuid).with_for_update().first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    if player.education_level == "College" or player.education_level == "University":
        return {"success": False, "message": "У вас вже є вища освіта!"}

    black_market_cost = money("350.00")  # Дорожче, ніж чесний іспит
    if money(player.balance) < black_market_cost:
        return {
            "success": False,
            "message": f"Кримінальний дилер вимагає {black_market_cost} ₴. У вас немає такої суми.",
        }

    city = db.query(City).filter(City.id == player.city_id).first()

    # Списання грошей у тіньовий сектор: це money sink, але він має бути видимим в аудиті.
    debit(db, player, "balance", black_market_cost)
    log_transaction(
        db,
        city.id,
        sender_id=player.id,
        sender_type="player",
        receiver_id=city.id,
        receiver_type="system",
        amount=float(black_market_cost),
        tax=0.0,
        purpose="fake_diploma_purchase",
    )
    player.education_level = "College"
    player.diploma_verified = False  # Підробка!

    # Створення поліцейського запису про можливе правопорушення
    record = PoliceRecord(
        player_id=player.id,
        offense_type="Fake College Diploma Purchased",
        fine_amount=money("500.00"),  # Штраф буде 500 грн, якщо зловлять
        status="under_investigation",
    )
    db.add(record)
    db.commit()

    return FakeDiplomaPurchaseServiceResult(
        success=True,
        message="Ви придбали підроблений диплом під прилавком! Тепер ви можете влаштуватись на кращу роботу. Але стережіться перевірок Поліції...",
        player={
            "balance": float(player.balance),
            "education_level": player.education_level,
            "diploma_verified": player.diploma_verified,
        },
    ).model_dump()


def run_police_audit(db: Session, player_id: str) -> dict:
    """ШІ-Поліція проводить випадковий аудит резюме гравця (наприклад, при спробі підвищення)"""
    player_uuid = to_uuid(player_id)
    player = db.query(Player).filter(Player.id == player_uuid).first()
    if not player:
        return {"success": False, "message": "Гравця не знайдено"}

    # Перевіряємо, чи є запис про підробку
    record = (
        db.query(PoliceRecord)
        .filter(PoliceRecord.player_id == player_uuid, PoliceRecord.status == "under_investigation")
        .first()
    )

    if not player.diploma_verified and record:
        # Зловили! Штрафуємо та анулюємо диплом
        fine = money(record.fine_amount)
        collected_fine = min(money(player.balance), fine)
        debit(db, player, "balance", collected_fine)
        player.education_level = "High School"  # Ануляція освіти
        player.diploma_verified = True

        # Гроші від штрафу йдуть у Скарбницю міста
        city = db.query(City).filter(City.id == player.city_id).first()
        credit(db, city, "treasury_balance", collected_fine)
        if collected_fine > money("0.00"):
            log_transaction(
                db,
                city.id,
                sender_id=player.id,
                sender_type="player",
                receiver_id=city.id,
                receiver_type="treasury",
                amount=float(collected_fine),
                tax=0.0,
                purpose="fake_diploma_fine",
            )

        record.status = "fined"
        db.commit()

        return PoliceAuditBustedServiceResult(
            busted=True,
            message=f"🚨 ПОЛІЦІЯ! Ваше резюме пройшло аудит. Виявлено підроблений диплом! Стягнуто штраф {collected_fine:.2f} ₴, а диплом анульовано.",
            player={"balance": float(player.balance), "education_level": player.education_level},
        ).model_dump()

    return PoliceAuditClearServiceResult(
        busted=False,
        message="Ваші документи пройшли перевірку успішно.",
    ).model_dump()
