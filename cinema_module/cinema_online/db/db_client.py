from interfaces.db_interface import DBInterface, ElasticInterface

db: ElasticInterface


# Функция понадобится при внедрении зависимостей
async def get_db_client() -> DBInterface:
    return db  # noqa
