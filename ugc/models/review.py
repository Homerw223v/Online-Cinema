from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.general import ObjectId


class ObjectIdModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: ObjectId = Field(validation_alias="_id")


class Like(BaseModel):
    film_id: UUID
    user_id: UUID
    grade: int


class ReviewLike(BaseModel):
    review_id: ObjectId
    user_id: UUID
    grade: int


class AggregateGrade(BaseModel):
    dislikes: int
    avg_grade: float


class Review(BaseModel):
    id: ObjectId
    text: str
    created: datetime
    user_id: UUID
    film_grade: int
    review_grade: AggregateGrade
