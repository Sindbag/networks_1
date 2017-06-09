from __future__ import absolute_import

import hashlib
import json
import logging
import sqlite3
import subprocess
from uuid import uuid4

import scrypt


import settings
from flask import Flask, session, redirect, render_template, request, flash, url_for, g
from flask_session import Session
from flask_sockets import Sockets
from wtforms import Form, StringField, PasswordField, validators

from models import User

app = Flask(__name__, static_folder='static', static_url_path='/st')
app.config.from_object(settings)
Session(app)
# sockets = Sockets(app)


# SQLite3-related functions ################################################

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(settings.DATABASE)
    return db


def get_users_db():
    db = getattr(g, '_userbase', None)
    if db is None:
        db = g._userbase = sqlite3.connect(settings.USERBASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    with app.app_context():
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv


def make_new_user(user):
    with app.app_context():
        db = get_users_db()

        # pbdkf2
        # salted = scrypt.hash(user.password, settings.SALT)

        # sha256
        salted = (user.password + settings.SALT)
        for _ in range(512):
            salted = hashlib.sha256(salted.encode()).hexdigest()

        # lets insert something each time
        db.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                   (str(uuid4()), salted, user.email))
        db.commit()
        return user.username


def authenticate(username, password):
    with app.app_context():
        row = get_users_db().execute("select username, password from users where username=?", (username,)).fetchone()
        # pbdkf2
        # if row and scrypt.hash(password, settings.SALT) == row[1]:
        #     return True

        # sha256
        salted = (password + settings.SALT)
        for _ in range(512):
            salted = hashlib.sha256(salted.encode()).hexdigest()
        if row and salted == row[1]:
            return True
        # For test purposes
        return True
    return False


# Views ####################################################################

def easy_task():
    with app.app_context():
        res = get_db().execute('select * from some where hello=?', ('abc',)).fetchall()
        return res


def factor(n):
    Ans = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            Ans.append(d)
            n //= d
        else:
            d += 1
    if n > 1:
        Ans.append(n)
    return Ans


def calc_task():
    return factor(2971215073)


# @sockets.route('/hard')
# def hard_task(ws):
#     while not ws.closed:
#         message = ws.receive()
#         if message:
#             try:
#                 data = json.loads(message)
#                 c = min(10000, max(1, int(data.get('c', 10))))
#                 t = min(128, max(1, int(data.get('t', 64))))
#                 i = min(120, max(1, int(data.get('i', 5))))
#                 addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
#                 addr = addr.split(':')[-1]
#                 with subprocess.Popen(["ping",
#                                        "-c", str(c),
#                                        "-t", str(t),
#                                        "-i", str(i),
#                                        addr],
#                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
#                     for line in proc.stdout:
#                         ws.send(line.decode())
#                     for line in proc.stderr:
#                         ws.send(line.decode())
#             except Exception as e:
#                 logging.exception('wow %s', e)
#                 ws.send(e)
#             ws.send('close')


def harder_task():
    c, t, i = 20, 64, 2
    addr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    addr = addr.split(':')[-1]
    out = b''
    with subprocess.Popen(["ping",
                           "-c", str(c),
                           "-t", str(t),
                           "-i", str(i),
                           addr],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        for line in proc.stdout:
            out += line
    return out


commands = {
    'easy': easy_task,
    'calc': calc_task,
    'hard': harder_task
}


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        task = request.args.get('task', None)
        res = 'Not found task'
        t = ''
        if task in ['easy', 'calc', 'hard']:
            t = commands[task]()
            res = '%s was done' % task
        return render_template('home.html', user='anonym', task=res, t=t)

    user = session.get('user')
    if user:
        task = request.args.get('task', None)
        res = 'Not found task'
        t = ''
        if task in ['easy', 'calc', 'hard']:
            t = commands[task]()
            res = '%s was done' % task
        return render_template('home.html', user=user, task=res, t=t)
    return redirect(url_for('login'))


class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=60), validators.InputRequired()])
    password = PasswordField('Password', [
        validators.InputRequired(), validators.Length(min=8, max=32)
    ])


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    error = ''
    if request.method == 'POST' and form.validate():
        if authenticate(form.username.data, form.password.data):
            user = form.username.data
            session['user'] = user
            return redirect(url_for('home'))
        else:
            error = 'Username or password invalid'
    return render_template('login.html', form=form, error=error)


class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=60), validators.InputRequired()])
    email = StringField('Email Address', [validators.Length(min=6, max=250)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.Length(min=8, max=32),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    error = ''

    if request.method == 'POST' and form.validate():
        user = User(form.username.data, form.email.data, form.password.data)
        try:
            username = make_new_user(user)
            session['user'] = username
            flash('Thanks for registering')
            return redirect(url_for('home'))
        except Exception as e:
            flash('Error while registration')
            error = 'Error while registration. %s' % e

    return render_template('registration.html', form=form, error=error)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
