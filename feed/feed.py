from flask import Flask
from flask import g
from flask import request
from flask import jsonify
from flask import send_from_directory
from flask import render_template
from flask import redirect
from flask import url_for

import sqlite3

DATABASE = '/app/database.sqlite'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def inittables():
    db = sqlite3.connect(DATABASE)
    c = db.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (
                                        id INTEGER PRIMARY KEY,
                                        name TEXT UNIQUE
                                        )''')
    c.execute('''CREATE TABLE IF NOT EXISTS profile_users (
                                        id INTEGER PRIMARY KEY,
                                        userID INT,
                                        profileID INT,
                                        UNIQUE(userID, profileID)
                                        )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                                    id INTEGER PRIMARY KEY,
                                    username TEXT UNIQUE,
                                    lastpoll INTEGER
                                    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS medias (
                                    shortcode TEXT PRIMARY KEY,
                                    username TEXT,
                                    thumbnailURL TEXT,
                                    imageURL TEXT,
                                    caption TEXT,
                                    timestamp INTEGER
                                )''')
    db.commit()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

inittables()
app = Flask(__name__)


@app.route('/')
def index():
    profile = get_db().cursor().execute('''select name from profiles limit 1''').fetchone()[0]
    return redirect(url_for('profile', profile=profile))


@app.route('/<profile>')
def profile(profile=None):
    return render_template('profile.html', profile=profile)


@app.route('/css/<path:filename>')
def css(filename):
    return send_from_directory('css', filename)


@app.route('/js/<path:filename>')
def js(filename):
    return send_from_directory('js', filename)


@app.route('/feed')
def feed():
    start = request.args.get('start', default=0, type=int)
    count = request.args.get('count', default=5, type=int)
    get_db().row_factory = dict_factory
    cursor = get_db().cursor()
    cursor.execute(
        '''SELECT shortcode, medias.username as source, thumbnailURL as thumb, imageURL as url, caption as caption, timestamp
        FROM medias 
        LEFT JOIN users on users.username=medias.username
        LEFT JOIN profile_users on profile_users.userid=users.id
        WHERE profile_users.profileID=1
        ORDER BY timestamp 
        DESC LIMIT ? 
        OFFSET ?''', (count, start))
    rows = cursor.fetchall()
    return jsonify(rows)


if __name__ == '__main__':
    app.run(debug=True)