from playhouse.shortcuts import model_to_dict

import sqlite_models
import models

sqlite_models.database.connect()
models.database.connect()

old_users = sqlite_models.User.select()

for old_user in old_users:
    new_user = models.User.create(**model_to_dict(old_user, recurse=False))

    old_apikeys = sqlite_models.ApiKey.select().where(sqlite_models.ApiKey.user == old_user)
    for old_apikey in old_apikeys:
        models.ApiKey.create(**model_to_dict(old_apikey, recurse=False))

    old_images = sqlite_models.Image.select().where(sqlite_models.Image.user == old_user)
    for old_image in old_images:
        try:
            models.Image.create(**model_to_dict(old_image, recurse=False))
        except:
            print(model_to_dict(old_image, recurse=False))

    old_collections = sqlite_models.Collection.select().where(sqlite_models.Collection.user == old_user)
    for old_collection in old_collections:
        models.Collection.create(**model_to_dict(old_collection, recurse=False))
        old_imagecollections = sqlite_models.ImageCollection.select().where(sqlite_models.ImageCollection.collection == old_collection)
        for old_imagecollecton in old_imagecollections:
            models.ImageCollection.create(**model_to_dict(old_imagecollecton, recurse=False))

tables = [
    'user',
    'apikey',
    'image',
    'collection',
    'imagecollection',
]

for table in tables:
    models.database.execute_sql('SELECT setval(pg_get_serial_sequence(\'{table}\', \'id\'), coalesce(max(id),0) + 1, false) FROM "{table}";'.format(table=table))

sqlite_models.database.close()
models.database.close()
