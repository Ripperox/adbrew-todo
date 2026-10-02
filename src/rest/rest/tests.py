from datetime import datetime
from unittest import TestCase, mock

from pymongo.errors import ServerSelectionTimeoutError
from rest_framework.test import APIRequestFactory

from .services import MAX_DESCRIPTION_LENGTH, TodoService, ValidationError
from .views import TodoListView


class FakeTodoRepository:
    def __init__(self):
        self.todos = []

    def create(self, description, created_at):
        todo = {"id": str(len(self.todos) + 1), "description": description,
                "created_at": created_at.isoformat(timespec="milliseconds") + "Z"}
        self.todos.append(todo)
        return todo

    def list_all(self):
        return list(reversed(self.todos))


class TodoServiceTests(TestCase):
    def setUp(self):
        self.repository = FakeTodoRepository()
        self.service = TodoService(self.repository)

    def test_create_strips_whitespace(self):
        todo = self.service.create_todo("  buy milk  ")
        self.assertEqual(todo["description"], "buy milk")

    def test_create_rejects_invalid_descriptions(self):
        for bad in [None, 42, "", "   ", "x" * (MAX_DESCRIPTION_LENGTH + 1)]:
            with self.subTest(description=bad):
                with self.assertRaises(ValidationError):
                    self.service.create_todo(bad)
        self.assertEqual(self.repository.todos, [])

    def test_list_returns_newest_first(self):
        self.service.create_todo("first")
        self.service.create_todo("second")
        descriptions = [t["description"] for t in self.service.list_todos()]
        self.assertEqual(descriptions, ["second", "first"])


class TodoListViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = TodoListView.as_view()
        patcher = mock.patch.object(TodoListView, "service", TodoService(FakeTodoRepository()))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_post_then_get(self):
        response = self.view(self.factory.post("/todos/", {"description": "buy milk"}, format="json"))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["description"], "buy milk")

        response = self.view(self.factory.get("/todos/"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([t["description"] for t in response.data], ["buy milk"])

    def test_post_blank_description_returns_400(self):
        response = self.view(self.factory.post("/todos/", {"description": " "}, format="json"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

    def test_post_non_object_body_returns_400(self):
        response = self.view(self.factory.post("/todos/", ["buy milk"], format="json"))
        self.assertEqual(response.status_code, 400)

    def test_database_error_returns_503(self):
        with mock.patch.object(TodoListView.service, "list_todos",
                               side_effect=ServerSelectionTimeoutError("down")):
            response = self.view(self.factory.get("/todos/"))
        self.assertEqual(response.status_code, 503)
