from typing import Optional, List
from datetime import datetime
from src.data.database.connection import db
from src.data.models.WebsiteStatesModel import WebsiteState


class WebsiteStateRepository:
    COLLECTION = "website_states"

    @staticmethod
    def get_all():
        collection = db.get_collection("website_states")
        docs = collection.find({})
        result = []
        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            result.append(WebsiteState(**doc))
        return result

    @staticmethod
    def get_by_name(name: str):
        collection = db.get_collection("website_states")
        doc = collection.find_one({"name": name})
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return WebsiteState(**doc) if doc else None

    @staticmethod
    def set_state(name: str, enabled: bool):
        collection = db.get_collection(WebsiteStateRepository.COLLECTION)
        collection.update_one(
            {"name": name},
            {"$set": {"enabled": enabled, "updated_at": datetime.now()}},
            upsert=True
        )

    @staticmethod
    def get_enabled_websites() -> list:
        """
        Lấy danh sách tên các website đang enabled từ MongoDB
        """
        all_states = WebsiteStateRepository.get_all()
        return [ws.name for ws in all_states if ws.enabled]

    @staticmethod
    def init_states(websites: dict):
        collection = db.get_collection("website_states")
        for name, info in websites.items():
            # Chỉ insert nếu chưa có document với name này
            if not collection.find_one({"name": name}):
                collection.insert_one({
                    "name": name,
                    "enabled": info.get("enabled", True),
                    "updated_at": datetime.now()
                })