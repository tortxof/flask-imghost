import base64
import datetime
import hashlib
import json
import os
import string
import tempfile
from urllib.parse import quote_plus

import boto3
from colorthief import ColorThief
from flask import Flask, g, redirect, render_template, request, session, url_for
from flask_httpauth import HTTPBasicAuth
from flask_restful import Api, Resource, abort, fields, marshal_with
from PIL import Image as PImage
from playhouse.shortcuts import model_to_dict
from werkzeug.security import check_password_hash, generate_password_hash
from whitenoise import WhiteNoise

import models


def migrate():
    models.database.connect()
    models.database.create_tables(
        [
            models.User,
            models.Collection,
            models.Image,
            models.ImageCollection,
            models.ApiKey,
        ],
        safe=True,
    )
    models.database.close()


app = Flask(__name__)
app.wsgi_app = WhiteNoise(app.wsgi_app, root="static/")
api = Api(app)
auth = HTTPBasicAuth()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["DEBUG"] = json.loads(os.getenv("FLASK_DEBUG", "false"))
app.config["S3_BUCKET"] = os.getenv("S3_BUCKET")
app.config["BUCKET_CDN"] = json.loads(os.getenv("BUCKET_CDN"))


@auth.verify_password
def verify_password(username, password):
    if "username" in session:
        try:
            user = models.User.get(models.User.username == session.get("username"))
        except models.User.DoesNotExist:
            session.pop("username", None)
            return False
        g.user = user
        return True
    try:
        api_key = models.ApiKey.get(models.ApiKey.key == password)
    except models.ApiKey.DoesNotExist:
        pass
    else:
        if api_key:
            g.user = api_key.user
            session["username"] = g.user.username
            return True
    try:
        user = models.User.get(models.User.username == username)
    except models.User.DoesNotExist:
        return False
    if check_password_hash(user.password, password):
        g.user = user
        session["username"] = g.user.username
        session.permanent = True
        return True
    return False


@app.before_request
def before_request():
    g.database = models.database
    g.database.connect()


@app.after_request
def after_request(request):
    g.database.close()
    return request


def valid_name(name):
    return (set(name) <= set(string.ascii_letters + string.digits + "-_")) and len(
        name
    ) >= 3


THUMB_SIZES = (64, 128, 256, 512)


def get_s3_client():
    return boto3.client("s3")


def gen_signed_post(s3_client):
    return s3_client.generate_presigned_post(
        Bucket=app.config["S3_BUCKET"],
        Key=base64.urlsafe_b64encode(os.urandom(6)).decode() + "/${filename}",
        Fields={
            "acl": "public-read",
            "success_action_status": "204",
        },
        Conditions=[
            {"acl": "public-read"},
            ["starts-with", "$success_action_status", "204"],
            ["starts-with", "$Content-Type", ""],
        ],
        ExpiresIn=600,
    )


def gen_image_dict(image):
    return {
        "title": image.title,
        "description": image.description,
        "s3_key": image.s3_key,
        "url": gen_cdn_url(image.s3_key, image.s3_bucket),
        "thumbs": {
            size: gen_cdn_url(gen_thumb_key(image.s3_key, size=size), image.s3_bucket)
            for size in THUMB_SIZES
        },
    }


def gen_thumb_key(key, size=THUMB_SIZES[0]):
    key = key.split("/")
    if len(key[-1].split(".")) > 1:
        filename = key[-1].split(".")
        filename[-1] = "jpg"
        key[-1] = ".".join(filename)
    else:
        key[-1] = ".".join((key[-1], "jpg"))
    size = "t{0}".format(size)
    key.insert(1, size)
    return "/".join(key)


def gen_s3_url(key, bucket):
    return f"https://s3.amazonaws.com/{bucket}/{quote_plus(key, safe='/')}"


def gen_cdn_url(key, bucket):
    if bucket in app.config["BUCKET_CDN"]:
        return f"{app.config['BUCKET_CDN'][bucket]}/{quote_plus(key, safe='/')}"
    return gen_s3_url(key, bucket)


def create_thumbnails(image, num_colors=9):
    if image.s3_key.split(".")[-1].lower() not in ("jpg", "jpeg", "png"):
        return
    s3 = get_s3_client()
    s3_object = s3.get_object(Bucket=image.s3_bucket, Key=image.s3_key)
    s3_object_body = tempfile.SpooledTemporaryFile()
    s3_object_body.write(s3_object["Body"].read())
    s3_object_body.seek(0)
    color_thief = ColorThief(s3_object_body)
    palette = color_thief.get_palette(color_count=num_colors + 1)
    palette = ["#{r:02x}{g:02x}{b:02x}".format(r=r, g=g, b=b) for r, g, b in palette]
    s3_object_body.seek(0)
    size = PImage.open(s3_object_body).size
    size = {"width": size[0], "height": size[1]}
    image.colors = json.dumps(palette)
    image.size = json.dumps(size)
    image.save()
    thumbs_object = {}
    for size in THUMB_SIZES:
        s3_object_body.seek(0)
        pil_object = PImage.open(s3_object_body)
        pil_object.thumbnail((size, size))
        thumb_image_size = pil_object.size
        thumb_image_size = {"width": thumb_image_size[0], "height": thumb_image_size[1]}
        thumb_file = tempfile.SpooledTemporaryFile()
        pil_object.save(thumb_file, format="JPEG", quality=60, optimize=True)
        thumb_file.seek(0)
        thumb_md5 = base64.b64encode(hashlib.md5(thumb_file.read()).digest()).decode()
        thumb_file.seek(0)
        thumb_s3_key = gen_thumb_key(image.s3_key, size=size)
        s3.put_object(
            Bucket=image.s3_bucket,
            Key=thumb_s3_key,
            ACL="public-read",
            ContentMD5=thumb_md5,
            ContentType="image/jpeg",
            Body=thumb_file.read(),
        )
        thumbs_object[size] = {
            "size": thumb_image_size,
            "url": gen_cdn_url(thumb_s3_key, image.s3_bucket),
        }
    image.thumbs = json.dumps(thumbs_object)
    image.save()


@app.route("/login")
@app.route("/create-account")
@app.route("/collections/<path:path>")
@app.route("/collections")
@app.route("/images/<path:path>")
@app.route("/images")
@app.route("/upload")
@app.route("/api-keys")
@app.route("/")
def index(path=""):
    return render_template("react-client.html")


def reprocess():
    images = models.Image.select()
    for image in images:
        create_thumbnails(image)
    return "Done."


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))


user_resource_fields = {
    "username": fields.String,
    "email": fields.String,
    "date_created": fields.DateTime(dt_format="iso8601"),
    "uri": fields.Url("user"),
}


class SignedPost(Resource):
    @auth.login_required
    def get(self):
        return gen_signed_post(get_s3_client())


session_resource_fields = {
    "user": fields.Nested(user_resource_fields, allow_null=True),
    "loggedIn": fields.Boolean(),
}

not_logged_in_response = {"loggedIn": False, "user": None}


class Session(Resource):
    @marshal_with(session_resource_fields)
    def get(self):
        if "username" in session:
            try:
                user = models.User.get(models.User.username == session.get("username"))
            except models.User.DoesNotExist:
                return not_logged_in_response
            return {"loggedIn": True, "user": model_to_dict(user)}
        return not_logged_in_response

    @marshal_with(session_resource_fields)
    def post(self):
        session.pop("username", None)
        if request.is_json:
            username = request.get_json().get("username")
            password = request.get_json().get("password")
        else:
            abort(
                400,
                message="Request must be of type application/json.",
            )
        if verify_password(username, password):
            return {"loggedIn": True, "user": model_to_dict(g.user)}
        else:
            return not_logged_in_response


class UserList(Resource):
    @auth.login_required
    @marshal_with(user_resource_fields)
    def get(self):
        users = models.User.select().where(
            models.User.username == g.user.username,
        )
        return [model_to_dict(user) for user in users]

    @marshal_with(user_resource_fields)
    def post(self):
        if request.is_json:
            username = request.get_json().get("username")
            email = request.get_json().get("email")
            password = request.get_json().get("password")
        else:
            abort(
                400,
                message="Request must be of type application/json.",
            )
        if not (username and email and password):
            abort(
                400,
                message="Username, email, and password must all be provided.",
            )
        if not valid_name(username):
            abort(
                400,
                message="Bad username.",
            )
        try:
            user = models.User.create(
                username=username,
                email=email,
                password=generate_password_hash(
                    password,
                    method="pbkdf2:sha256",
                ),
                date_created=datetime.datetime.utcnow(),
            )
        except models.IntegrityError:
            abort(
                409,
                message="Username or email already in use.",
            )
        return model_to_dict(user)


