from datetime import datetime
from typing import Annotated, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field, ConfigDict


def validate_object_id(v):
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError('Invalid ObjectID')

PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class CrawlStats(BaseModel):
    """Model thống kê quá trình crawl"""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    source: str = Field(..., description="Nguồn crawl")
    start_time: datetime = Field(..., description="Thời gian bắt đầu")
    end_time: Optional[datetime] = Field(None, description="Thời gian kết thúc")
    total_pages: int = Field(default=0, description="Tổng số trang")
    total_items: int = Field(default=0, description="Tổng số items crawl")
    successful_items: int = Field(default=0, description="Số items thành công")
    failed_items: int = Field(default=0, description="Số items thất bại")
    duplicate_items: int = Field(default=0, description="Số items trùng lặp")
    status: str = Field(default="running", description="Trạng thái: running, completed, failed")
    error_message: Optional[str] = Field(None, description="Thông báo lỗi")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )