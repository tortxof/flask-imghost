import os
import base64
import datetime
from functools import wraps
import tempfile
import hashlib
from urllib.parse import quote_plus

from flask import (
    Flask, render_template, request, flash, g, session, redirect,
    url_for, jsonify
)
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api, abort
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from PIL import Image as PImage

from database import (
    database, User, Collection, Image, ImageCollection, ApiKey, IntegrityError
)

database.connect()
database.create_tables(
    [User, Collection, Image, ImageCollection, ApiKey],
    safe=True
)
database.close()

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
    try:
        api_key = ApiKey.get(ApiKey.key == password)
    except ApiKey.DoesNotExist:
        pass
    else:
        if api_key:
            g.user = api_key.user
            return True
    try:
        user = User.get(User.username == username)
    except User.DoesNotExist:
        return False
    if check_password_hash(user.password, password):
        g.user = user
        return True
    return False

@app.before_request
def before_request():
    g.database = database
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
    return User.get(User.username == session['username'])

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_flash_message = 'Incorrect name or password.'
    if request.method == 'POST':
        try:
            user = User.get(User.username == request.form['username'])
        except User.DoesNotExist:
            flash(error_flash_message)
            return render_template('login.html')
        if check_password_hash(user.password, request.form['password']):
            session['username'] = user.username
            session.permanent = True
            flash('You are now logged in.')
            return redirect(url_for('index'))
        else:
            flash(error_flash_message)
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        password_hash = generate_password_hash(
            request.form['password'],
            method = 'pbkdf2:sha256'
        )
        try:
            User.create(
                email = request.form['email'],
                username = request.form['username'],
                password = password_hash,
                date_created = datetime.datetime.utcnow(),
            )
        except IntegrityError:
            flash('That name or email is already taken.')
            return redirect(url_for('signup'))
        flash('Account created.')
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')

@app.route('/collections')
@login_required
def collections():
    user = get_current_user()
    collections = Collection.select().where(Collection.user == user)
    return render_template('collections.html', collections=collections)

@app.route('/collections/delete', methods=['POST'])
def collections_delete():
    user = get_current_user()
    if request.form.get('delete'):
        collections = [
            Collection.get(
                (Collection.name == k) &
                (Collection.user == user)
            )
            for k, v in request.form.to_dict().items() if v == 'selected'
        ]
        for collection in collections:
            collection.delete_instance(recursive=True)
            flash('Collection {0} deleted'.format(collection.name))
    return redirect(url_for('collections'))

@app.route('/collections/create', methods=['POST'])
@login_required
def collections_create():
    user = get_current_user()
    name = request.form.get('name')
    try:
        Collection.create(
            user = user,
            name = name
        )
    except IntegrityError:
        flash('A collection with that name already exists.')
        return redirect(url_for('collections'))
    flash('New collection created.')
    return redirect(url_for('collections'))

@app.route('/images', methods=['GET', 'POST'])
@login_required
def images():
    user = get_current_user()
    if request.method == 'POST':
        images = [
            Image.get(
                (Image.s3_key == k) &
                (Image.user == user)
            )
            for k, v in request.form.to_dict().items() if v == 'selected'
        ]
        if request.form.get('add_to_collection'):
            collection = Collection.get(
                (Collection.id == request.form.get('collection')) &
                (Collection.user == user)
            )
            for image in images:
                try:
                    ImageCollection.create(
                        image = image,
                        collection = collection
                    )
                    flash(
                        'Image {0} added to collection {1}'
                        .format(image.s3_key, collection.name)
                    )
                except IntegrityError:
                    flash(
                        'Image {0} is already in collection {1}'
                        .format(image.s3_key, collection.name)
                    )
            return redirect(url_for('images'))
        elif request.form.get('delete'):
            s3 = get_s3_client()
            for image in images:
                image.delete_instance(recursive=True)
                s3.delete_object(
                    Bucket = image.s3_bucket,
                    Key = image.s3_key
                )
                for size in THUMB_SIZES:
                    s3.delete_object(
                        Bucket = image.s3_bucket,
                        Key = gen_thumb_key(image.s3_key, size=size)
                    )
                flash('Image {0} deleted'.format(image.s3_key))
            return redirect(url_for('images'))
    else:
        images = Image.select().where(Image.user == user)
        collections = Collection.select().where(Collection.user == user)
        return render_template(
            'images.html', images=images, collections=collections
        )

