async def create_index(connection, collection_property, fields_names, unique=False):
    index_name = f'{"_".join(fields_names)}_index'
    collection = connection[collection_property.db_name][collection_property.name]
    indexes = await collection.index_information()
    if index_name not in indexes.keys():
        collection.create_index(fields_names, name=index_name, unique=unique)


async def create_indexes(connection, collections):
    for collection_property in collections:
        for index in collection_property.indexes:
            await create_index(connection, collection_property, index.fields, index.unique)
