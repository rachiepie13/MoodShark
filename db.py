import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["moodshark"]
users_collection = db["users"]
movies_collection = db["movies"]

books_collection = db["books"]
tv_shows_collection = db["tv_shows"]
music_collection = db["music"]
podcasts_collection = db["podcasts"]
activities_collection = db["activities"]


if __name__ == "__main__":
    try:
        print(db.list_collection_names())
        print("Connected to MongoDB successfully!")
    except Exception as e:
        print("Connection failed:", e)