from peewee import (
    SqliteDatabase, Model, ForeignKeyField, CharField, TextField,
    DateTimeField, IntegrityError
    )

database = SqliteDatabase('/data/data.db')

class BaseModel(Model):
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

class Image(BaseModel):
    user = ForeignKeyField(User)
    s3_key = CharField(unique=True)
    s3_bucket = CharField()
    title = CharField(default='')
    description = TextField(default='')
    date_created = DateTimeField()

class ImageCollection(BaseModel):
    image = ForeignKeyField(Image)
    collection = ForeignKeyField(Collection)
