from peewee import (
    SqliteDatabase, Model, ForeignKeyField, CharField, TextField,
    DateTimeField, IntegrityError
    )

from playhouse.sqlite_ext import PrimaryKeyAutoIncrementField

database = SqliteDatabase('/data/data.db')

class BaseModel(Model):
    id = PrimaryKeyAutoIncrementField()
    class Meta():
        database = database

class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(unique=True)
    date_created = DateTimeField()

class Collection(BaseModel):
    user = ForeignKeyField(User)
    name = CharField(unique=True)

    def images(self):
        return (
            Image.select()
            .join(ImageCollection)
            .where(ImageCollection.collection == self)
        )

class Image(BaseModel):
    user = ForeignKeyField(User)
    s3_key = CharField(unique=True)
    s3_bucket = CharField()
    title = CharField(default='')
    description = TextField(default='')
    colors = CharField(default='')
    size = CharField(default='')
    date_created = DateTimeField()

    class Meta:
        order_by = ('-date_created',)

class ImageCollection(BaseModel):
    image = ForeignKeyField(Image)
    collection = ForeignKeyField(Collection)

    class Meta:
        indexes = (
            (('image', 'collection'), True),
        )

class ApiKey(BaseModel):
    key = CharField(unique=True)
    user = ForeignKeyField(User)
    description = CharField(default='')
    date_created = DateTimeField()
