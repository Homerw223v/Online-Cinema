from db.review_db_client import get_db_client
from services.exceptions import FilmTimestampNotFoundException
from services.mongo.collections import timestamp_collection
from services.mongo.mongo_repository import BaseService


class FilmTimestampService(BaseService):
    _collection_name = timestamp_collection.name
    _not_found_exception = FilmTimestampNotFoundException


async def get_film_timestamp_service():
    yield FilmTimestampService(await get_db_client())
