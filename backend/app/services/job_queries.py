import uuid

from sqlalchemy.orm import Session

from backend.app.models import Job


def education_rank(value: str) -> int:
    return {"High School": 1, "College": 2, "University": 3}.get(value, 1)


def get_job(db: Session, job_id: uuid.UUID) -> Job | None:
    return db.query(Job).filter(Job.id == job_id).first()


def get_vacant_jobs(db: Session) -> list[Job]:
    return db.query(Job).filter(Job.filled_by_player_id.is_(None)).all()


def get_active_job(db: Session, player_id: uuid.UUID) -> Job | None:
    return db.query(Job).filter(Job.filled_by_player_id == player_id).first()


def get_first_vacant_job_by_min_education(db: Session, min_education: str) -> Job | None:
    return (
        db.query(Job)
        .filter(Job.min_education == min_education, Job.filled_by_player_id.is_(None))
        .first()
    )


def has_eligible_vacancy(db: Session, education_level: str) -> bool:
    player_rank = education_rank(education_level)
    return any(education_rank(job.min_education) <= player_rank for job in get_vacant_jobs(db))
