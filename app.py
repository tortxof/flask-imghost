import os
import base64
import datetime
from functools import wraps
import tempfile
import hashlib
from urllib.parse import quote_plus

from flask import (
    Flask, render_template, request, g, session, redirect,
    url_for, jsonify
)
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api, abort, fields, marshal_with
from playhouse.shortcuts import model_to_dict
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from PIL import Image as PImage

import models

models.database.connect()
models.database.create_tables(
    [
        models.User,
        models.Collection,
        models.Image,
        models.ImageCollection,
        models.ApiKey
    ],
    safe=True,
)
models.database.close()

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

app.config['APP_URL'] = os.environ.get('APP_URL')

app.config['S3_BUCKET'] = os.environ.get('S3_BUCKET')

app.config['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')

@auth.verify_password
def verify_password(username, password):
    if 'username' in session:
        try:
            user = models.User.get(
                models.User.username == session.get('username')
            )
        except models.User.DoesNotExist:
            session.pop('username', None)
        g.user = user
        return True
    try:
        api_key = models.ApiKey.get(models.ApiKey.key == password)
    except models.ApiKey.DoesNotExist:
        pass
    else:
        if api_key:
            g.user = api_key.user
            session['username'] = g.user.username
            return True
    try:
        user = models.User.get(models.User.username == username)
    except models.User.DoesNotExist:
        return False
    if check_password_hash(user.password, password):
        g.user = user
        session['username'] = g.user.username
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

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('username'):
            return f(*args, **kwargs)
        else:
            flash('You are not logged in.')
            return redirect(url_for('login'))
    return wrapper

THUMB_SIZES = (64, 128, 256, 512)

def get_current_user():
    return models.User.get(models.User.username == session['username'])

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id = app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key = app.config['AWS_SECRET_ACCESS_KEY']
        )

def gen_image_dict(image):
    return {
        'title': image.title,
        'description': image.description,
        's3_key': image.s3_key,
        'url': gen_s3_url(image.s3_key, image.s3_bucket),
        'thumbs': {
            size: gen_s3_url(
                gen_thumb_key(image.s3_key, size=size),
                image.s3_bucket
            )
            for size in THUMB_SIZES
        }
    }

@app.template_filter('gen_thumb_key')
def gen_thumb_key(key, size=THUMB_SIZES[0]):
    key = key.split('/')
    if len(key[-1].split('.')) > 1:
        filename = key[-1].split('.')
        filename[-1] = 'jpg'
        key[-1] = '.'.join(filename)
    else:
        key[-1] = '.'.join((key[-1], 'jpg'))
    size = 't{0}'.format(size)
    key.insert(1, size)
    return '/'.join(key)

@app.template_filter('gen_s3_url')
def gen_s3_url(key, bucket):
    return 'https://s3.amazonaws.com/{0}/{1}'.format(
        bucket,
        quote_plus(key, safe='/')
    )

def create_thumbnails(image):
    for size in THUMB_SIZES:
        s3 = get_s3_client()
        s3_object = s3.get_object(
            Bucket = image.s3_bucket,
            Key = image.s3_key
        )
        pil_object = PImage.open(s3_object['Body'])
        pil_object.thumbnail((size, size))
        thumb_file = tempfile.SpooledTemporaryFile()
        pil_object.save(thumb_file, format='JPEG', quality=60, optimize=True)
        thumb_file.seek(0)
        thumb_md5 = base64.b64encode(
            hashlib.md5(thumb_file.read()).digest()
        ).decode()
        thumb_file.seek(0)
        thumb_s3_key = gen_thumb_key(image.s3_key, size=size)
        s3.put_object(
            Bucket = image.s3_bucket,
            Key = thumb_s3_key,
            ACL = 'public-read',
            ContentMD5 = thumb_md5,
            ContentType = 'image/jpeg',
            Body = thumb_file.read(),
        )

