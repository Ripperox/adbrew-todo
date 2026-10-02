import os

from pymongo import MongoClient

MONGO_URI = "mongodb://{}:{}".format(os.environ["MONGO_HOST"], os.environ["MONGO_PORT"])
DB_NAME = "test_db"

# MongoClient keeps its own connection pool and connects lazily, so one
# instance per process is the recommended usage.
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
