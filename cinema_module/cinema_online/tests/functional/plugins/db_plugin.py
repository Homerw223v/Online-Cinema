import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from functional.config import settings
from functional.testdata.elastic_indexes import index_genre, index_movie, index_person
from functional.testdata.films_data import films_data
from functional.testdata.genres_data import genres_data
from functional.testdata.person_data import person_data
from functional.utils.interfaces.db_interface import ElasticInterface


@pytest_asyncio.fixture(scope="session")
async def db_client():
    async with AsyncElasticsearch(hosts=[str(settings.elastic.base_url)], verify_certs=False) as client:
        db_interface = ElasticInterface(client)
        yield db_interface


@pytest_asyncio.fixture(scope="session")
async def db_write_films_data(db_client):
    await db_client.create_or_replace_table(index_movie["index"], index_movie)
    await db_client.write_data(index_movie["index"], films_data)


@pytest_asyncio.fixture(scope="session")
async def db_write_person_data(db_client):
    await db_client.create_or_replace_table(index_person["index"], index_person)
    await db_client.write_data(index_person["index"], person_data)


@pytest_asyncio.fixture(scope="session")
async def db_write_genre_data(db_client):
    await db_client.create_or_replace_table(index_genre["index"], index_genre)
    await db_client.write_data(index_genre["index"], genres_data)
