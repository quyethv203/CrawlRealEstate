
from datetime import datetime
from typing import Optional, Annotated

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field


def validate_object_id(v):
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError('Invalid ObjectID')

PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]

class WebsiteState(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., description="Tên website")
    enabled: bool = Field(default=True, description="Trạng thái bật/tắt crawler")
    updated_at: datetime = Field(default_factory=datetime.now, description="Thời điểm cập nhật")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}