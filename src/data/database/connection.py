from typing import Optional, Dict, Any

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError
from pymongo.synchronous.database import Database


class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init = False
        return cls._instance

    def __init__(self):
        if self._init:
            return

        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.connected = False
        self._init = True

    def connect(self, uri) -> bool:
        if self.connected:
            return True

        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            self.db = self.client.real_estate_db
            self.connected = True

            self._setup_indexes()
            return True

        except ServerSelectionTimeoutError:
            return False
        except Exception as e:
            return False

    def _setup_indexes(self):
        if not self.connected:
            return
        try:
            collection = self.db.properties
            collection.create_index('link', unique=True)
            collection.create_index('thanh_pho')
            collection.create_index('gia')
            collection.create_index('dien_tich')
            collection.create_index('loai_hinh')
        except Exception as e:
            print(e)

    def save(self, data: Dict[str, Any]):
        if not self.connected:
            return False
        try:
            result = self.db.properties.insert_one(data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            return 'duplicate'
        except Exception as e:
            return False

    def count(self, query: Dict = None) -> int:
        """Đếm properties"""
        if not self.connected:
            return 0
        try:
            return self.db.properties.count_documents(query or {})
        except Exception as e:
            return 0

    def stats(self) -> Dict[str, int]:
        """Thống kê theo source"""
        if not self.connected:
            return {}
        try:
            pipeline = [{"$group": {"_id": "$source", "count": {"$sum": 1}}}]
            results = self.db.properties.aggregate(pipeline)
            return {r["_id"]: r["count"] for r in results}
        except Exception as e:
            return {}

    def close(self):
        """Đóng kết nối"""
        if self.client:
            self.client.close()
            self.connected = False

    def get_collection(self, name: str):
        """Get collection"""
        if not self.connected:
            return None
        return getattr(self.db, name, self.db[name])

    def get_crawl_stats(self, query=None):
        """Get crawl statistics"""
        if not self.connected:
            return {} if query else []
        collection = self.get_collection("crawl_stats")
        if query:
            result = collection.find_one({'session_id': query})
            return result or {}
        return list(collection.find({}))

    def save_document(self, collection_name: str, document: dict):
        """Save document to collection"""
        if not self.connected:
            return None
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document)
        return result.inserted_id

    def find_one(self, collection_name: str, query: dict = None):
        """Find one document"""
        if not self.connected:
            return None
        collection = self.get_collection(collection_name)
        return collection.find_one(query or {})


# Global instance
database = DatabaseManager()

# Aliases for compatibility
db = database
