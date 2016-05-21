import os
import base64
import datetime
from functools import wraps

from flask import Flask, render_template, request, flash, g, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import boto3

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

@app.route('/images')
@login_required
def images():
    user = User.get(User.username == session['username'])
    images = Image.select().where(Image.user == user)
    return render_template('images.html', images=images)

@app.route('/upload')
@login_required
def upload():
    args = request.args.to_dict()
    if args:
        try:
            image = Image.create(
                s3_key = args['key'],
                s3_bucket = args['bucket'],
                user = User.get(User.username == session['username']),
                date_created = datetime.datetime.utcnow()
            )
            flash('Image added.')
        except IntegrityError:
            flash('Image already exists.')
    key_prefix = base64.urlsafe_b64encode(os.urandom(6)).decode()
    s3 = boto3.client(
        's3',
        aws_access_key_id = app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key = app.config['AWS_SECRET_ACCESS_KEY']
        )
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

if __name__ == '__main__':
    app.run(host='0.0.0.0')
