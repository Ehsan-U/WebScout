import pymongo


def get_mongo(settings):
    MONGO_URI = settings.get('MONGO_URI')
    MONGO_DATABASE = settings.get('MONGO_DATABASE')
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DATABASE]
    return (client, db)