class User(Resource):
    @auth.login_required
    @marshal_with(user_resource_fields)
    def get(self, username):
        try:
            user = models.User.get(
                models.User.username == username,
                models.User.username == g.user.username,
            )
        except models.User.DoesNotExist:
            abort(
                404,
                message="User {0} does not exist.".format(username),
            )
        return model_to_dict(user)

    @auth.login_required
    @marshal_with(user_resource_fields)
    def put(self, username):
        try:
            user = models.User.get(
                models.User.username == username,
                models.User.username == g.user.username,
            )
        except models.User.DoesNotExist:
            abort(
                404,
                message="User {0} does not exist.".format(username),
            )
        if request.is_json:
            email = request.get_json().get("email")
            password = request.get_json().get("password")
        else:
            abort(
                400,
                message="Request must be of type application/json.",
            )
        if email:
            user.email = email
        if password:
            user.password = generate_password_hash(
                password,
                method="pbkdf2:sha256",
            )
        try:
            user.save()
        except models.IntegrityError:
            abort(
                409,
                message="Email address already in use.",
            )
        return model_to_dict(user)

    @auth.login_required
    @marshal_with(user_resource_fields)
    def delete(self, username):
        try:
            user = models.User.get(
                models.User.username == username,
                models.User.username == g.user.username,
            )
        except models.User.DoesNotExist:
            abort(
                404,
                message="User {0} does not exist.".format(username),
            )
        user.delete_instance(recursive=True)
        return model_to_dict(user)


api_key_resource_fields = {
    "key": fields.String,
    "user": fields.String(attribute="user.username"),
    "description": fields.String,
    "date_created": fields.DateTime(dt_format="iso8601"),
    "uri": fields.Url("apikey"),
}


class ApiKeyList(Resource):
    @auth.login_required
    @marshal_with(api_key_resource_fields)
    def get(self):
        api_keys = models.ApiKey.select().where(models.ApiKey.user == g.user)
        return [model_to_dict(api_key) for api_key in api_keys]

    @auth.login_required
    @marshal_with(api_key_resource_fields)
    def post(self):
        if request.is_json:
            description = request.get_json().get("description", "")
        else:
            description = ""
        api_key = models.ApiKey.create(
            key=base64.urlsafe_b64encode(os.urandom(24)).decode(),
            user=g.user,
            description=description,
            date_created=datetime.datetime.utcnow(),
        )
        return model_to_dict(api_key)


class ApiKey(Resource):
    @auth.login_required
    @marshal_with(api_key_resource_fields)
    def get(self, key):
        try:
            api_key = models.ApiKey.get(
                models.ApiKey.key == key,
                models.ApiKey.user == g.user,
            )
        except models.ApiKey.DoesNotExist:
            abort(404, message="API key {0} does not exist.".format(key))
        return model_to_dict(api_key)

    @auth.login_required
    @marshal_with(api_key_resource_fields)
    def put(self, key):
        try:
            api_key = models.ApiKey.get(
                models.ApiKey.key == key,
                models.ApiKey.user == g.user,
            )
        except models.ApiKey.DoesNotExist:
            abort(404, message="API key {0} does not exist.".format(key))
        if request.is_json:
            description = request.get_json().get("description")
        else:
            abort(
                400,
                message="Request must be of type application/json.",
            )
        if description is not None:
            api_key.description = description
        api_key.save()
        return model_to_dict(api_key)

    @auth.login_required
    @marshal_with(api_key_resource_fields)
    def delete(self, key):
        try:
            api_key = models.ApiKey.get(
                models.ApiKey.key == key,
                models.ApiKey.user == g.user,
            )
        except models.ApiKey.DoesNotExist:
            abort(404, message="API key {0} does not exist.".format(key))
        api_key.delete_instance(recursive=True)
        return model_to_dict(api_key)


