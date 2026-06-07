from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Базовий репозиторій з CRUD операціями."""

    def __init__(self, db: Session, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    def get_by_id(self, id_) -> ModelT | None:
        return self.db.query(self.model).filter(self.model.id == id_).first()

    def get_by_id_for_update(self, id_) -> ModelT | None:
        return (
            self.db.query(self.model)
            .filter(self.model.id == id_)
            .with_for_update()
            .first()
        )

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[ModelT]:
        query = self.db.query(self.model).offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def count(self) -> int:
        return self.db.query(self.model).count()
