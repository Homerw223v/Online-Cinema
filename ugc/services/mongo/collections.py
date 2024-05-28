from pydantic import BaseModel


class Index(BaseModel):
    fields: list[str]
    unique: bool = False


class Collection(BaseModel):
    db_name: str
    name: str
    indexes: list[Index]


film_collection = Collection(
    db_name="review_db",
    name="films",
    indexes=[
        Index(fields=["film_id"]),
        Index(fields=["reviews._id"]),
        Index(fields=["reviews.user_id"]),
        Index(fields=["grades._id"]),
        Index(fields=["grades.user_id"]),
        Index(fields=["reviews.grades._id"]),
        Index(fields=["reviews.grades.user_id"]),
    ],
)

timestamp_collection = Collection(
    db_name="review_db",
    name="timestamps",
    indexes=[Index(fields=["user_id", "film_id"], unique=True)],
)
