from datetime import datetime
from typing import Annotated, Optional, List

from bson import ObjectId
from pydantic import BeforeValidator, BaseModel, Field, ConfigDict, field_validator


def validate_object_id(v):
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError('Invalid ObjectID')


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class RealEstateProperty(BaseModel):
    """Model cho thông tin bất động sản"""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Core fields theo yêu cầu
    title: Optional[str] = Field(None, description="Tên bất động sản")
    address: Optional[str] = Field(None, description="Địa chỉ")
    city: Optional[str] = Field(None, description="Thành phố")
    seller: Optional[str] = Field(None, description="Người bán")
    numberPhone: Optional[str] = Field(None, description="Số điện thoại")
    price: Optional[float] = Field(None, description="Giá (chuỗi gốc)")
    area: Optional[float] = Field(None, description="Diện tích (m²)")
    unit_price: Optional[float] = Field(None, description="Đơn giá (VND/m²)")
    link: str = Field(..., description="Link bài đăng - dùng để xử lý trùng lặp")
    datepost: Optional[str] = Field(None, description="Ngày đăng")
    bedroom: Optional[int] = Field(None, description="Số phòng ngủ")
    bathroom: Optional[int] = Field(None, description="Số phòng tắm")
    legal: Optional[str] = Field(None, description="Pháp lý")
    frontage: Optional[float] = Field(None, description="Mặt tiền")
    description: Optional[str] = Field(None, description="Mô tả dự án")

    # Fields extracted by LLM from description
    amenityLocation: Optional[str] = Field(None, description="Vị trí tiện ích (trích xuất từ LLM)")
    type: Optional[str] = Field(None,
                                description="Loại hình: căn hộ, nhà phố, đất nền, biệt thự, shophouse, kho xưởng (LLM)")

    # Metadata
    source: str = Field(..., description="Nguồn crawl")
    crawled_at: datetime = Field(default_factory=datetime.now, description="Thời điểm crawl")
    updated_at: datetime = Field(default_factory=datetime.now, description="Thời điểm cập nhật")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

    @field_validator('area', 'unit_price')
    @classmethod
    def validate_positive_numbers(cls, v):
        if v is not None and v < 0:
            raise ValueError('Giá trị phải lớn hơn 0')
        return v

    @field_validator('bedroom', 'bathroom')
    @classmethod
    def validate_positive_integers(cls, v):
        if v is not None and v < 0:
            raise ValueError('Số phòng phải lớn hơn hoặc bằng 0')
        return v

    @field_validator('link')
    @classmethod
    def validate_link(cls, v):
        if not v or not v.startswith('http'):
            raise ValueError('Link không hợp lệ')
        return v

    def calculate_unit_price(self):
        """Tính đơn giá từ giá và diện tích"""
        if isinstance(self.price, (int, float)) and self.area and self.area > 0:
            self.unit_price = self.price / self.area
        return self.unit_price