from peewee import (
    PostgresqlDatabase, Model, ForeignKeyField, CharField, TextField,
    DateTimeField, IntegrityError
    )

database = PostgresqlDatabase(
    os.environ.get('POSTGRES_DB', 'imghost'),
    user = os.environ.get('POSTGRES_USER', 'postgres'),
    password = os.environ.get('POSTGRES_PASSWORD', ''),
    host = os.environ.get('POSTGRES_HOST', 'postgres'),
    port = os.environ.get('POSTGRES_PORT', 5432),
)

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
    thumbs = CharField(default='')
    date_created = DateTimeField()

    class Meta:
        order_by = ('-date_created',)

class ImageCollection(BaseModel):
    image = ForeignKeyField(Image)
    collection = ForeignKeyField(Collection, index=True)

    class Meta:
        indexes = (
            (('image', 'collection'), True),
        )

class ApiKey(BaseModel):
    key = CharField(unique=True)
    user = ForeignKeyField(User)
    description = CharField(default='')
    date_created = DateTimeField()