@app.route('/upload')
@login_required
def upload():
    user = get_current_user()
    args = request.args.to_dict()
    if args:
        try:
            image = Image.create(
                s3_key = args['key'],
                s3_bucket = args['bucket'],
                user = user,
                date_created = datetime.datetime.utcnow()
            )
            flash('Image {0} added.'.format(args['key']))
        except IntegrityError:
            flash('Image already exists.')
        create_thumbnails(image)
    key_prefix = base64.urlsafe_b64encode(os.urandom(6)).decode()
    s3 = get_s3_client()
    post = s3.generate_presigned_post(
        Bucket = app.config['S3_BUCKET'],
        Key = key_prefix + '/${filename}',
        Fields = {
            'acl': 'public-read',
            'success_action_redirect': '{0}/upload'.format(
                app.config['APP_URL']
            )
        },
        Conditions = [
            {'acl': 'public-read'},
            ['starts-with', '$key', key_prefix],
            ['starts-with', '$success_action_redirect', app.config['APP_URL']],
            ['starts-with', '$Content-Type', 'image/'],
        ],
        ExpiresIn = 600
    )
    return render_template('upload.html', post=post)

@app.route('/api/c/<collection_name>')
def get_json_collection(collection_name):
    collection = Collection.get(Collection.name == collection_name)
    return jsonify(
        name = collection.name,
        images = [
            gen_image_dict(image)
            for image in collection.images()
        ]
    ), 200, {'Access-Control-Allow-Origin': '*'}

@app.route('/api/i/<path:s3_key>')
def get_json_image(s3_key):
    image = Image.get(Image.s3_key == s3_key)
    return jsonify(
        gen_image_dict(image)
    ), 200, {'Access-Control-Allow-Origin': '*'}

class RestUserList(Resource):
    @auth.login_required
    def get(self):
        users = User.select().where(User.username == g.user.username)
        return [
            {
                'username': user.username,
                'email': user.email,
                'date_created': user.date_created.isoformat(),
            } for user in users
        ]

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
            user = User.create(
                username = username,
                email = email,
                password = generate_password_hash(
                    password,
                    method = 'pbkdf2:sha256',
                ),
                date_created = datetime.datetime.utcnow(),
            )
        except IntegrityError:
            abort(
                409,
                message = 'Username or email already in use.',
            )
        return {
            'username': user.username,
            'email': user.email,
            'date_created': user.date_created.isoformat(),
        }

class RestUser(Resource):
    @auth.login_required
    def get(self, username):
        try:
            user = User.get(
                User.username == username,
                User.username == g.user.username,
            )
        except User.DoesNotExist:
            abort(
                404,
                message = 'User {0} does not exist.'.format(username),
            )
        return {
            'username': user.username,
            'email': user.email,
            'date_created': user.date_created.isoformat(),
        }

    @auth.login_required
    def put(self, username):
        try:
            user = User.get(
                User.username == username,
                User.username == g.user.username,
            )
        except User.DoesNotExist:
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
        except IntegrityError:
            abort(
                409,
                message = 'Email address already in use.',
            )
        return {
            'username': user.username,
            'email': user.email,
            'date_created': user.date_created.isoformat(),
        }

    @auth.login_required
    def delete(self, username):
        try:
            user = User.get(
                User.username == username,
                User.username == g.user.username,
            )
        except User.DoesNotExist:
            abort(
                404,
                message = 'User {0} does not exist.'.format(username),
            )
        user.delete_instance(recursive=True)
        return {
            'username': user.username,
            'email': user.email,
            'date_created': user.date_created.isoformat(),
        }

