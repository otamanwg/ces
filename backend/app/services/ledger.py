from sqlalchemy.orm import Session

from backend.app.models import TransactionModelLog
from backend.app.services.money import money


def log_transaction(
    db: Session,
    city_id: str,
    sender_id: str,
    sender_type: str,
    receiver_id: str,
    receiver_type: str,
    amount: float,
    tax: float,
    purpose: str,
) -> None:
    db.add(
        TransactionModelLog(
            city_id=city_id,
            sender_id=sender_id,
            sender_type=sender_type,
            receiver_id=receiver_id,
            receiver_type=receiver_type,
            amount=money(amount),
            tax_deducted=money(tax),
            purpose=purpose,
        )
    )


def debit(db: Session, balance_holder, field: str, amount) -> None:
    current = money(getattr(balance_holder, field))
    setattr(balance_holder, field, current - money(amount))


def credit(db: Session, balance_holder, field: str, amount) -> None:
    current = money(getattr(balance_holder, field))
    setattr(balance_holder, field, current + money(amount))
