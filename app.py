import os
import base64
import datetime
from functools import wraps
import tempfile
import hashlib

from flask import Flask, render_template, request, flash, g, session, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from PIL import Image as PImage

from database import database, User, Collection, Image, ImageCollection, IntegrityError

database.connect()
database.create_tables([User, Collection, Image, ImageCollection], safe=True)
database.close()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

app.config['APP_URL'] = os.environ.get('APP_URL')

app.config['S3_BUCKET'] = os.environ.get('S3_BUCKET')

app.config['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')

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

def get_current_user():
    return User.get(User.username == session['username'])

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id = app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key = app.config['AWS_SECRET_ACCESS_KEY']
        )

def gen_thumb_key(key, size):
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

def create_thumbnails(image):
    for size in [128, 256, 512]:
        s3 = get_s3_client()
        s3_object = s3.get_object(
            Bucket = image.s3_bucket,
            Key = image.s3_key
        )
        pil_object = PImage.open(s3_object['Body'])
        pil_object.thumbnail((size, size))
        thumb_file = tempfile.SpooledTemporaryFile()
        pil_object.save(thumb_file, format='JPEG')
        thumb_file.seek(0)
        thumb_md5 = base64.b64encode(hashlib.md5(thumb_file.read()).digest()).decode()
        thumb_file.seek(0)
        thumb_s3_key = gen_thumb_key(image.s3_key, size)
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
                (Image.id == k) &
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
                flash('Image {0} deleted'.format(image.s3_key))
            return redirect(url_for('images'))
    else:
        images = Image.select().where(Image.user == user)
        collections = Collection.select().where(Collection.user == user)
        return render_template('images.html', images=images, collections=collections)

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
            'success_action_redirect': '{0}/upload'.format(app.config['APP_URL'])
            },
        Conditions = [
            {'acl': 'public-read'},
            ['starts-with', '$key', key_prefix],
            ['starts-with', '$success_action_redirect', app.config['APP_URL']],
            ['starts-with', '$Content-Type', 'image/'],
            ],
        ExpiresIn = 600
        )
    return render_template('upload.html', post=post, args=args)

def gen_image_dict(image):
    return {
        'title': image.title,
        'description': image.description,
        's3_key': image.s3_key,
        'url': 'https://s3.amazonaws.com/{0}/{1}'.format(image.s3_bucket, image.s3_key),
        'thumbs': {
            size: 'https://s3.amazonaws.com/{0}/{1}'.format(image.s3_bucket, gen_thumb_key(image.s3_key, size))
            for size in (128, 256, 512)
        }
    }

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

if __name__ == '__main__':
    app.run(host='0.0.0.0')