@app.route('/login')
@app.route('/create-account')
@app.route('/collections')
@app.route('/images')
@app.route('/api-keys')
@app.route('/')
def index():
    return render_template('react-client.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error_flash_message = 'Incorrect name or password.'
#     if request.method == 'POST':
#         try:
#             user = models.User.get(
#                 models.User.username == request.form['username'],
#             )
#         except models.User.DoesNotExist:
#             flash(error_flash_message)
#             return render_template('login.html')
#         if check_password_hash(user.password, request.form['password']):
#             session['username'] = user.username
#             session.permanent = True
#             flash('You are now logged in.')
#             return redirect(url_for('index'))
#         else:
#             flash(error_flash_message)
#             return render_template('login.html')
#     else:
#         return render_template('login.html')
#
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         password_hash = generate_password_hash(
#             request.form['password'],
#             method = 'pbkdf2:sha256'
#         )
#         try:
#             models.User.create(
#                 email = request.form['email'],
#                 username = request.form['username'],
#                 password = password_hash,
#                 date_created = datetime.datetime.utcnow(),
#             )
#         except models.IntegrityError:
#             flash('That name or email is already taken.')
#             return redirect(url_for('signup'))
#         flash('Account created.')
#         return redirect(url_for('login'))
#     else:
#         return render_template('signup.html')
#
# @app.route('/collections')
# @login_required
# def collections():
#     user = get_current_user()
#     collections = models.Collection.select().where(
#         models.Collection.user == user,
#     )
#     return render_template('collections.html', collections=collections)
#
# @app.route('/collections/delete', methods=['POST'])
# def collections_delete():
#     user = get_current_user()
#     if request.form.get('delete'):
#         collections = [
#             models.Collection.get(
#                 (models.Collection.name == k) &
#                 (models.Collection.user == user)
#             )
#             for k, v in request.form.to_dict().items() if v == 'selected'
#         ]
#         for collection in collections:
#             collection.delete_instance(recursive=True)
#             flash('Collection {0} deleted'.format(collection.name))
#     return redirect(url_for('collections'))
#
# @app.route('/collections/create', methods=['POST'])
# @login_required
# def collections_create():
#     user = get_current_user()
#     name = request.form.get('name')
#     try:
#         models.Collection.create(
#             user = user,
#             name = name
#         )
#     except models.IntegrityError:
#         flash('A collection with that name already exists.')
#         return redirect(url_for('collections'))
#     flash('New collection created.')
#     return redirect(url_for('collections'))
#
# @app.route('/images', methods=['GET', 'POST'])
# @login_required
# def images():
#     user = get_current_user()
#     if request.method == 'POST':
#         images = [
#             models.Image.get(
#                 (models.Image.s3_key == k) &
#                 (models.Image.user == user)
#             )
#             for k, v in request.form.to_dict().items() if v == 'selected'
#         ]
#         if request.form.get('add_to_collection'):
#             collection = models.Collection.get(
#                 (models.Collection.id == request.form.get('collection')) &
#                 (models.Collection.user == user)
#             )
#             for image in images:
#                 try:
#                     models.ImageCollection.create(
#                         image = image,
#                         collection = collection
#                     )
#                     flash(
#                         'Image {0} added to collection {1}'
#                         .format(image.s3_key, collection.name)
#                     )
#                 except models.IntegrityError:
#                     flash(
#                         'Image {0} is already in collection {1}'
#                         .format(image.s3_key, collection.name)
#                     )
#             return redirect(url_for('images'))
#         elif request.form.get('delete'):
#             s3 = get_s3_client()
#             for image in images:
#                 image.delete_instance(recursive=True)
#                 s3.delete_object(
#                     Bucket = image.s3_bucket,
#                     Key = image.s3_key
#                 )
#                 for size in THUMB_SIZES:
#                     s3.delete_object(
#                         Bucket = image.s3_bucket,
#                         Key = gen_thumb_key(image.s3_key, size=size)
#                     )
#                 flash('Image {0} deleted'.format(image.s3_key))
#             return redirect(url_for('images'))
#     else:
#         images = models.Image.select().where(models.Image.user == user)
#         collections = models.Collection.select().where(
#             models.Collection.user == user,
#         )
#         return render_template(
#             'images.html', images=images, collections=collections
#         )
#
# @app.route('/upload')
# @login_required
# def upload():
#     user = get_current_user()
#     args = request.args.to_dict()
#     if args:
#         try:
#             image = models.Image.create(
#                 s3_key = args['key'],
#                 s3_bucket = args['bucket'],
#                 user = user,
#                 date_created = datetime.datetime.utcnow()
#             )
#             flash('Image {0} added.'.format(args['key']))
#         except models.IntegrityError:
#             flash('Image already exists.')
#         create_thumbnails(image)
#     key_prefix = base64.urlsafe_b64encode(os.urandom(6)).decode()
#     s3 = get_s3_client()
#     post = s3.generate_presigned_post(
#         Bucket = app.config['S3_BUCKET'],
#         Key = key_prefix + '/${filename}',
#         Fields = {
#             'acl': 'public-read',
#             'success_action_redirect': '{0}/upload'.format(
#                 app.config['APP_URL']
#             )
#         },
#         Conditions = [
#             {'acl': 'public-read'},
#             ['starts-with', '$key', key_prefix],
#             ['starts-with', '$success_action_redirect', app.config['APP_URL']],
#             ['starts-with', '$Content-Type', 'image/'],
#         ],
#         ExpiresIn = 600
#     )
#     return render_template('upload.html', post=post)

@app.route('/api/c/<collection_name>')
def get_json_collection(collection_name):
    collection = models.Collection.get(
        models.Collection.name == collection_name,
    )
    return jsonify(
        name = collection.name,
        images = [
            gen_image_dict(image)
            for image in collection.images()
        ]
    ), 200, {'Access-Control-Allow-Origin': '*'}

@app.route('/api/i/<path:s3_key>')
def get_json_image(s3_key):
    image = models.Image.get(models.Image.s3_key == s3_key)
    return jsonify(
        gen_image_dict(image)
    ), 200, {'Access-Control-Allow-Origin': '*'}

user_resource_fields = {
    'username': fields.String,
    'email': fields.String,
    'date_created': fields.DateTime(dt_format='iso8601'),
    'uri': fields.Url('user')
}

class Session(Resource):
    @marshal_with({
        'user': fields.Nested(user_resource_fields, allow_null=True),
        'loggedIn': fields.Boolean(),
        })
    def get(self):
        not_logged_in_response = {'loggedIn': False, 'user': None}
        if 'username' in session:
            try:
                user = models.User.get(models.User.username == session.get('username'))
            except models.User.DoesNotExist:
                return not_logged_in_response
            return {'loggedIn': True, 'user': model_to_dict(user)}
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
            username = request.get_json().get('username')
            email = request.get_json().get('email')
            password = request.get_json().get('password')
        else:
            abort(
                400,
                message = 'Request must be of type application/json.',
            )
        if not (username and email and password):
            abort(
                400,
                message = 'Username, email, and password must all be provided.',
            )
        try:
            user = models.User.create(
                username = username,
                email = email,
                password = generate_password_hash(
                    password,
                    method = 'pbkdf2:sha256',
                ),
                date_created = datetime.datetime.utcnow(),
            )
        except models.IntegrityError:
            abort(
                409,
                message = 'Username or email already in use.',
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
                message = 'User {0} does not exist.'.format(username),
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
                message = 'User {0} does not exist.'.format(username),
            )
        if request.is_json:
            email = request.get_json().get('email')
            password = request.get_json().get('password')
        else:
            abort(
                400,
                message = 'Request must be of type application/json.',
            )
        if email:
            user.email = email
        if password:
            user.password = generate_password_hash(
                password,
                method = 'pbkdf2:sha256',
            )
        try:
            user.save()
        except models.IntegrityError:
            abort(
                409,
                message = 'Email address already in use.',
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
                message = 'User {0} does not exist.'.format(username),
            )
        user.delete_instance(recursive=True)
        return model_to_dict(user)

api_key_resource_fields = {
    'key': fields.String,
    'user': fields.String(attribute='user.username'),
    'description': fields.String,
    'date_created': fields.DateTime(dt_format='iso8601'),
    'uri': fields.Url('apikey'),
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
            description = request.get_json().get('description', '')
        else:
            description = ''
        api_key = models.ApiKey.create(
            key = base64.urlsafe_b64encode(os.urandom(24)).decode(),
            user = g.user,
            description = description,
            date_created = datetime.datetime.utcnow(),
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
            abort(
                404,
                message = 'API key {0} does not exist.'.format(key)
            )
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
            abort(
                404,
                message = 'API key {0} does not exist.'.format(key)
            )
        if request.is_json:
            description = request.get_json().get('description')
        else:
            abort(
                400,
                message = 'Request must be of type application/json.',
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
            abort(
                404,
                message = 'API key {0} does not exist.'.format(key)
            )
        api_key.delete_instance(recursive=True)
        return model_to_dict(api_key)

collection_resource_fields = {
    'user': fields.String(attribute='user.username'),
    'name': fields.String,
    'uri': fields.Url('collection'),
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
            name = request.get_json().get('name')
        else:
            abort(
                400,
                message = 'Request must be of type application/json.',
            )
        if not name:
            abort(
                400,
                message = 'Bad collection name.',
            )
        try:
            collection = models.Collection.create(
                name = name,
                user = g.user,
            )
        except models.IntegrityError:
            abort(
                409,
                message = 'A collection named {0} already exists.'.format(name)
            )
        return model_to_dict(collection)

image_resource_fields = {
    's3_key': fields.String,
    's3_bucket': fields.String,
    'user': fields.String(attribute='user.username'),
    'title': fields.String,
    'description': fields.String,
    'date_created': fields.DateTime(dt_format='iso8601'),
    'uri': fields.Url('image'),
}

collection_images_resource_fields = {
    **collection_resource_fields,
    'images': fields.List(fields.Nested(image_resource_fields)),
}

class Collection(Resource):
    @auth.login_required
    @marshal_with(collection_images_resource_fields)
    def get(self, name):
        try:
            collection = models.Collection.get(
                models.Collection.name == name,
                models.Collection.user == g.user,
            )
        except models.Collection.DoesNotExist:
            abort(
                404,
                message = 'A collection named {0} does not exist.'.format(name)
            )
        images = [model_to_dict(image) for image in collection.images()]
        collection = {
            **model_to_dict(collection),
            'images': images,
            }
        return collection

    @auth.login_required
    @marshal_with(collection_resource_fields)
    def delete(self, name):
        try:
            collection = models.Collection.get(
                models.Collection.name == name,
                models.Collection.user == g.user,
            )
        except models.Collection.DoesNotExist:
            abort(
                404,
                message = 'A collection named {0} does not exist.'.format(name)
            )
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
            abort(
                404,
                message = 'A collection named {0} does not exist.'.format(name)
            )
        images = collection.images()
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
            abort(
                404,
                message = 'A collection named {0} does not exist.'.format(name)
            )
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
        try:
            image_collection = models.ImageCollection.get(
                models.ImageCollection.image == image,
                models.ImageCollection.collection == collection,
            )
        except models.ImageCollection.DoesNotExist:
            abort(
                404,
                message = (
                    'Image with s3_key {0} '
                    'is not in collection {1}.'.format(s3_key, name)
                )
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
            abort(
                404,
                message = 'A collection named {0} does not exist.'.format(name)
            )
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
        try:
            models.ImageCollection.create(
                collection = collection,
                image = image,
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
            abort(
                404,
                message = 'A collection named {0} does not exist.'.format(name)
            )
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
        try:
            image_collection = models.ImageCollection.get(
                models.ImageCollection.image == image,
                models.ImageCollection.collection == collection,
            )
        except models.ImageCollection.DoesNotExist:
            abort(
                404,
                message = (
                    'Image with s3_key {0} '
                    'is not in collection {1}.'.format(s3_key, name)
                )
            )
        image_collection.delete_instance(recursive=True)
        return model_to_dict(image)

class ImageList(Resource):
    @auth.login_required
    @marshal_with(image_resource_fields)
    def get(self):
        images = models.Image.select().where(models.Image.user == g.user)
        return [model_to_dict(image) for image in images]

    @auth.login_required
    @marshal_with(image_resource_fields)
    def post(self):
        if request.is_json:
            s3_key = request.get_json().get('s3_key')
            s3_bucket = request.get_json().get('s3_bucket')
            title = request.get_json().get('title', '')
            description = request.get_json().get('description', '')
        else:
            abort(
                400,
                message = 'Request must be of type application/json.'
            )
        if not (s3_key and s3_bucket):
            abort(
                400,
                message = 'Fields s3_key and s3_bucket must be provided.'
            )
        try:
            image = models.Image.create(
                user = g.user,
                s3_key = s3_key,
                s3_bucket = s3_bucket,
                title = title,
                description = description,
                date_created = datetime.datetime.utcnow(),
            )
        except models.IntegrityError:
            abort(
                409,
                message = 'Integrity Error.',
            )
        return model_to_dict(image)

class Image(Resource):
    @auth.login_required
    @marshal_with(image_resource_fields)
    def get(self, s3_key):
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
        return model_to_dict(image)

    @auth.login_required
    @marshal_with(image_resource_fields)
    def put(self, s3_key):
        if request.is_json:
            title = request.get_json().get('title')
            description = request.get_json().get('description')
        else:
            abort(
                400,
                message = 'Request must be of type application/json.'
            )
        try:
            image = models.Image.get(
                models.Image.s3_key == s3_key,
                models.Image.user == g.user,
            )
        except models.Image.DoesNotExist:
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
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
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
        image.delete_instance(recursive=True)
        return model_to_dict(image)

api.add_resource(Session, '/api/session')
api.add_resource(UserList, '/api/users')
api.add_resource(User, '/api/users/<username>')
api.add_resource(ApiKeyList, '/api/api-keys')
api.add_resource(ApiKey, '/api/api-keys/<key>')
api.add_resource(CollectionList, '/api/collections')
api.add_resource(Collection, '/api/collections/<name>')
api.add_resource(ImageList, '/api/images')
api.add_resource(Image, '/api/images/<path:s3_key>')
api.add_resource(CollectionImageList, '/api/collections/<name>/images')
api.add_resource(CollectionImage, '/api/collections/<name>/images/<path:s3_key>')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
