import os

from pymongo import MongoClient
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()

# Get MongoDB connection string
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in .env")


# Connect to MongoDB Atlas
client = MongoClient(MONGODB_URI)


# Select database and collection
db = client["ai_doc"]
collection = db["court_cases"]


def test_connection():
    """Test connection to MongoDB Atlas."""
    
    client.admin.command("ping")
    
    print("MongoDB Atlas connection successful!")
    print("Database: ai_doc")
    print("Collection: court_cases")


if __name__ == "__main__":
    test_connection()