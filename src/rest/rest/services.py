from datetime import datetime
from typing import Dict, List

from .repositories import TodoRepository

MAX_DESCRIPTION_LENGTH = 500


class ValidationError(Exception):
    pass


class TodoService:
    """Business rules for todos, independent of HTTP and of the database."""

    def __init__(self, repository: TodoRepository):
        self._repository = repository

    def list_todos(self) -> List[Dict]:
        return self._repository.list_all()

    def create_todo(self, description) -> Dict:
        description = self._clean_description(description)
        return self._repository.create(description, created_at=datetime.utcnow())

    @staticmethod
    def _clean_description(description) -> str:
        if description is None:
            raise ValidationError("description is required")
        if not isinstance(description, str):
            raise ValidationError("description must be a string")
        description = description.strip()
        if not description:
            raise ValidationError("description is required")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ValidationError(
                "description must be at most {} characters".format(MAX_DESCRIPTION_LENGTH)
            )
        return description
