from datetime import datetime
from typing import Dict, List

from pymongo import DESCENDING
from pymongo.collection import Collection


class TodoRepository:
    """Persistence for todos. The only place that knows todos live in Mongo."""

    def __init__(self, collection: Collection):
        self._collection = collection

    def create(self, description: str, created_at: datetime) -> Dict:
        doc = {"description": description, "created_at": created_at}
        result = self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._to_dict(doc)

    def list_all(self) -> List[Dict]:
        cursor = self._collection.find().sort("created_at", DESCENDING)
        return [self._to_dict(doc) for doc in cursor]

    @staticmethod
    def _to_dict(doc: Dict) -> Dict:
        # ObjectId and datetime are not JSON-serialisable; expose plain types
        # and an `id` field so API clients don't depend on Mongo's `_id`.
        # Mongo stores datetimes at millisecond precision, so format at that
        # precision to keep POST and GET responses identical.
        return {
            "id": str(doc["_id"]),
            "description": doc["description"],
            "created_at": doc["created_at"].isoformat(timespec="milliseconds") + "Z",
        }
