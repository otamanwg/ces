import uuid

from sqlalchemy.orm import Session

from backend.app.models import Job
from backend.app.repositories.job import JobRepository


def education_rank(value: str) -> int:
    return {"High School": 1, "College": 2, "University": 3}.get(value, 1)


def get_job(db: Session, job_id: uuid.UUID) -> Job | None:
    return JobRepository(db).get_by_id(job_id)


def get_vacant_jobs(db: Session) -> list[Job]:
    return JobRepository(db).get_vacant()


def get_active_job(db: Session, player_id: uuid.UUID) -> Job | None:
    return JobRepository(db).get_active_for_player(player_id)


def get_first_vacant_job_by_min_education(
    db: Session, min_education: str
) -> Job | None:
    return JobRepository(db).get_first_vacant_by_min_education(min_education)


def has_eligible_vacancy(db: Session, education_level: str) -> bool:
    player_rank = education_rank(education_level)
    return any(
        education_rank(job.min_education) <= player_rank for job in get_vacant_jobs(db)
    )