collection_resource_fields = {
    "user": fields.String(attribute="user.username"),
    "name": fields.String,
    "uri": fields.Url("collection"),
}


class CollectionList(Resource):
    @auth.login_required
    @marshal_with(collection_resource_fields)
    def get(self):
        collections = models.Collection.select().where(
            models.Collection.user == g.user,
        )
        return [model_to_dict(collection) for collection in collections]

    @auth.login_required
    @marshal_with(collection_resource_fields)
    def post(self):
        if request.is_json:
            name = request.get_json().get("name")
        else:
            abort(
                400,
                message="Request must be of type application/json.",
            )
        if not valid_name(name):
            abort(
                400,
                message="Bad collection name.",
            )
        try:
            collection = models.Collection.create(
                name=name,
                user=g.user,
            )
        except models.IntegrityError:
            abort(409, message="A collection named {0} already exists.".format(name))
        return model_to_dict(collection)


class JSONField(fields.Raw):
    def format(self, json_string):
        try:
            return json.loads(json_string)
        except json.decoder.JSONDecodeError:
            return None


image_resource_fields = {
    "s3_key": fields.String,
    "s3_bucket": fields.String,
    "url": fields.String(
        attribute=lambda image: gen_cdn_url(image["s3_key"], image["s3_bucket"])
    ),
    "user": fields.String(attribute="user.username"),
    "title": fields.String,
    "description": fields.String,
    "date_created": fields.DateTime(dt_format="iso8601"),
    "uri": fields.Url("image"),
    "colors": JSONField(),
    "size": JSONField(),
    "thumbs": JSONField(),
}

collection_images_resource_fields = {
    **collection_resource_fields,
    "images": fields.List(fields.Nested(image_resource_fields)),
}


class Collection(Resource):
    @marshal_with(collection_images_resource_fields)
    def get(self, name):
        try:
            collection = models.Collection.get(
                models.Collection.name == name,
            )
        except models.Collection.DoesNotExist:
            abort(404, message="A collection named {0} does not exist.".format(name))
        images = (
            models.Image.select(models.Image, models.User)
            .join(models.User)
            .switch(models.Image)
            .join(models.ImageCollection)
            .where(models.ImageCollection.collection == collection)
        )
        collection = {
            **model_to_dict(collection),
            "images": [model_to_dict(image) for image in images],
        }
        return collection, {"Access-Control-Allow-Origin": "*"}

    @auth.login_required
    @marshal_with(collection_resource_fields)
    def delete(self, name):
        try:
            collection = models.Collection.get(
                models.Collection.name == name,
                models.Collection.user == g.user,
            )
        except models.Collection.DoesNotExist:
            abort(404, message="A collection named {0} does not exist.".format(name))
        collection.delete_instance(recursive=True)
        return model_to_dict(collection)


class CollectionImageList(Resource):
    @auth.login_required
    @marshal_with(image_resource_fields)
    def get(self, name):
        try:
            collection = models.Collection.get(
                models.Collection.name == name,
                models.Collection.user == g.user,
            )
        except models.Collection.DoesNotExist:
            abort(404, message="A collection named {0} does not exist.".format(name))
        images = (
            models.Image.select(models.Image, models.User)
            .join(models.User)
            .switch(models.Image)
            .join(models.ImageCollection)
            .where(models.ImageCollection.collection == collection)
        )
        return [model_to_dict(image) for image in images]


