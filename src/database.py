import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


# Load .env that lives next to this file (src/.env)
load_dotenv(Path(__file__).resolve().parent / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")

DB_NAME = "ai_doc"
COLLECTION_NAME = "court_cases"

_client = None


def get_collection():
    """Return the collection handle, connecting lazily on first use."""

    global _client

    if not MONGODB_URI:
        raise RuntimeError("MONGODB_URI not set in src/.env")

    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

    return _client[DB_NAME][COLLECTION_NAME]


def save_case(record: dict) -> str:
    """Insert or replace a case record keyed by filename."""

    collection = get_collection()

    result = collection.replace_one(
        {"filename": record["filename"]},
        record,
        upsert=True
    )

    return str(result.upserted_id)


def list_cases(limit: int = 100) -> list:
    """Return the most recently saved cases."""

    cursor = (
        get_collection()
        .find()
        .sort("extracted_at", -1)
        .limit(limit)
    )

    cases = []

    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        cases.append(doc)

    return cases


def test_connection():
    """Test connection to MongoDB Atlas."""

    get_collection().database.client.admin.command("ping")

    print("MongoDB Atlas connection successful!")
    print(f"Database: {DB_NAME}")
    print(f"Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    test_connection()
