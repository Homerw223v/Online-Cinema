from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.general import ObjectId


class PaginatedParams(BaseModel):
    page_size: int = Field(ge=1, default=20)
    page_number: int = Field(ge=1, default=1)

    @property
    def offset(self):
        return self.page_size * (self.page_number - 1)


class HttpException(BaseModel):
    detail: str


class ObjectIdModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: ObjectId = Field(validation_alias="_id")


class AggregateLikes(BaseModel):
    likes: int
    dislikes: int


class AggregateGrade(BaseModel):
    avg_grade: float | None


class Grade(BaseModel):
    grade: int


class ExtendedGrade(Grade):
    user_id: UUID
    film_id: UUID


class RetrieveGrade(ObjectIdModel, ExtendedGrade):
    pass  # noqa


class ExtendedReviewGrade(Grade):
    user_id: UUID
    review_id: ObjectId
    film_id: UUID


class RetrieveReviewGrade(ObjectIdModel, ExtendedReviewGrade):
    pass  # noqa


class Review(BaseModel):
    text: str


class ExtendedReview(Review):
    film_id: UUID
    user_id: UUID
    created: datetime = Field(default_factory=datetime.now)


class RetrieveReview(ObjectIdModel, ExtendedReview):
    pass  # noqa


class ExtendedRetrieveReview(RetrieveReview):
    film_grade: int = None
    review_grade: AggregateLikes = None


class FilmTimestamp(BaseModel):
    timestamp: int


class ExtendedFilmTimestamp(FilmTimestamp):
    user_id: UUID
    film_id: UUID


class RetrieveFilmTimestamp(ObjectIdModel, ExtendedFilmTimestamp):
    pass  # noqa
