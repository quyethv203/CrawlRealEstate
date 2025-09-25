import logging
from typing import Dict, Any, List

from ..database.connection import db
from ..models.CrawlStatsModel import CrawlStats
from ..models.RealEstateModel import RealEstateProperty
from ...config.settings import Config


class RealEstateRepository:
    """Repository cho crawler - chỉ save và stats"""

    def __init__(self):
        # Ensure database connection
        if not db.connected:
            config = Config()
            success = db.connect(config.MONGODB_URI)
            if not success:
                print(f"❌ Failed to connect to MongoDB: {config.MONGODB_URI}")
            else:
                print(f"✅ Connected to MongoDB: {config.MONGODB_DATABASE}")

    def save_property(self, property_data: RealEstateProperty) -> str:
        try:
            data_dict = property_data.model_dump(by_alias=True)
            existing = db.db.properties.find_one({"link": property_data.link})
            if existing:
                data_dict.pop('_id', None)
                db.db.properties.update_one(
                    {"link": property_data.link},
                    {"$set": data_dict}
                )
                logging.info(f"Updated property: {property_data.link}")
                return str(existing["_id"])
            else:
                result = db.db.properties.insert_one(data_dict)
                logging.info(f"Inserted property: {property_data.link}")
                return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error saving property: {e}")
            return ""

    def save_crawl_stats(self, stats: CrawlStats) -> str:
        """Lưu thống kê crawl session"""
        try:
            data_dict = stats.model_dump(by_alias=True)
            result = db.db.crawl_stats.insert_one(data_dict)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error saving crawl stats: {e}")
            return ""

    def count_total(self) -> int:
        """Đếm tổng số properties đã crawl"""
        try:
            return db.db.properties.count_documents({})
        except:
            return 0

    def count_by_source(self, source: str) -> int:
        """Đếm số properties từ 1 source"""
        try:
            return db.db.properties.count_documents({"source": source})
        except:
            return 0

    def get_stats(self) -> Dict[str, int]:
        """Thống kê số lượng theo từng source"""
        try:
            pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}}
            ]
            result = db.db.properties.aggregate(pipeline)
            return {item["_id"]: item["count"] for item in result}
        except:
            return {}

    def get_recent_crawl_stats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy stats của các phiên crawl gần nhất"""
        try:
            cursor = db.db.crawl_stats.find().sort("start_time", -1).limit(limit)
            return list(cursor)
        except:
            return []

    def exists_by_link(self, link: str) -> bool:
        return db.db.properties.find_one({"link": link}) is not None


# Global instances cho crawler sử dụng
real_estate_repo = RealEstateRepository()
