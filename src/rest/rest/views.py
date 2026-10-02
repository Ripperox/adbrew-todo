import logging

from pymongo.errors import PyMongoError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .db import db
from .repositories import TodoRepository
from .services import TodoService, ValidationError

logger = logging.getLogger(__name__)


class TodoListView(APIView):
    service = TodoService(TodoRepository(db["todos"]))

    def get(self, request):
        try:
            todos = self.service.list_todos()
        except PyMongoError:
            logger.exception("Failed to fetch todos")
            return self._db_unavailable()
        return Response(todos, status=status.HTTP_200_OK)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response({"detail": "request body must be a JSON object"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            todo = self.service.create_todo(request.data.get("description"))
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except PyMongoError:
            logger.exception("Failed to create todo")
            return self._db_unavailable()
        return Response(todo, status=status.HTTP_201_CREATED)

    @staticmethod
    def _db_unavailable():
        return Response({"detail": "database unavailable, please try again"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
