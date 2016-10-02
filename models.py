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

    def images(self):
        return (
            Image.select()
            .join(ImageCollection)
            .where(ImageCollection.collection == self)
        )

    def plain_dict(self):
        return {
            'user': self.user.username,
            'name': self.name,
            'images': [image.plain_dict() for image in self.images()],
        }

    def plain_dict_short(self):
        return {
            'user': self.user.username,
            'name': self.name,
        }

class Image(BaseModel):
    user = ForeignKeyField(User)
    s3_key = CharField(unique=True)
    s3_bucket = CharField()
    title = CharField(default='')
    description = TextField(default='')
    date_created = DateTimeField()

    def plain_dict(self):
        return {
            'user': self.user.username,
            's3_key': self.s3_key,
            's3_bucket': self.s3_bucket,
            'title': self.title,
            'description': self.description,
            'date_created': self.date_created.isoformat(),
        }

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
