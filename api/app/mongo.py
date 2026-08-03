from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings


mongo_client: MongoClient = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=3000)
mongo_db: Database = mongo_client[settings.mongo_database]