class RestApiKeyList(Resource):
    @auth.login_required
    def get(self):
        api_keys = ApiKey.select().where(ApiKey.user == g.user)
        return [
            {
                'key': api_key.key,
                'user': api_key.user.username,
                'description': api_key.description,
                'date_created': api_key.date_created.isoformat(),
            } for api_key in api_keys
        ]

    @auth.login_required
    def post(self):
        if request.is_json:
            description = request.get_json().get('description', '')
        else:
            description = ''
        api_key = ApiKey.create(
            key = base64.urlsafe_b64encode(os.urandom(24)).decode(),
            user = g.user,
            description = description,
            date_created = datetime.datetime.utcnow(),
        )
        return {
            'key': api_key.key,
            'user': api_key.user.username,
            'description': api_key.description,
            'date_created': api_key.date_created.isoformat(),
        }

class RestApiKey(Resource):
    @auth.login_required
    def get(self, api_key_str):
        try:
            api_key = ApiKey.get(
                ApiKey.key == api_key_str,
                ApiKey.user == g.user,
            )
        except ApiKey.DoesNotExist:
            abort(
                404,
                message = 'API key {0} does not exist.'.format(api_key_str)
            )
        else:
            return {
                'key': api_key.key,
                'user': api_key.user.username,
                'description': api_key.description,
                'date_created': api_key.date_created.isoformat(),
            }

class RestCollectionList(Resource):
    @auth.login_required
    def get(self):
        collections = Collection.select().where(Collection.user == g.user)
        return [collection.plain_dict_short() for collection in collections]

    @auth.login_required
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
            collection = Collection.create(
                name = name,
                user = g.user,
            )
        except IntegrityError:
            abort(
                409,
                message = 'A collection named {0} already exists.'.format(name)
            )
        return collection.plain_dict()

class RestCollection(Resource):
    @auth.login_required
    def get(self, name):
        try:
            collection = Collection.get(
                Collection.name == name,
                Collection.user == g.user,
            )
        except Collection.DoesNotExist:
            abort(
                404,
                message = 'A collection named {0} does not exist.'.format(name)
            )
        return collection.plain_dict()

class RestImageList(Resource):
    @auth.login_required
    def get(self):
        images = Image.select().where(Image.user == g.user)
        return [image.plain_dict() for image in images]

    @auth.login_required
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
            image = Image.create(
                user = g.user,
                s3_key = s3_key,
                s3_bucket = s3_bucket,
                title = title,
                description = description,
                date_created = datetime.datetime.utcnow(),
            )
        except IntegrityError:
            abort(
                409,
                message = 'Integrity Error.',
            )
        return image.plain_dict()

class RestImage(Resource):
    @auth.login_required
    def get(self, s3_key):
        try:
            image = Image.get(
                Image.s3_key == s3_key,
                Image.user == g.user,
            )
        except Image.DoesNotExist:
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
        return image.plain_dict()

    @auth.login_required
    def put(self, s3_key):
        if request.is_json:
            title = request.get_json().get('title', '')
            description = request.get_json().get('description', '')
        else:
            abort(
                400,
                message = 'Request must be of type application/json.'
            )
        try:
            image = Image.get(
                Image.s3_key == s3_key,
                Image.user == g.user,
            )
        except Image.DoesNotExist:
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
        image.description = description
        image.title = title
        image.save()
        return image.plain_dict()

    @auth.login_required
    def delete(self, s3_key):
        try:
            image = Image.get(
                Image.s3_key == s3_key,
                Image.user == g.user,
            )
        except Image.DoesNotExist:
            abort(
                404,
                message = 'Image with s3_key {0} does not exist.'.format(s3_key)
            )
        image.delete_instance(recursive=True)
        return image.plain_dict()

api.add_resource(RestUserList, '/api/users')
api.add_resource(RestUser, '/api/users/<username>')
api.add_resource(RestApiKeyList, '/api/api-keys')
api.add_resource(RestApiKey, '/api/api-keys/<api_key_str>')
api.add_resource(RestCollectionList, '/api/collections')
api.add_resource(RestCollection, '/api/collections/<name>')
api.add_resource(RestImageList, '/api/images')
api.add_resource(RestImage, '/api/images/<path:s3_key>')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
