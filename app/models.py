from email.policy import default
from typing import Optional, List, Any
from pydantic import BaseModel, Field, Json
from bson import ObjectId
import datetime


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class EventModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    tracking_key: str = Field(...)
    type: str = Field(...)    
    timestamp: Optional[datetime.datetime]
    created_by: int = Field(...)
    meta: Json[Any]
    visible: Optional[bool] = Field(default = False)
    reason: Optional[str] = Field(default = "Event submitted.")
    status: Optional[str] = Field(default = None)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "tracking_key": "AM037392733LO",
                "type": "PACKAGE_CREATED",
                "created_by": 12345,
                "meta": "{ \"unit_load\": 12345 }",
            }
        }


class TrackingModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    tracking_key: str = Field(...)
    events: list[Json[Any]]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "tracking_key": "AM037392733LO",
                "type": "PACKAGE_CREATED",
                "created_by": 12345,
                "meta": "{ \"unit_load\": 12345 }"
            }
        }        