class CollectionImage(Resource):
    @auth.login_required
    @marshal_with(image_resource_fields)
    def get(self, name, s3_key):
        try:
            collection = models.Collection.get(
                models.Collection.name == name,
                models.Collection.user == g.user,
            )
        except models.Collection.DoesNotExist:
            abort(404, message="A collection named {0} does not exist.".format(name))
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(404, message="Image with s3_key {0} does not exist.".format(s3_key))
        try:
            image_collection = models.ImageCollection.get(
                models.ImageCollection.image == image,
                models.ImageCollection.collection == collection,
            )
        except models.ImageCollection.DoesNotExist:
            abort(
                404,
                message=(
                    "Image with s3_key {0} is not in collection {1}.".format(
                        s3_key, name
                    )
                ),
            )
        return model_to_dict(image)

    @auth.login_required
    @marshal_with(image_resource_fields)
    def put(self, name, s3_key):
        try:
            collection = models.Collection.get(
                models.Collection.name == name,
                models.Collection.user == g.user,
            )
        except models.Collection.DoesNotExist:
            abort(404, message="A collection named {0} does not exist.".format(name))
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(404, message="Image with s3_key {0} does not exist.".format(s3_key))
        try:
            models.ImageCollection.create(
                collection=collection,
                image=image,
            )
        except models.IntegrityError:
            pass
        return model_to_dict(image)

    @auth.login_required
    @marshal_with(image_resource_fields)
    def delete(self, name, s3_key):
        try:
            collection = models.Collection.get(
                models.Collection.name == name,
                models.Collection.user == g.user,
            )
        except models.Collection.DoesNotExist:
            abort(404, message="A collection named {0} does not exist.".format(name))
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(404, message="Image with s3_key {0} does not exist.".format(s3_key))
        try:
            image_collection = models.ImageCollection.get(
                models.ImageCollection.image == image,
                models.ImageCollection.collection == collection,
            )
        except models.ImageCollection.DoesNotExist:
            abort(
                404,
                message=(
                    "Image with s3_key {0} is not in collection {1}.".format(
                        s3_key, name
                    )
                ),
            )
        image_collection.delete_instance(recursive=True)
        return model_to_dict(image)


class ImageList(Resource):
    @auth.login_required
    @marshal_with(image_resource_fields)
    def get(self):
        images = (
            models.Image.select(models.Image, models.User)
            .join(models.User)
            .where(models.Image.user == g.user)
        )
        return [model_to_dict(image) for image in images]

    @auth.login_required
    @marshal_with(image_resource_fields)
    def post(self):
        if request.is_json:
            s3_key = request.get_json().get("s3_key")
            s3_bucket = request.get_json().get("s3_bucket", app.config["S3_BUCKET"])
            title = request.get_json().get("title", "")
            description = request.get_json().get("description", "")
        else:
            abort(400, message="Request must be of type application/json.")
        if not (s3_key and s3_bucket):
            abort(400, message="Fields s3_key and s3_bucket must be provided.")
        try:
            image = models.Image.create(
                user=g.user,
                s3_key=s3_key,
                s3_bucket=s3_bucket,
                title=title,
                description=description,
                date_created=datetime.datetime.utcnow(),
            )
        except models.IntegrityError:
            abort(
                409,
                message="Integrity Error.",
            )
        create_thumbnails(image)
        return model_to_dict(image)


class Image(Resource):
    @marshal_with(image_resource_fields)
    def get(self, s3_key):
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
            )
        except models.Image.DoesNotExist:
            abort(404, message="Image with s3_key {0} does not exist.".format(s3_key))
        return model_to_dict(image), {"Access-Control-Allow-Origin": "*"}

    @auth.login_required
    @marshal_with(image_resource_fields)
    def put(self, s3_key):
        if request.is_json:
            title = request.get_json().get("title")
            description = request.get_json().get("description")
        else:
            abort(400, message="Request must be of type application/json.")
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(404, message="Image with s3_key {0} does not exist.".format(s3_key))
        if description is not None:
            image.description = description
        if title is not None:
            image.title = title
        image.save()
        return model_to_dict(image)

    @auth.login_required
    @marshal_with(image_resource_fields)
    def delete(self, s3_key):
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(404, message="Image with s3_key {0} does not exist.".format(s3_key))
        image.delete_instance(recursive=True)
        return model_to_dict(image)


api.add_resource(SignedPost, "/api/signed-post")
api.add_resource(Session, "/api/session")
api.add_resource(UserList, "/api/users")
api.add_resource(User, "/api/users/<username>")
api.add_resource(ApiKeyList, "/api/api-keys")
api.add_resource(ApiKey, "/api/api-keys/<key>")
api.add_resource(CollectionList, "/api/collections")
api.add_resource(Collection, "/api/collections/<name>", "/api/c/<name>")
api.add_resource(ImageList, "/api/images")
api.add_resource(Image, "/api/images/<path:s3_key>", "/api/i/<path:s3_key>")
api.add_resource(CollectionImageList, "/api/collections/<name>/images")
api.add_resource(
    CollectionImage,
    "/api/collections/<name>/images/<path:s3_key>",
)
